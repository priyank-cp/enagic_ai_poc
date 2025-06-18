# ui_components.py

import streamlit as st
import base64
from pathlib import Path
import pandas as pd
import random

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
            ("0. Execute all steps 1-7 for the SAP ES Matched Data", "", False),
            ("1. Recover SAP Commission For cancelled orders", "", False),
            ("2. Reconcile SAP vs ES Commission For a specific date", "", True),
            ("3. Check Commission Recovery Status For today's payments", "", False),
            ("4. Execute SAP payment for a specific sale date", "", False),
            ("5. Create a bank transfer file or print cheque", "", False),
            ("6. Update SAP payment at ES", "", False),
            ("7. Download the summary of commission payments for a sales date", "", False),
            ("8. E8PA Members Fast commission payment", "", False)
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
            ("Send Balance Confirmations", "To IC partners", False),
            ("TDS Report", "", False),
            ("Send Commision GST Invoices", "", False),
            ("Scan the gst_commission_ind@enagic.com email post GST commission invoices and make GST payment to the distributor", "", False)
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

         # --- Year-End Operationsn ---
        st.subheader("📆 Year-End Operations", anchor=False)
        yearly_actions = [
            ("1099 report and list of distributor who had a name or SSN change", "", False)
        ]
        cols = st.columns(4)
        for i, (title, caption, is_working) in enumerate(yearly_actions):
            with cols[i % 2]:
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

            /* Microphone Button Styling */
            .stMicRecorder button {
                background: none !important;
                border: none !important;
                padding: 10px !important;
                border-radius: 50% !important;
                transition: all 0.3s ease !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                font-size: 24px !important;
                width: 44px !important;
                height: 44px !important;
                min-width: 44px !important;
                min-height: 44px !important;
            }
            .stMicRecorder button:hover {
                background-color: #f0f0f0 !important;
            }
            .stMicRecorder button.recording {
                background-color: #ff4444 !important;
                animation: pulse 1.5s infinite !important;
            }
            @keyframes pulse {
                0% { transform: scale(1); }
                50% { transform: scale(1.1); }
                100% { transform: scale(1); }
            }
        </style>
    """, unsafe_allow_html=True)

def display_reconciliation_results(result: dict, idx=None):
    """Display reconciliation results in the chat UI"""
    if result["status"] == "error":
        st.error(result["message"])
        return

    details = result["details"]
    st.info(f"Reconciliation completed for period {details['start_date']} to {details['end_date']}")
    print(f"idx: {idx}")
    # Display unmatched amounts
    if details["unmatched_amounts"]:
        st.write("#### Unmatched Amounts")
        df_unmatched = pd.DataFrame(details["unmatched_amounts"])
        st.dataframe(df_unmatched)
        # Download button for complete list
        csv = pd.DataFrame(details["unmatched_amounts"]).to_csv(index=False)
        st.download_button(
            label="Download Complete List",
            data=csv,
            file_name="unmatched_amounts.csv",
            mime="text/csv",
            key=f"unmatched_download_btn_{idx}" if idx is not None else "unmatched_download_btn"
        )
    # Display payment block removal
    if details["payment_block_removal"]:
        st.write("#### You can remove the payment block for the following records from SAP")
        df_payment_block = pd.DataFrame(details["payment_block_removal"])
        st.dataframe(df_payment_block)
        # Confirmation button if there are records
        if len(details["payment_block_removal"]) > 0:
            btn_key = f"remove_payment_block_btn_{idx}" if idx is not None else "remove_payment_block_btn"
            if st.button(
                f"Remove Payment Block for {len(details['payment_block_removal'])} records",
                key=btn_key,
            ):
                print("Removing payment block...====>")
                from agent_logic import execute_action
                result = execute_action({
                    "action": "remove_payment_block",
                    "args": {"records": details["payment_block_removal"]}
                })
                st.success(result.get("result", {}).get("message", "Payment block removed from SAP"))

# Tool-to-UI mapping for dynamic invocation
TOOL_UI_RENDERERS = {
    "reconcile_sap_vs_es_sales": display_reconciliation_results,
}