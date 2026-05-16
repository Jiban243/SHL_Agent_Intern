import streamlit as st
import requests

# --- CONFIGURATION ---
# Replace this with your actual Hugging Face Space URL + /chat
API_URL = "https://jibank-shl-agent-intern.hf.space/chat" 

st.set_page_config(page_title="SHL Agent - Intern", page_icon="🤖", layout="centered")

# --- SIDEBAR ---
with st.sidebar:
    st.title("SHL Agent - Intern")
    st.markdown("Welcome to the SHL Assessment Recommender.")
    st.divider()
    if st.button("New Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

st.title("Assessment Recommender Chat")

# --- SESSION STATE ---
# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- RENDER HISTORY ---
# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # If there are recommendations saved in the history, display them as cards
        if "recommendations" in message and message["recommendations"]:
            st.markdown("### Suggested Assessments:")
            for rec in message["recommendations"]:
                # The border=True creates that nice "card" look from your screenshot
                with st.container(border=True): 
                    st.markdown(f"**[{rec['name']}]({rec['url']})**")
                    st.caption(f"Type: {rec.get('test_type', 'General')}")

# --- USER INPUT ---
# React to user input
if prompt := st.chat_input("E.g., I need a mid-level Python developer test..."):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Prepare payload for backend (FastAPI expects a list of dictionaries with role/content)
    payload = {
        "messages": [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
    }

    # --- API CALL ---
    with st.spinner("Agent is searching the catalog..."):
        try:
            response = requests.post(API_URL, json=payload)
            response.raise_for_status() # Raise an error for bad status codes
            data = response.json()
            
            # 🚨 THE DEBUG LINE: This will print the exact JSON your API is sending back
            # st.write("DEBUG - RAW API RESPONSE:", data)
            
            assistant_message = data.get("reply", "Sorry, I couldn't process that.")
            recommendations = data.get("recommendations", [])
            
            # Display assistant response
            with st.chat_message("assistant"):
                st.markdown(assistant_message)
                
                # Display the assessment cards dynamically
                if recommendations:
                    st.markdown("### Suggested Assessments:")
                    for rec in recommendations:
                        with st.container(border=True):
                            st.markdown(f"**[{rec['name']}]({rec['url']})**")
                            st.caption(f"Type: {rec.get('test_type', 'General')}")
            
            # Add assistant response (and its recommendations) to the session state history
            st.session_state.messages.append({
                "role": "assistant", 
                "content": assistant_message,
                "recommendations": recommendations
            })
            
        except Exception as e:
            st.error(f"Error connecting to backend: Make sure your API_URL is correct! Details: {e}")