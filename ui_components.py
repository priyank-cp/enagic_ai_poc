# ui_components.py

import streamlit as st

def display_welcome_message():
    """Displays a professional welcome message in the chat container."""
    st.info("Welcome! I'm your Commission Co-Pilot. You can ask me to perform a task by typing, using your voice, or selecting an action from the dashboard above. How can I assist you today?")

def display_predefined_actions():
    """
    Displays the full actions dashboard. All actions are for display and initiated via chat.
    """
    with st.expander("✨ View Available Actions Dashboard", expanded=True):
        
        # Helper function to render all action boxes consistently
        def action_box(title, caption, is_working=False):
            if is_working:
                classname = "working-feature"
                caption_text = caption
            else:
                classname = "coming-soon-feature"
                caption_text = "(Coming Soon)"

            st.markdown(f"""
            <div class="action-box {classname}">
                <p class="action-title">{title}</p>
                <p class="action-caption">{caption_text if is_working else caption}</p>
                <p class="action-status">{"" if is_working else "(Coming Soon)"}</p>
            </div>
            """, unsafe_allow_html=True)

        # --- Daily Operations Section ---
        st.subheader("🛠️ Daily Operations", anchor=False)
        daily_actions = [
            ("Recover SAP Commission", "For cancelled orders", False),
            ("Reconcile SAP vs ES Sales", "For a specific date", True),
            ("Check Recovery Status", "For today's cancellations", False),
            ("Process Sales Payment", "For a specific date", False),
            ("Issue Payment", "Transfer or print check", False),
            ("Update ES Payment Result", "From a results file", False),
            ("Recover Canceled Orders", "From the ES system", False)
        ]
        
        cols = st.columns(4)
        for i, (title, caption, is_working) in enumerate(daily_actions):
            with cols[i % 4]:
                action_box(title, caption, is_working)

        # --- Month-End Operations Section ---
        st.subheader("📅 Month-End Operations", anchor=False)
        monthly_actions = [
            ("Post Intercompany Debits", "Send debit notes", False),
            ("Accrue & Reverse Commissions", "Handle IC commission", False),
            ("Reconcile IC Payments", "Match payment instructions", False),
            ("Send Balance Confirmations", "To IC partners", False)
        ]
        cols = st.columns(4)
        for i, (title, caption, is_working) in enumerate(monthly_actions):
            with cols[i % 4]:
                action_box(title, caption, is_working)
        
        # --- Reports Section ---
        st.subheader("📊 Reports", anchor=False)
        report_actions = [
            ("General Commission Report", "View overall commissions", True),
            ("Top Vendor Payments", "Ranked for last month", False),
            ("6A Bonus Forecast", "Expected bonus accrual", False)
        ]
        cols = st.columns(4)
        for i, (title, caption, is_working) in enumerate(report_actions):
            with cols[i % 4]:
                action_box(title, caption, is_working)


def inject_custom_css():
    """Injects all necessary CSS for the layout."""
    st.markdown("""
        <style>
            /* Layout Adjustments */
            .main .block-container {
                padding-top: 2rem;
                padding-bottom: 10rem;
            }
            .sticky-input-bar {
                position: fixed; bottom: 0; left: 0; right: 0; width: 100%;
                background: white; padding: 1rem 1rem 1.5rem 1rem;
                border-top: 1px solid #e0e0e0; z-index: 9999;
            }

            /* Chat Message Styling */
            .stChatMessage { max-width: 85%; border-radius: 1rem; }

            /* Action Box Styling */
            .action-box {
                padding: 0.75rem; border-radius: 0.5rem; text-align: center;
                margin-bottom: 1rem; min-height: 100px; display: flex;
                flex-direction: column; justify-content: center; align-items: center;
            }
            .action-title { font-weight: bold; font-size: 0.9rem; margin-bottom: 0.25rem; line-height: 1.2; }
            .action-caption { font-size: 0.8rem; margin: 0; line-height: 1.1; color: #555; }
            .action-status { font-size: 0.75rem; font-style: italic; color: #888; margin-top: 0.25rem;}
            .working-feature { background-color: #e8f5e9; border: 1px solid #a5d6a7; }
            .coming-soon-feature { background-color: #fafafa; border: 1px solid #eeeeee; }
        </style>
    """, unsafe_allow_html=True)