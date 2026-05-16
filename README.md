# SHL Assessment Recommender Agent 🚀

A full-stack, RAG-powered Conversational AI application. This project bridges the gap between vague hiring requirements (e.g., "I need a mid-level Java developer test") and concrete SHL assessment recommendations using advanced natural language processing.

## 🌐 Live Demos
* **Live Chat UI (Frontend):** [Insert your Streamlit Cloud URL here - if deployed]
* **Live API Endpoint (Backend):** [https://jibank-shl-agent-intern.hf.space](https://jibank-shl-agent-intern.hf.space)
*(Interactive Swagger Documentation is available by appending `/docs` to the backend URL.)*

## ✨ Key Features
* **Interactive Chat UI:** A sleek, conversational frontend built with Streamlit that mimics native AI assistant experiences.
* **Conversational Awareness:** The agent handles natural greetings, time-of-day awareness, and small talk, gently steering users back to SHL assessments.
* **Stateless Architecture:** Fully RESTful design. The `/chat` endpoint requires the full conversation history to maintain context without server-side memory.
* **Retrieval-Augmented Generation (RAG):** Utilizes `ChromaDB` and Hugging Face's `all-MiniLM-L6-v2` to semantically search the SHL catalog and inject relevant test data into the LLM context.
* **Strict JSON Schemas:** Leverages Groq's JSON mode and Pydantic validation to guarantee the LLM response perfectly matches the required frontend schema.
* **Containerized Deployment:** The backend is fully dockerized for seamless deployment to Hugging Face Spaces.

## 🛠️ Tech Stack
* **Frontend:** Streamlit
* **Backend Framework:** FastAPI / Python 3.11
* **LLM Provider:** Groq (`llama-3.3-70b-versatile`)
* **Vector Database:** ChromaDB
* **Embeddings:** Sentence-Transformers (`all-MiniLM-L6-v2`)
* **Deployment:** Docker & Hugging Face Spaces

## 🚀 Local Setup & Installation

**1. Clone the repository**
```bash
git clone [https://github.com/Jiban243/SHL_Agent_Intern.git](https://github.com/jibank/SHL_Agent_Intern.git)
cd SHL_Agent_Intern

2. Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

3. Install dependencies
pip install -r requirements.txt

4. Environment Variables
Create a .env file in the root directory and add your Groq API key:
GROQ_API_KEY=gsk_your_api_key_here

5. Build the Vector Database
Run the ingestion script to parse the a.json catalog and generate local embeddings.
python ingest.py

6. Start the Backend Server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

7. Start the Frontend UI (New Terminal)
Open a second terminal window, activate your environment, and run:
streamlit run app.py

📡 API Endpoints
GET /health
Simple readiness probe.
Response:
{
  "status": "ok"
}

POST /chat
Core conversational endpoint.
Request Payload:
{
  "messages": [
    {"role": "user", "content": "I am looking for a test for a mid-level Python engineer."}
  ]
}

Response:
{
  "reply": "Here are some targeted assessments for a mid-level Python engineer. Would you like to focus more on algorithmic problem-solving or practical framework usage?",
  "recommendations": [
    {
      "name": "Python 3 Core Knowledge",
      "url": "[https://www.shl.com/products/](https://www.shl.com/products/)...",
      "test_type": "Programming, Knowledge"
    }
  ],
  "end_of_conversation": false
}

🏗️ Deployment
The FastAPI backend is containerized using Docker and configured to deploy automatically to Hugging Face Spaces. The Dockerfile handles environment setup, package installation, and executes the vector database build (python ingest.py) dynamically at startup to ensure the RAG pipeline is always up to date. The Streamlit frontend connects dynamically to this hosted API.

