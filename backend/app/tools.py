"""
Customer support tools extracted from the notebook
"""
import re
import sqlite3
import logging
from datetime import date, datetime
from typing import Optional, Union, List
import numpy as np
import pytz
import requests
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from .config import settings
from .data_setup import get_company_policies

# Configure logging
logger = logging.getLogger(__name__)

# Global database file path
DB_FILE = "travel2.sqlite"

# Policy retrieval setup
def setup_policy_retriever():
    """Set up the policy retriever with company FAQs"""
    try:
        import openai
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        
        faq_text = get_company_policies()
        docs = [{"page_content": txt} for txt in re.split(r"(?=\n##)", faq_text)]
        
        class VectorStoreRetriever:
            def __init__(self, docs: list, vectors: list, client):
                self._arr = np.array(vectors)
                self._docs = docs
                self._client = client
                
            @classmethod
            def from_docs(cls, docs, client):
                # Use Gemini for embeddings since you have that API key
                embeddings_model = GoogleGenerativeAIEmbeddings(
                    model="models/text-embedding-004",
                    google_api_key=settings.gemini_api_key
                )                
                vectors = []
                for doc in docs:
                    embedding = embeddings_model.embed_query(doc["page_content"])
                    vectors.append(embedding)
                
                return cls(docs, vectors, client)

            def query(self, query: str, k: int = 5) -> list[dict]:
                embeddings_model = GoogleGenerativeAIEmbeddings(
                    model="models/text-embedding-004",
                    google_api_key=settings.gemini_api_key
                )
                query_embedding = embeddings_model.embed_query(query)
                
                scores = np.array(query_embedding) @ self._arr.T
                top_k_idx = np.argpartition(scores, -k)[-k:]
                top_k_idx_sorted = top_k_idx[np.argsort(-scores[top_k_idx])]
                return [
                    {**self._docs[idx], "similarity": scores[idx]} for idx in top_k_idx_sorted
                ]

        retriever = VectorStoreRetriever.from_docs(docs, None)
        return retriever
    except Exception as e:
        print(f"Warning: Could not set up policy retriever: {e}")
        return None

# Initialize retriever
try:
    policy_retriever = setup_policy_retriever()
except:
    policy_retriever = None

@tool
def lookup_policy(query: str) -> str:
    """Consult the company policies to check whether certain options are permitted."""
    if policy_retriever is None:
        return "Policy information temporarily unavailable. Please contact support for policy questions."
    
    try:
        docs = policy_retriever.query(query, k=2)
        return "\n\n".join([doc["page_content"] for doc in docs])
    except Exception as e:
        return f"Error retrieving policy information: {str(e)}"

@tool
def fetch_user_flight_information(config: RunnableConfig) -> list[dict]:
    """Fetch all tickets for the user along with corresponding flight information and seat assignments."""
    if settings.verbose_logging:
        logger.info("🎫 TOOL CALLED: fetch_user_flight_information")
    
    configuration = config.get("configurable", {})
    passenger_id = configuration.get("passenger_id", None)
    
    if settings.verbose_logging:
        logger.info(f"👤 Passenger ID: {passenger_id}")
    
    if not passenger_id:
        if settings.verbose_logging:
            logger.warning("⚠️ No passenger ID configured")
        return [{"error": "No passenger ID configured"}]

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    query = """
    SELECT 
        t.ticket_no, t.book_ref,
        f.flight_id, f.flight_no, f.departure_airport, f.arrival_airport, 
        f.scheduled_departure, f.scheduled_arrival,
        bp.seat_no, tf.fare_conditions
    FROM 
        tickets t
        JOIN ticket_flights tf ON t.ticket_no = tf.ticket_no
        JOIN flights f ON tf.flight_id = f.flight_id
        JOIN boarding_passes bp ON bp.ticket_no = t.ticket_no AND bp.flight_id = f.flight_id
    WHERE 
        t.passenger_id = ?
    """
    cursor.execute(query, (passenger_id,))
    rows = cursor.fetchall()
    column_names = [column[0] for column in cursor.description]
    results = [dict(zip(column_names, row)) for row in rows]

    cursor.close()
    conn.close()

    return results

@tool
def search_flights(
    departure_airport: Optional[str] = None,
    arrival_airport: Optional[str] = None,
    start_time: Optional[Union[date, datetime]] = None,
    end_time: Optional[Union[date, datetime]] = None,
    limit: int = 20,
) -> list[dict]:
    """Search for flights based on departure airport, arrival airport, and departure time range."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    query = "SELECT * FROM flights WHERE 1 = 1"
    params = []

    if departure_airport:
        query += " AND departure_airport = ?"
        params.append(departure_airport)

    if arrival_airport:
        query += " AND arrival_airport = ?"
        params.append(arrival_airport)

    if start_time:
        query += " AND scheduled_departure >= ?"
        params.append(start_time)

    if end_time:
        query += " AND scheduled_departure <= ?"
        params.append(end_time)
    
    query += " LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    column_names = [column[0] for column in cursor.description]
    results = [dict(zip(column_names, row)) for row in rows]

    cursor.close()
    conn.close()

    return results

@tool
def update_ticket_to_new_flight(
    ticket_no: str, new_flight_id: int, *, config: RunnableConfig
) -> str:
    """Update the user's ticket to a new valid flight."""
    configuration = config.get("configurable", {})
    passenger_id = configuration.get("passenger_id", None)
    if not passenger_id:
        return "No passenger ID configured."

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Check if new flight exists
    cursor.execute(
        "SELECT departure_airport, arrival_airport, scheduled_departure FROM flights WHERE flight_id = ?",
        (new_flight_id,),
    )
    new_flight = cursor.fetchone()
    if not new_flight:
        cursor.close()
        conn.close()
        return "Invalid new flight ID provided."
    
    column_names = [column[0] for column in cursor.description]
    new_flight_dict = dict(zip(column_names, new_flight))
    
    # Check timing constraints
    timezone = pytz.timezone("Etc/GMT-3")
    current_time = datetime.now(tz=timezone)
    departure_time = datetime.strptime(
        new_flight_dict["scheduled_departure"], "%Y-%m-%d %H:%M:%S.%f%z"
    )
    time_until = (departure_time - current_time).total_seconds()
    if time_until < (3 * 3600):
        return f"Not permitted to reschedule to a flight that is less than 3 hours from the current time. Selected flight is at {departure_time}."

    # Check if ticket exists and belongs to user
    cursor.execute(
        "SELECT * FROM tickets WHERE ticket_no = ? AND passenger_id = ?",
        (ticket_no, passenger_id),
    )
    current_ticket = cursor.fetchone()
    if not current_ticket:
        cursor.close()
        conn.close()
        return f"Current signed-in passenger with ID {passenger_id} not the owner of ticket {ticket_no}"

    # Update the ticket
    cursor.execute(
        "UPDATE ticket_flights SET flight_id = ? WHERE ticket_no = ?",
        (new_flight_id, ticket_no),
    )
    conn.commit()

    cursor.close()
    conn.close()
    return "Ticket successfully updated to new flight."

@tool
def cancel_ticket(ticket_no: str, *, config: RunnableConfig) -> str:
    """Cancel the user's ticket and remove it from the database."""
    configuration = config.get("configurable", {})
    passenger_id = configuration.get("passenger_id", None)
    if not passenger_id:
        return "No passenger ID configured."
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Check if user owns the ticket
    cursor.execute(
        "SELECT ticket_no FROM tickets WHERE ticket_no = ? AND passenger_id = ?",
        (ticket_no, passenger_id),
    )
    current_ticket = cursor.fetchone()
    if not current_ticket:
        cursor.close()
        conn.close()
        return f"Current signed-in passenger with ID {passenger_id} not the owner of ticket {ticket_no}"

    cursor.execute("DELETE FROM ticket_flights WHERE ticket_no = ?", (ticket_no,))
    conn.commit()

    cursor.close()
    conn.close()
    return "Ticket successfully cancelled."

# Car Rental Tools
@tool
def search_car_rentals(
    location: Optional[str] = None,
    name: Optional[str] = None,
    price_tier: Optional[str] = None,
    start_date: Optional[Union[datetime, date]] = None,
    end_date: Optional[Union[datetime, date]] = None,
) -> list[dict]:
    """Search for car rentals based on location, name, price tier, start date, and end date."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    query = "SELECT * FROM car_rentals WHERE 1=1"
    params = []

    if location:
        query += " AND location LIKE ?"
        params.append(f"%{location}%")
    if name:
        query += " AND name LIKE ?"
        params.append(f"%{name}%")
    
    cursor.execute(query, params)
    results = cursor.fetchall()
    column_names = [column[0] for column in cursor.description]
    
    conn.close()

    return [dict(zip(column_names, row)) for row in results]

@tool
def book_car_rental(rental_id: int) -> str:
    """Book a car rental by its ID."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("UPDATE car_rentals SET booked = 1 WHERE id = ?", (rental_id,))
    conn.commit()

    if cursor.rowcount > 0:
        conn.close()
        return f"Car rental {rental_id} successfully booked."
    else:
        conn.close()
        return f"No car rental found with ID {rental_id}."

# Hotel Tools
@tool
def search_hotels(
    location: Optional[str] = None,
    name: Optional[str] = None,
    price_tier: Optional[str] = None,
    checkin_date: Optional[Union[datetime, date]] = None,
    checkout_date: Optional[Union[datetime, date]] = None,
) -> list[dict]:
    """Search for hotels based on location, name, price tier, check-in date, and check-out date."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    query = "SELECT * FROM hotels WHERE 1=1"
    params = []

    if location:
        query += " AND location LIKE ?"
        params.append(f"%{location}%")
    if name:
        query += " AND name LIKE ?"
        params.append(f"%{name}%")
    
    cursor.execute(query, params)
    results = cursor.fetchall()
    column_names = [column[0] for column in cursor.description]

    conn.close()

    return [dict(zip(column_names, row)) for row in results]

@tool
def book_hotel(hotel_id: int) -> str:
    """Book a hotel by its ID."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("UPDATE hotels SET booked = 1 WHERE id = ?", (hotel_id,))
    conn.commit()

    if cursor.rowcount > 0:
        conn.close()
        return f"Hotel {hotel_id} successfully booked."
    else:
        conn.close()
        return f"No hotel found with ID {hotel_id}."

# Excursion Tools
@tool
def search_trip_recommendations(
    location: Optional[str] = None,
    name: Optional[str] = None,
    keywords: Optional[str] = None,
) -> list[dict]:
    """Search for trip recommendations based on location, name, and keywords."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    query = "SELECT * FROM trip_recommendations WHERE 1=1"
    params = []

    if location:
        query += " AND location LIKE ?"
        params.append(f"%{location}%")
    if name:
        query += " AND name LIKE ?"
        params.append(f"%{name}%")
    if keywords:
        keyword_list = keywords.split(",")
        keyword_conditions = " OR ".join(["keywords LIKE ?" for _ in keyword_list])
        query += f" AND ({keyword_conditions})"
        params.extend([f"%{keyword.strip()}%" for keyword in keyword_list])

    cursor.execute(query, params)
    results = cursor.fetchall()
    column_names = [column[0] for column in cursor.description]

    conn.close()

    return [dict(zip(column_names, row)) for row in results]

@tool
def book_excursion(recommendation_id: int) -> str:
    """Book an excursion by its recommendation ID."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE trip_recommendations SET booked = 1 WHERE id = ?", (recommendation_id,)
    )
    conn.commit()

    if cursor.rowcount > 0:
        conn.close()
        return f"Trip recommendation {recommendation_id} successfully booked."
    else:
        conn.close()
        return f"No trip recommendation found with ID {recommendation_id}."

# Web Search Tool
@tool
def tavily_search(query: str) -> str:
    """Search the web for current information using Tavily."""
    try:
        from tavily import TavilyClient
        
        if not settings.tavily_api_key:
            return "Web search temporarily unavailable - API key not configured."
        
        tavily = TavilyClient(api_key=settings.tavily_api_key)
        response = tavily.search(query=query, search_depth="basic", max_results=3)
        
        if response and "results" in response:
            results = []
            for result in response["results"][:3]:
                results.append(f"Title: {result.get('title', 'N/A')}\nContent: {result.get('content', 'N/A')}\nURL: {result.get('url', 'N/A')}")
            return "\n\n".join(results)
        else:
            return "No search results found."
            
    except Exception as e:
        return f"Search error: {str(e)}"

# Collect all tools
ALL_TOOLS = [
    lookup_policy,
    fetch_user_flight_information,
    search_flights,
    update_ticket_to_new_flight,
    cancel_ticket,
    search_car_rentals,
    book_car_rental,
    search_hotels,
    book_hotel,
    search_trip_recommendations,
    book_excursion,
    tavily_search,
]

# Categorize tools
SAFE_TOOLS = [
    lookup_policy,
    fetch_user_flight_information,
    search_flights,
    search_car_rentals,
    search_hotels,
    search_trip_recommendations,
    tavily_search,
]

SENSITIVE_TOOLS = [
    update_ticket_to_new_flight,
    cancel_ticket,
    book_car_rental,
    book_hotel,
    book_excursion,
]
