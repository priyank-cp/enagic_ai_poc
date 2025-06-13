# app/chat_ui.py

import streamlit as st
import pandas as pd
from streamlit_mic_recorder import mic_recorder
from agent_logic import execute_action
from ui_components import display_predefined_actions, display_welcome_message
from app.state import add_message, process_text_input, handle_user_input

def _render_sidebar(db_manager):
    """Renders the sidebar with chat history, controls, and DB status."""
    with st.sidebar:
        st.title("Commission Co-Pilot")
        st.markdown("---")
        if st.button("➕ New Chat", use_container_width=True):
            auth_state = st.session_state.authenticated
            for key in st.session_state.keys():
                del st.session_state[key]
            st.session_state.authenticated = auth_state
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
                if st.session_state.get("chat_id") == chat['chat_id']:
                    st.session_state.chat_id = None
                    st.session_state.messages = []
                    st.session_state.pending_action = None
                st.rerun()

        st.markdown("---")
        if st.button("Clear All History", type="primary", use_container_width=True):
            db_manager.clear_all_history()
            st.session_state.messages = []
            st.session_state.pending_action = None
            if 'chat_id' in st.session_state:
                del st.session_state['chat_id']
            st.rerun()

        st.markdown('<div style="margin-top: 2rem;"></div>', unsafe_allow_html=True)
        status_info = st.session_state.get("db_status")
        if status_info:
            if status_info["type"] == "success":
                st.success(status_info["message"], icon="🗄️")
            else:
                st.warning(status_info["message"], icon="⚠️")

def _render_chat_messages():
    """Renders the chat messages and action confirmation buttons."""
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            content = msg["content"]
            if isinstance(content, list):
                df = pd.DataFrame(content)
                if "Error" in df.columns:
                    st.error(df["Error"].iloc[0])
                elif df.empty:
                    st.write("No records found for your query.")
                else:
                    st.write("Here is a preview of the report:")
                    st.dataframe(df.head(10))
                    @st.cache_data
                    def convert_df_to_csv(d):
                        return d.to_csv(index=False).encode('utf-8')
                    csv_data = convert_df_to_csv(df)
                    st.download_button("📥 Download Full Report", csv_data, "report.csv", "text/csv")
            else:
                st.markdown(str(content))

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

def _render_user_input(openai_client):
    """Renders the user input bar."""
    st.markdown('<div class="sticky-input-bar">', unsafe_allow_html=True)
    input_container = st.container()
    with input_container:
        input_disabled = st.session_state.pending_action is not None
        audio_bytes = None
        if not input_disabled:
            col1, col2 = st.columns([8, 1])
            with col1:
                st.text_input("Your message...", key="prompt_input", on_change=process_text_input,
                              disabled=input_disabled, label_visibility="collapsed")
            with col2:
                audio_bytes = mic_recorder(start_prompt="🎙️", stop_prompt="⏹️", 
                                           key='mic', just_once=True, use_container_width=True)
        
        if audio_bytes:
            with st.spinner("Transcribing..."):
                try:
                    transcript = openai_client.audio.transcriptions.create(
                        model="whisper-1", file=("audio.wav", audio_bytes['bytes'])
                    )
                    handle_user_input(transcript.text)
                    st.rerun()
                except Exception as e:
                    st.error(f"Voice transcription failed: {e}", icon="🚨")
    st.markdown('</div>', unsafe_allow_html=True)


def show_main_chat_ui(db_manager, openai_client):
    """The main function to build the entire chat UI."""
    _render_sidebar(db_manager)
    
    st.header("Commission Co-Pilot")
    
    if not st.session_state.messages:
        display_welcome_message()
        
    # The dashboard is now for display purposes only.
    display_predefined_actions()
    st.markdown("---")

    _render_chat_messages()
    _render_user_input(openai_client)