"""
Customer Support Agent using LangGraph
"""
from typing import Annotated, Optional
from typing_extensions import TypedDict
from datetime import datetime
import uuid
import logging

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableLambda

from langgraph.graph.message import AnyMessage, add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import tools_condition, ToolNode

from .tools import ALL_TOOLS, SAFE_TOOLS, SENSITIVE_TOOLS, fetch_user_flight_information
from .config import settings

# Configure logging
logger = logging.getLogger(__name__)
if settings.verbose_logging:
    logging.getLogger("langgraph").setLevel(logging.DEBUG)
    logging.getLogger("langchain").setLevel(logging.DEBUG)

# Try to import available LLM providers
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    GEMINI_AVAILABLE = bool(settings.gemini_api_key)
except ImportError:
    GEMINI_AVAILABLE = False

try:
    from langchain_anthropic import ChatAnthropic
    ANTHROPIC_AVAILABLE = bool(settings.anthropic_api_key)
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    from langchain_openai import ChatOpenAI
    OPENAI_AVAILABLE = bool(settings.openai_api_key)
except ImportError:
    OPENAI_AVAILABLE = False


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    user_info: Optional[str]


class Assistant:
    def __init__(self, runnable: Runnable):
        self.runnable = runnable
    
    def __call__(self, state: State, config: RunnableConfig):
        if settings.verbose_logging:
            logger.info(f"🤖 Assistant called with {len(state.get('messages', []))} messages")
            if state.get('messages'):
                last_msg = state['messages'][-1]
                logger.info(f"📝 Last message: {type(last_msg).__name__} - {getattr(last_msg, 'content', '')[:100]}...")
        
        while True:
            result = self.runnable.invoke(state)
            
            if settings.verbose_logging:
                logger.info(f"🔍 LLM Response: {result.content[:200] if result.content else 'No content'}...")
                if hasattr(result, 'tool_calls') and result.tool_calls:
                    logger.info(f"🔧 Tool calls requested: {[call.get('name', 'unknown') for call in result.tool_calls]}")
            
            # If the LLM happens to return an empty response, we will re-prompt it
            if not result.tool_calls and (
                not result.content
                or isinstance(result.content, list)
                and not result.content[0].get("text")
            ):
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
                if settings.verbose_logging:
                    logger.warning("⚠️ Empty response, re-prompting...")
            else:
                break
        return {"messages": result}


def handle_tool_error(state) -> dict:
    error = state.get("error")
    tool_calls = state["messages"][-1].tool_calls
    return {
        "messages": [
            ToolMessage(
                content=f"Error: {repr(error)}\n please fix your mistakes.",
                tool_call_id=tc["id"],
            )
            for tc in tool_calls
        ]
    }


def create_tool_node_with_fallback(tools: list) -> ToolNode:
    return ToolNode(tools).with_fallbacks(
        [RunnableLambda(handle_tool_error)], exception_key="error"
    )


def get_llm():
    """Get the best available LLM based on API keys"""
    if GEMINI_AVAILABLE:
        return ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=settings.gemini_api_key,
            temperature=0.1
        )
    elif ANTHROPIC_AVAILABLE:
        return ChatAnthropic(
            model="claude-3-sonnet-20240229",
            temperature=0.1
        )
    elif OPENAI_AVAILABLE:
        return ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0.1
        )
    else:
        raise ValueError("No LLM API key configured. Please set GEMINI_API_KEY, ANTHROPIC_API_KEY, or OPENAI_API_KEY")


def create_customer_support_agent():
    """Create the customer support agent graph"""
    
    # Initialize LLM
    llm = get_llm()
    
    # Create prompt template
    assistant_prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "You are a helpful customer support assistant for Swiss Airlines. "
            "Use the provided tools to search for flights, company policies, and other information to assist the user's queries. "
            "When searching, be persistent. Expand your query bounds if the first search returns no results. "
            "If a search comes up empty, expand your search before giving up. "
            "Always be polite, professional, and helpful. "
            "Current user info: {user_info} "
            "Current time: {time}.",
        ),
        ("placeholder", "{messages}"),
    ]).partial(time=datetime.now)
    
    # Create assistant runnable
    assistant_runnable = assistant_prompt | llm.bind_tools(ALL_TOOLS)
    
    # Define state graph
    builder = StateGraph(State)
    
    def user_info(state: State):
        """Fetch user info at the start"""
        try:
            config = RunnableConfig(configurable={"passenger_id": "3442 587242"})  # Default for demo
            user_flights = fetch_user_flight_information.invoke({}, config)
            return {"user_info": f"User has {len(user_flights)} flight bookings"}
        except Exception as e:
            return {"user_info": f"Could not fetch user info: {str(e)}"}
    
    # Add nodes
    builder.add_node("fetch_user_info", user_info)
    builder.add_node("assistant", Assistant(assistant_runnable))
    builder.add_node("safe_tools", create_tool_node_with_fallback(SAFE_TOOLS))
    builder.add_node("sensitive_tools", create_tool_node_with_fallback(SENSITIVE_TOOLS))
    
    # Add edges
    builder.add_edge(START, "fetch_user_info")
    builder.add_edge("fetch_user_info", "assistant")
    
    def route_tools(state: State):
        """Route to appropriate tool node based on tool type"""
        next_node = tools_condition(state)
        if next_node == END:
            return END
        
        ai_message = state["messages"][-1]
        if not ai_message.tool_calls:
            return END
            
        # Check if any tool call is sensitive
        sensitive_tool_names = {t.name for t in SENSITIVE_TOOLS}
        for tool_call in ai_message.tool_calls:
            if tool_call["name"] in sensitive_tool_names:
                return "sensitive_tools"
        
        return "safe_tools"
    
    builder.add_conditional_edges(
        "assistant", 
        route_tools, 
        ["safe_tools", "sensitive_tools", END]
    )
    builder.add_edge("safe_tools", "assistant")
    builder.add_edge("sensitive_tools", "assistant")
    
    # Create checkpointer
    memory = MemorySaver()
    
    # Compile graph with interrupt before sensitive tools
    graph = builder.compile(
        checkpointer=memory,
        interrupt_before=["sensitive_tools"]
    )
    
    return graph


# Global agent instance
customer_support_agent = None

def get_agent():
    """Get or create the customer support agent"""
    global customer_support_agent
    if customer_support_agent is None:
        customer_support_agent = create_customer_support_agent()
    return customer_support_agent
