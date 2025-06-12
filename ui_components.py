# ui_components.py

import streamlit as st

def inject_custom_css():
    """
    Injects custom CSS to style the app and create a custom sticky input bar.
    """
    st.markdown("""
        <style>
            /* Main chat container */
            .st-emotion-cache-1jicfl2 {
                flex-direction: column-reverse;
                overflow-y: auto;
            }

            /* Add padding to the bottom of the main app to prevent overlap with the sticky bar */
            .main .block-container {
                padding-bottom: 8rem; 
            }

            /* --- Custom Sticky Input Bar --- */
            /* This is the container for our text input and mic button */
            .st-emotion-cache-1fplaw9 {
                position: fixed;
                bottom: 0;
                width: 100%;
                background-color: white;
                border-top: 1px solid #e0e0e0;
                padding: 10px 1rem 20px 1rem;
                z-index: 999;
            }

            /* Chat messages styling (remains the same) */
            .st-emotion-cache-1c7y2kd {
                width: 100%;
                display: flex;
            }
            .stChatMessage {
                max-width: 85%;
                padding: 0.75rem 1rem;
                border-radius: 1rem;
                margin-bottom: 0.5rem;
                line-height: 1.6;
            }

            /* AI (Assistant) message */
            [data-testid="stChatMessage"]:has([data-testid="stStreamlitUIAvatar-assistant"]) {
                background-color: #f0f2f6;
                color: #333;
                align-self: flex-start;
            }

            /* User message */
            [data-testid="stChatMessage"]:has([data-testid="stStreamlitUIAvatar-user"]) {
                background-color: #0b93f6;
                color: white;
                align-self: flex-end;
            }
            
            /* Align user message to the right */
            .st-emotion-cache-1c7y2kd:has([data-testid="stStreamlitUIAvatar-user"]) {
                justify-content: flex-end;
            }
        </style>
    """, unsafe_allow_html=True)

def display_predefined_actions():
    """
    Displays the list of predefined actions in a collapsible expander.
    """
    with st.expander("✨ View Available Actions", expanded=True):
        st.markdown("""
        You can ask the agent to perform the following actions using text or voice.
        
        * **Get Invoice Count:** *"How many invoices did we have for 2025-06-15?"*
        * **Fetch Invoice Details:** *"Show me the invoice details for today."*
        * **Reconcile System:** *"Reconcile the ES system for vendor 'Global Imports' for yesterday."*
        * **List Overdue Orders:** *"List upcoming overdue sales orders."*
        * **List Overdue Invoices:** *"Are there any invoices about to be overdue?"*
        """)