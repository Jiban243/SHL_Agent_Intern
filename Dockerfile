# Use an official Python runtime
FROM python:3.11-slim

# Set the working directory
WORKDIR /code

# Copy requirements
COPY ./requirements.txt /code/requirements.txt

# Force-install all required libraries
RUN pip install --no-cache-dir --upgrade fastapi uvicorn chromadb sentence-transformers groq pydantic python-dotenv -r /code/requirements.txt

# Copy the rest of your app code and database
COPY . /code

# THE FIX: Tell the server to build its database from a.json right now!
RUN python ingest.py

# Boot the server safely
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]