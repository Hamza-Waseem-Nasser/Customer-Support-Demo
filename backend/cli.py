#!/usr/bin/env python3
"""
Customer Support CLI Chat Interface
A command-line interface for the Swiss Airlines Customer Support Bot.
Run this script to interact with the AI agent via terminal.
"""
import os
import sys
import asyncio
import logging

# Set environment variables for verbose logging
os.environ["VERBOSE_LOGGING"] = "true"
os.environ["LOG_LEVEL"] = "DEBUG"

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Filter out the LangChain serialization warning that doesn't affect functionality
class LangChainSerializationFilter(logging.Filter):
    def filter(self, record):
        # Suppress the 'Failed to serialize object' debug messages from langchain_core.load.serializable
        if (record.name == 'langchain_core.load.serializable' and 
            record.levelname == 'DEBUG' and 
            'Failed to serialize object' in record.getMessage()):
            return False
        return True

# Apply the filter to suppress serialization warnings
logging.getLogger('langchain_core.load.serializable').addFilter(LangChainSerializationFilter())

from app.config import settings
from app.agent import get_agent
from app.data_setup import setup_sample_database

class SimpleCliChat:
    def __init__(self):
        self.agent = None
        self.session_id = f"cli-session-{os.getpid()}"
        self.passenger_id = "3442 587242"
        
    async def initialize(self):
        print("🚀 Initializing Customer Support Agent...")
        print("📝 Verbose logging enabled")
        print("-" * 60)
        
        try:
            # Check if database already exists
            if os.path.exists("travel2.sqlite"):
                print("✅ Database: travel2.sqlite (existing)")
                db_file = "travel2.sqlite"
            else:
                # Setup database
                print("⏳ Setting up database...")
                db_file = setup_sample_database()
                print(f"✅ Database: {db_file}")
            
            # Get agent
            self.agent = get_agent()
            print("✅ Agent ready")
            print("-" * 60)
            return True
            
        except Exception as e:
            print(f"❌ Error: {e}")
            # Try to continue without database setup if agent can be created
            try:
                print("⚠️ Trying to continue with existing database...")
                self.agent = get_agent()
                print("✅ Agent ready (using existing setup)")
                print("-" * 60)
                return True
            except Exception as e2:
                print(f"❌ Final error: {e2}")
                return False
    
    async def chat_loop(self):
        print("\n💬 Swiss Airlines Customer Support CLI")
        print("Type 'quit' to exit")
        print("=" * 60)
        
        while True:
            try:
                user_input = input("\n👤 You: ").strip()
                
                if not user_input:
                    continue
                    
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                print(f"\n🔄 Processing: '{user_input}'")
                print("🔍 Agent thinking...")
                print("-" * 40)
                
                response = await self.process_message(user_input)
                
                print("-" * 40)
                print(f"🤖 Agent: {response}")
                print("=" * 60)
                
            except KeyboardInterrupt:
                print("\n👋 Interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

    async def process_message(self, message: str) -> str:
        try:
            config = {
                "configurable": {
                    "passenger_id": self.passenger_id,
                    "session_id": self.session_id,
                    "thread_id": self.session_id  # Add thread_id for LangGraph
                }
            }
            
            if settings.verbose_logging:
                print(f"🎫 Passenger ID: {self.passenger_id}")
                print(f"🆔 Session ID: {self.session_id}")
            
            state = {
                "messages": [("user", message)],
                "user_info": f"Passenger ID: {self.passenger_id}"
            }
            
            result = await self.agent.ainvoke(state, config)
            
            if result and "messages" in result:
                last_message = result["messages"][-1]
                if hasattr(last_message, 'content'):
                    return last_message.content
                else:
                    return str(last_message)
            
            return "Sorry, I couldn't process that."
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error processing message: {e}")
            return f"Error: {e}"

async def main():
    cli = SimpleCliChat()
    if await cli.initialize():
        await cli.chat_loop()
    else:
        print("❌ Failed to initialize.")

if __name__ == "__main__":
    asyncio.run(main())
