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
def add_message(role: str, content: str | pd.DataFrame):
    """Adds a message to the chat history and saves it to the database."""
    try:
        # Convert content to savable format
        savable_content = content
        if isinstance(content, pd.DataFrame):
            savable_content = content.to_dict('records')
        
        # Add to session state
        st.session_state.messages.append({"role": role, "content": savable_content})
        
        # Save to database if available
        chat_id = st.session_state.get("chat_id")
        print("chat_id", chat_id)
        if chat_id is not None:
            try:
                st.session_state.chat_id = get_db_manager().save_message(chat_id, role, savable_content)
            except Exception as db_error:
                print(f"Database save error: {str(db_error)}")
                # Continue even if database save fails
                pass
    except Exception as e:
        print(f"Error in add_message: {str(e)}")
        # Ensure the message is at least added to the session state
        st.session_state.messages.append({"role": role, "content": str(content)})

def handle_user_input(user_input: str):
    """Processes user input and updates chat state."""
    if not user_input:
        return

    # Add user message to chat
    add_message("user", user_input)

    # Get planned action from LLM
    planned_action = get_planned_action(user_input)
    print("============planned_action===============")
    print(planned_action)

    # Handle the response based on status
    if planned_action["status"] == "action_found":
        # Set pending action for confirmation
        st.session_state.pending_action = {
            "action": planned_action["action"],
            "args": planned_action["args"]
        }
        add_message("assistant", f"{planned_action['message']}. Would you like me to proceed?")
    else:
        add_message("assistant", planned_action["message"])

def handle_voice_input(audio_data):
    """Processes voice input and updates chat state."""
    if not audio_data:
        return

    # Show processing status for audio
    with st.status("🎤 Processing your voice input...", expanded=True) as status:
        try:
            # Transcribe audio
            text = transcribe_audio(audio_data)
            status.update(label="✅ Voice processing complete!", state="complete")
            
            if text:
                # Process the transcribed text
                handle_user_input(text)
            else:
                add_message("assistant", "I couldn't understand the audio. Could you please try again or type your message?")
        except Exception as e:
            status.update(label="❌ Voice processing failed", state="error")
            add_message("assistant", f"Voice transcription failed: {str(e)}")

def process_text_input():
    """Callback function to process and clear the text input."""
    prompt_to_process = st.session_state.prompt_input.strip()
    if prompt_to_process:
        # Disable the input while processing
        st.session_state.input_disabled = True
        handle_user_input(prompt_to_process)
        # Re-enable the input after processing
        st.session_state.input_disabled = False

# Before rendering the text_input in your UI function:
if st.session_state.get("clear_prompt_input", False):
    st.session_state.prompt_input = ""
    st.session_state.clear_prompt_input = False

# Removed duplicate st.text_input to avoid duplicate key error
# st.text_input("Your message...", key="prompt_input", on_change=process_text_input)