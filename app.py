# app.py

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import os
import pandas as pd
from streamlit_mic_recorder import mic_recorder
from database import MongoManager, MemoryManager
from agent_logic import get_planned_action, execute_action
from ui_components import inject_custom_css, display_predefined_actions
from openai import OpenAI

# --- Page Configuration and Initialization ---
st.set_page_config(page_title="AI Business Agent", layout="wide", page_icon="🤖")
inject_custom_css()

# --- Dynamic Resource Initialization ---
@st.cache_resource
def init_resources():
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    db_manager = None
    mongo_uri = os.getenv("MONGO_URI")
    if mongo_uri:
        try:
            db_manager = MongoManager()
            st.success("Connected to MongoDB. Chat history will be saved.", icon="🗄️")
        except Exception as e:
            st.warning(f"MongoDB connection failed: {e}. Falling back to in-memory storage.", icon="⚠️")
            db_manager = MemoryManager()
    else:
        st.warning("MongoDB URI not found. Using in-memory storage (history will be lost on session end).", icon="⚠️")
        db_manager = MemoryManager()
    return openai_client, db_manager

openai_client, db_manager = init_resources()

# --- Session State Initialization ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_action" not in st.session_state:
    st.session_state.pending_action = None
if "prompt_input" not in st.session_state:
    st.session_state.prompt_input = ""

# --- Helper and Callback Functions ---
def add_message(role, content):
    st.session_state.messages.append({"role": role, "content": content})
    if st.session_state.get("chat_id"):
        st.session_state.chat_id = db_manager.save_message(st.session_state.chat_id, role, content)
    else:
        st.session_state.chat_id = db_manager.save_message(None, role, content)

def handle_user_input(prompt):
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
    prompt = st.session_state.prompt_input.strip()
    if prompt:
        handle_user_input(prompt)

# --- LOGIN UI FUNCTION ---
def show_login_ui():
    st.title("Welcome to the AI Business Agent")
    st.markdown("Please log in to continue.")
    correct_username = os.getenv("APP_USERNAME")
    correct_password = os.getenv("APP_PASSWORD")
    if not correct_username or not correct_password:
        st.error("Authentication credentials are not set. Please contact the administrator.")
        return
    with st.form("login_form"):
        username = st.text_input("Username").lower()
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log In")
        if submitted:
            if username == correct_username and password == correct_password:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Invalid username or password.")

# --- MAIN CHAT UI FUNCTION ---
def show_main_chat_ui():
    with st.sidebar:
        st.title("Business Agent")
        st.markdown("---")
        if st.button("➕ New Chat", use_container_width=True):
            # Clear relevant chat state, but preserve authentication and db manager
            st.session_state.messages = []
            st.session_state.pending_action = None
            if 'chat_id' in st.session_state:
                del st.session_state['chat_id']
            st.rerun()

        st.markdown("#### Chat History")
        chat_summaries = db_manager.get_chat_summaries()
        if "chat_id" not in st.session_state:
            st.session_state.chat_id = None
        for chat in chat_summaries:
            col1, col2 = st.columns([4, 1])
            if col1.button(chat["title"], key=f"load_{chat['chat_id']}", use_container_width=True):
                st.session_state.chat_id = chat["chat_id"]
                st.session_state.messages = db_manager.get_chat_messages(chat['chat_id'])
                st.session_state.pending_action = None
                st.rerun()
            if col2.button("🗑️", key=f"del_{chat['chat_id']}", help="Delete chat"):
                db_manager.delete_chat(chat['chat_id'])
                if st.session_state.chat_id == chat['chat_id']:
                    st.session_state.chat_id = None
                    st.session_state.messages = []
                    st.session_state.pending_action = None
                st.rerun()

        st.markdown("---")
        # --- THIS IS THE CORRECTED SECTION ---
        if st.button("Clear All History", type="primary", use_container_width=True):
            # Delegate clearing to the database manager
            db_manager.clear_all_history()
            # Reset the current chat UI state
            st.session_state.messages = []
            st.session_state.pending_action = None
            if 'chat_id' in st.session_state:
                del st.session_state['chat_id']
            st.rerun()
        # --- END OF CORRECTION ---

    # Main Chat Panel
    st.header("Conversational Interface")
    display_predefined_actions()
    st.markdown("---")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            content = msg["content"]
            if isinstance(content, list):
                st.dataframe(pd.DataFrame(content), use_container_width=True)
            else:
                st.markdown(content)

    if st.session_state.pending_action:
        col1, col2, col3 = st.columns([1, 1, 4])
        if col1.button("✅ Yes, proceed", use_container_width=True):
            with st.spinner("Executing action..."):
                action_to_run = st.session_state.pending_action
                st.session_state.pending_action = None
                result = execute_action(action_to_run)
                add_message("assistant", result)
                st.rerun()
        if col2.button("❌ No, cancel", use_container_width=True):
            st.session_state.pending_action = None
            add_message("assistant", "Action cancelled.")
            st.rerun()

    # Custom Sticky User Input
    input_container = st.container()
    with input_container:
        input_disabled = st.session_state.pending_action is not None
        audio_bytes = None
        if not input_disabled:
            col1, col2 = st.columns([8, 1])
            with col1:
                st.text_input(
                    "Your message...", key="prompt_input",
                    on_change=process_text_input, disabled=input_disabled,
                    label_visibility="collapsed"
                )
            with col2:
                audio_bytes = mic_recorder(
                    start_prompt="🎤", stop_prompt="⏹️",
                    key='mic', just_once=True, use_container_width=True
                )
        if audio_bytes:
            with st.spinner("Transcribing..."):
                audio_file = {"file": audio_bytes['bytes'], "name": "audio.wav"}
                try:
                    transcript = openai_client.audio.transcriptions.create(model="whisper-1", file=(audio_file['name'], audio_file['file']))
                    handle_user_input(transcript.text)
                    st.rerun()
                except Exception as e:
                    st.error(f"Voice transcription failed: {e}", icon="🚨")

# --- MAIN APP LOGIC ---
if st.session_state.authenticated:
    show_main_chat_ui()
else:
    show_login_ui()