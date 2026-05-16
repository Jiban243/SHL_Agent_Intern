import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
from groq import Groq
from datetime import datetime

# Load environment variables from .env
load_dotenv()

app = FastAPI()

# --- 1. Initialize Clients ---
# Verify the API key exists
if not os.environ.get("GROQ_API_KEY"):
    raise ValueError("GROQ_API_KEY is missing from the .env file.")

groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Initialize ChromaDB exactly as we did in the ingestion script
chroma_client = chromadb.PersistentClient(path="./chroma_db")
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)
collection = chroma_client.get_collection(
    name="shl_assessments", 
    embedding_function=sentence_transformer_ef
)

# --- 2. Schemas ---
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]

class Recommendation(BaseModel):
    name: str
    url: str
    test_type: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    recommendations: List[Recommendation]
    end_of_conversation: bool

# --- 3. Endpoints ---
@app.get("/health")
async def health_check():
    """Readiness check for the automated evaluator."""
    return {"status": "ok"}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Stateless chat endpoint that handles context, retrieval, and LLM generation.
    """
    if not request.messages:
        raise HTTPException(status_code=400, detail="Messages array cannot be empty.")

    # A. Determine Time of Day for dynamic greetings
    now = datetime.now()
    current_time = now.strftime("%I:%M %p")
    if now.hour < 12:
        time_of_day = "morning"
    elif now.hour < 17:
        time_of_day = "afternoon"
    else:
        time_of_day = "evening"

    # B. Create a search query based on the entire conversation history
    full_conversation_text = " ".join([m.content for m in request.messages])
    
    # C. Retrieve grounded context from the local ChromaDB
    db_results = collection.query(
        query_texts=[full_conversation_text],
        n_results=15 # Grab top 15 to give the LLM plenty of options to filter
    )
    
    # Format the retrieved data into a readable string for the LLM prompt
    catalog_context = ""
    if db_results['documents'] and len(db_results['documents'][0]) > 0:
        for idx in range(len(db_results['documents'][0])):
            doc = db_results['documents'][0][idx]
            meta = db_results['metadatas'][0][idx]
            catalog_context += f"Name: {meta.get('name')}\nURL: {meta.get('url')}\n{doc}\n\n"
    else:
        catalog_context += "No relevant assessments found in the database.\n"

    # D. Build the Smarter, Conversational System Prompt
    system_prompt = f"""You are a Conversational SHL Assessment Recommender.
You are polite, helpful, and natural, similar to an AI assistant like ChatGPT or Gemini. 
The current time is {current_time} ({time_of_day}).

CRITICAL RULES (Always base your action on the user's LATEST message):
1. GREETINGS: If the user's latest message is "Hi", "Hello", etc., respond warmly with "Good {time_of_day}!" and ask how you can help. "recommendations" MUST be [].
2. GRATITUDE/FAREWELLS: If the user's latest message is "Thanks", "Looks good", or implies they are finished, acknowledge them politely (e.g., "You're very welcome!"). You MUST set "end_of_conversation" to true, and "recommendations" MUST be an empty array []. Do NOT recommend tests again.
3. CLARIFY: If the latest message asks for a test but is too vague, ask follow-up questions. "recommendations" MUST be [].
4. RECOMMEND/REFINE: ONLY if the user's latest message is actively asking for tests or refining a search, populate the "recommendations" array strictly from the catalog context below.

--- AVAILABLE SHL ASSESSMENTS ---
{catalog_context}

RESPONSE FORMAT:
You MUST respond with a valid JSON object matching this exact schema:
{{
  "reply": "Your conversational response to the user.",
  "recommendations": [
    {{"name": "Assessment Name", "url": "Exact URL from context", "test_type": "Optional type if known, else null"}}
  ],
  "end_of_conversation": false
}}

STRICT JSON RULES:
- If you are greeting, saying you're welcome, small-talking, or clarifying, "recommendations" MUST be [].
- "end_of_conversation" MUST be `true` when the user says thanks or goodbye.
"""

    # E. Format messages for Groq API
    groq_messages = [{"role": "system", "content": system_prompt}]
    for msg in request.messages:
        groq_messages.append({"role": msg.role, "content": msg.content})

    # F. Call the Groq LLM
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=groq_messages,
            response_format={"type": "json_object"},
            temperature=0.0 # Force deterministic output
        )
        
        response_data = json.loads(completion.choices[0].message.content)
        return ChatResponse(**response_data)
        
    except Exception as e:
        print(f"Error during LLM generation: {e}")
        return ChatResponse(
            reply="I encountered an internal error. Could you please rephrase your request?",
            recommendations=[],
            end_of_conversation=False
        )