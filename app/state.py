# app/state.py

import streamlit as st
from agent_logic import get_planned_action
import pandas as pd

def get_db_manager():
    from main import db_manager
    return db_manager

# --- Session State Initialization ---
def initialize_session_state():
    """Initializes all necessary keys in the session state."""
    defaults = {
        "authenticated": False,
        "messages": [],
        "pending_action": None,
        "prompt_input": "",
        "db_status": None  # <-- New key for database status message
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# --- Helper & Callback Functions ---
def add_message(role, content):
    """Adds a message to the chat history and saves it to the database."""
    db_manager = get_db_manager()
    
    savable_content = content
    if isinstance(content, pd.DataFrame):
        savable_content = content.to_dict('records')

    st.session_state.messages.append({"role": role, "content": savable_content})
    
    chat_id = st.session_state.get("chat_id")
    st.session_state.chat_id = db_manager.save_message(chat_id, role, savable_content)

def handle_user_input(prompt):
    """Processes a user's prompt, plans an action, and updates state."""
    add_message("user", prompt)
    with st.spinner("Understanding your request..."):
        planned_action = get_planned_action(prompt)
    
    if planned_action and planned_action.get("action") == "chitchat":
        add_message("assistant", planned_action["args"]["message"])
    elif planned_action:
        st.session_state.pending_action = planned_action
        confirmation_message = f"I understand you want to perform the action: **{planned_action['action']}** with the parameters **{planned_action['args']}**. Should I proceed?"
        add_message("assistant", confirmation_message)

def process_text_input():
    """Callback function to process and clear the text input."""
    prompt_to_process = st.session_state.prompt_input.strip()
    if prompt_to_process:
        handle_user_input(prompt_to_process)
        st.session_state.prompt_input = ""