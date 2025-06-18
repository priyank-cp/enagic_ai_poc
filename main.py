# main.py

import streamlit as st
st.set_page_config(page_title="Commission Co-Pilot", layout="wide", page_icon="🤖")

from ui_components import inject_custom_css
inject_custom_css()

from dotenv import load_dotenv
load_dotenv()

import os
from openai import OpenAI

from database import MongoManager, MemoryManager
from app.auth import show_login_ui
from app.chat_ui import show_main_chat_ui
from app.state import initialize_session_state

# --- Resource Initialization ---
@st.cache_resource
def init_resources():
    """Initializes all shared resources and returns them."""
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    db_manager = None
    mongo_uri = os.getenv("MONGO_URI")

    # Store connection status in session_state to be displayed in the sidebar
    if mongo_uri:
        try:
            db_manager = MongoManager()
            st.session_state.db_status = {"type": "success", "message": "Connected to persistent database."}
        except Exception as e:
            db_manager = MemoryManager()
            st.session_state.db_status = {"type": "warning", "message": f"DB connection failed. Using temporary storage."}
    else:
        db_manager = MemoryManager()
        st.session_state.db_status = {"type": "warning", "message": "Using temporary storage (history will be lost)."}

    return openai_client, db_manager

# Initialize resources once
openai_client, db_manager = init_resources()

# --- Initialize Session State ---
initialize_session_state()

# --- Main Application Router ---
# if st.session_state.get("authenticated", False):
#     show_main_chat_ui(db_manager=db_manager, openai_client=openai_client)
# else:
#     show_login_ui()

show_main_chat_ui(db_manager=db_manager, openai_client=openai_client)