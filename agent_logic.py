# agent_logic.py

import os
import json
import pandas as pd
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.tools import Tool
import streamlit as st
from datetime import datetime
import re

# --- Import all tools from the new modular files ---
from tools.daily_ops import *
from tools.monthly_ops import *
from tools.reports import *

def manually_render_text_descriptions(tools: list[Tool]) -> str:
    output = ""
    for tool in tools:
        description = tool.description.strip() if tool.description else "No description available."
        output += f"{tool.name}: {description}\n\n"
    return output

# --- Tool and Model Setup ---

# Dictionary of all available tool functions with their parameter requirements
AVAILABLE_TOOLS = {
    "recover_sap_commission": {
        "func": recover_sap_commission,
        "required_params": ["order_id", "reason"],
        "description": "Recovers commission from SAP for a specific cancelled order ID and reason.",
        "param_descriptions": {
            "order_id": "The ID of the cancelled order",
            "reason": "The reason for commission recovery"
        }
    },
    "reconcile_sap_vs_es_sales": {
        "func": reconcile_sap_vs_es_sales,
        "required_params": ["start_date", "end_date"],
        "description": "Reconciles sales data between SAP and ES for a given date range.",
        "param_descriptions": {
            "start_date": "Start date in YYYY-MM-DD format or natural language (e.g., 'this month', 'last quarter')",
            "end_date": "End date in YYYY-MM-DD format or natural language"
        }
    },
    "check_recovery_status": {
        "func": check_recovery_status,
        "required_params": [],
        "description": "Checks if today's order cancellations are fully recovered in payment.",
        "param_descriptions": {}
    },
    "process_sales_payment": {
        "func": process_sales_payment,
        "required_params": ["sales_date"],
        "description": "Processes sales payment for a specific sales date.",
        "param_descriptions": {
            "sales_date": "The sales date in YYYY-MM-DD format or natural language"
        }
    },
    "issue_payment": {
        "func": issue_payment,
        "required_params": ["amount", "vendor_id"],
        "description": "Issues a payment to a vendor for a specific amount.",
        "param_descriptions": {
            "amount": "The payment amount",
            "vendor_id": "The ID of the vendor to pay"
        }
    },
    "update_es_payment_result": {
        "func": update_es_payment_result,
        "required_params": ["file_name"],
        "description": "Updates the payment result for a specific file.",
        "param_descriptions": {
            "file_name": "The name of the file containing payment results"
        }
    },
    "recover_canceled_orders": {
        "func": recover_canceled_orders,
        "required_params": [],
        "description": "Recovers canceled orders.",
        "param_descriptions": {}
    },
    "post_intercompany_debits": {
        "func": post_intercompany_debits,
        "required_params": [],
        "description": "Posts intercompany debits.",
        "param_descriptions": {}
    },
    "accrue_reverse_commissions": {
        "func": accrue_reverse_commissions,
        "required_params": [],
        "description": "Accrues reverse commissions.",
        "param_descriptions": {}
    },
    "reconcile_intercompany_payments": {
        "func": reconcile_intercompany_payments,
        "required_params": [],
        "description": "Reconciles intercompany payments.",
        "param_descriptions": {}
    },
    "send_balance_confirmations": {
        "func": send_balance_confirmations,
        "required_params": [],
        "description": "Sends balance confirmations.",
        "param_descriptions": {}
    },
    "get_general_commission_report": {
        "func": get_general_commission_report,
        "required_params": ["start_date", "end_date"],
        "description": "Generates a general commission report for a given date range.",
        "param_descriptions": {
            "start_date": "Start date in YYYY-MM-DD format or natural language",
            "end_date": "End date in YYYY-MM-DD format or natural language"
        }
    },
    "get_top_vendor_payments": {
        "func": get_top_vendor_payments,
        "required_params": [],
        "description": "Gets the top vendor payments.",
        "param_descriptions": {}
    },
    "get_6a_bonus_forecast": {
        "func": get_6a_bonus_forecast,
        "required_params": [],
        "description": "Gets the 6A bonus forecast.",
        "param_descriptions": {}
    }
}

# Create a list of Tool objects for the agent
tool_objects = [Tool(name=name, func=info["func"], description=info["description"]) for name, info in AVAILABLE_TOOLS.items()]

def generate_tool_descriptions() -> str:
    """Generates a formatted string of all available tools and their parameters."""
    descriptions = []
    for name, tool in AVAILABLE_TOOLS.items():
        desc = f"- {name}: {tool['description']}\n"
        if 'required_params' in tool:
            desc += "  Required parameters:\n"
            for param in tool['required_params']:
                param_desc = f"    - {param}: {tool['param_descriptions'][param]}"
                if param in ['start_date', 'end_date']:
                    param_desc += " (Must be in YYYY-MM-DD format. Natural language dates like 'today', 'this month', etc. will be automatically converted)"
                desc += param_desc + "\n"
        descriptions.append(desc)
    return "\n".join(descriptions)

llm = ChatOpenAI(model="gpt-4-turbo", temperature=0, api_key=os.getenv("OPENAI_API_KEY"))

def get_date_prediction_prompt() -> str:
    today = datetime.now().date()
    current_year = today.year
    today_str = today.strftime("%Y-%m-%d")

    return f"""
    Today's date is {today_str}. Use this to resolve natural language dates:
    - "this year" → {current_year}-01-01 to {today_str}
    - "last year" → {current_year - 1}-01-01 to {current_year - 1}-12-31
    Always return dates in YYYY-MM-DD format.
    Never hardcode years like 2023.
    """
    

prompt_template_string = """
You are an AI assistant that helps users perform specific actions. Your task is to analyze the user's input and determine what action they want to take.

Available tools:
{tool_descriptions}

IMPORTANT: Always extract and normalize date ranges from user input.
{date_prediction_prompt}

{conversation_context}

User input: {user_input}

CRITICAL: Your response must be a raw JSON object without any markdown formatting or code block notation. DO NOT include ```json or any other markdown formatting.

Based on the user's input and conversation context, determine if they want to perform any of the available actions. If they do, return a JSON object with the following structure:
{{
    "status": "action_found",
    "action": "name_of_action",
    "args": {{
        "param1": "value1",
        "param2": "value2"
    }},
    "message": "A natural, user-friendly message that includes the detected parameters in a conversational way. For example: 'I'll help you reconcile SAP vs ES sales data for the period from [start_date] to [end_date].'"
}}

If the user's input is unclear or doesn't match any available actions, return:
{{
    "status": "action_not_found",
    "message": "I couldn't understand what action you want to take. Could you please rephrase your request?",
    "type": "unclear_action"
}}

If the user's input matches an action but is missing required parameters, return:
{{
    "status": "action_not_found",
    "message": "I understand you want to [action], but I need [missing parameters]. Could you please specify [missing parameters]?",
    "type": "missing_parameters"
}}

If the user's input is a follow-up to a previous request (like providing missing parameters), use the conversation context to understand the full request.

Remember to:
1. Consider the conversation context when interpreting the user's input
2. If the user provides only parameters in a follow-up message, use the action from the previous context
3. Be specific about what information is missing
4. Return valid JSON that can be parsed by the application
5. ALWAYS convert dates to YYYY-MM-DD format
6. Handle natural language date expressions appropriately
7. DO NOT include any markdown formatting or code block notation in your response
8. Include a natural, conversational message that incorporates the detected parameters
9. NEVER hardcode years - always use the current year or calculate relative to current year
10. Handle variations of date expressions (e.g., "current month" = "this month")
11. For "this year" or similar expressions, ALWAYS use the current year (2024) and NEVER use 2023 or any other hardcoded year
"""

prompt = ChatPromptTemplate.from_template(prompt_template_string)

# Update the prompt with tool descriptions
prompt = prompt.partial(tool_descriptions=generate_tool_descriptions())

def get_planned_action(user_input: str) -> dict:
    """Determines the action to take based on user input."""
    tool_descriptions = generate_tool_descriptions()
    
    # Get conversation history
    conversation_history = st.session_state.get("messages", [])
    # Get the last 25 messages for context (excluding the current input)
    recent_messages = conversation_history[-25:-1] if len(conversation_history) > 1 else []
    
    # Format conversation history with token optimization
    conversation_context = ""
    if recent_messages:
        conversation_context = "Recent conversation (last 25 messages):\n"
        for msg in recent_messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            # Truncate long messages to save tokens
            content = str(msg['content'])
            if len(content) > 100:  # Truncate messages longer than 100 chars
                content = content[:97] + "..."
            conversation_context += f"{role}: {content}\n"
    
    # Update the prompt with conversation context
    chain = prompt | llm
    try:
        # Do not remove formatted_prompt commented code
        # formatted_prompt = prompt.format(tool_descriptions=tool_descriptions, user_input=user_input)
        # print("============formatted_prompt===============")
        # print(formatted_prompt)
        response = chain.invoke({
            "tool_descriptions": tool_descriptions, 
            "user_input": user_input,
            "date_prediction_prompt": get_date_prediction_prompt(),
            "conversation_context": conversation_context
        })
        content = response.content
        print("============content===============")
        print(content)
        try:
            planned_action = json.loads(content)
            if planned_action["status"] == "action_found" and "action" in planned_action and "args" in planned_action:
                return {
                    "status": "action_found",
                    "action": planned_action["action"],
                    "args": planned_action["args"],
                    "message": planned_action.get("message", f"I'll help you execute action {planned_action['action']}.")
                }
            else:
                return {
                    "status": "action_not_found",
                    "message": planned_action.get("message", "Action not found"),
                    "type": planned_action.get("type", "action_not_found")
                }
        except json.JSONDecodeError as e:
            return {
                "status": "action_not_found",
                "message": f"Failed to parse LLM response as JSON: {str(e)}",
                "type": "json_parse_error"
            }
    except Exception as e:
        print(e)
        return {
            "status": "action_not_found",
            "message": f"Error in get_planned_action: {str(e)}",
            "type": "execution_error"
        }

def execute_action(action: dict):
    tool_name = action.get("action")
    tool_args = action.get("args")
    if tool_name in AVAILABLE_TOOLS:
        try:
            tool_function = AVAILABLE_TOOLS[tool_name]["func"]
            result = tool_function(**tool_args)
            return {
                "tool": tool_name,
                "result": result
            }
        except Exception as e:
            return {
                "tool": tool_name,
                "error": str(e)
            }
    else:
        return {
            "tool": tool_name,
            "error": "Unknown tool"
        }