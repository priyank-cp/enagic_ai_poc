# agent_logic.py

import os
import json
import pandas as pd
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.tools import Tool

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

# Dictionary of all available tool functions
AVAILABLE_TOOLS = {
    "recover_sap_commission": recover_sap_commission,
    "reconcile_sap_vs_es_sales": reconcile_sap_vs_es_sales,
    "check_recovery_status": check_recovery_status,
    "process_sales_payment": process_sales_payment,
    "issue_payment": issue_payment,
    "update_es_payment_result": update_es_payment_result,
    "recover_canceled_orders": recover_canceled_orders,
    "post_intercompany_debits": post_intercompany_debits,
    "accrue_reverse_commissions": accrue_reverse_commissions,
    "reconcile_intercompany_payments": reconcile_intercompany_payments,
    "send_balance_confirmations": send_balance_confirmations,
    "get_general_commission_report": get_general_commission_report,
    "get_top_vendor_payments": get_top_vendor_payments,
    "get_6a_bonus_forecast": get_6a_bonus_forecast,
}

# Create a list of Tool objects for the agent
tool_objects = [Tool(name=name, func=func, description=func.__doc__) for name, func in AVAILABLE_TOOLS.items()]

llm = ChatOpenAI(model="gpt-4-turbo", temperature=0, api_key=os.getenv("OPENAI_API_KEY"))

prompt_template_string = """
You are an AI assistant that understands user requests and identifies the correct business action to take.
You do not execute the action, you only identify it.
The user's request might be imprecise; map it to the best available tool.

Here are the available actions:
{tool_descriptions}

Based on the user's request: "{user_input}", determine which action to take.
Respond in one of two ways:

1. If the request maps to one of the available actions, provide a JSON object with the action name and parameters.
   Example for a tool with arguments: {{"action": "process_sales_payment", "args": {{"sales_date": "2025-06-12"}}}}
   Example for a tool with no arguments: {{"action": "check_recovery_status", "args": {{}}}}

2. If the request does not map to any action, respond with a conversational fallback message.

Your response should be ONLY the JSON object or the fallback message.
The current date is June 13, 2025.
"""

prompt = ChatPromptTemplate.from_template(prompt_template_string)

def get_planned_action(user_input: str):
    tool_descriptions = manually_render_text_descriptions(tool_objects)
    chain = prompt | llm
    try:
        response = chain.invoke({"tool_descriptions": tool_descriptions, "user_input": user_input})
        content = response.content
        try:
            planned_action = json.loads(content)
            if isinstance(planned_action, dict) and "action" in planned_action and "args" in planned_action:
                return planned_action
            else:
                return {"action": "chitchat", "args": {"message": content}}
        except (json.JSONDecodeError, TypeError):
            return {"action": "chitchat", "args": {"message": content}}
    except Exception as e:
        error_message = f"An error occurred: {e}"
        print(f"Error in get_planned_action: {e}")
        return {"action": "chitchat", "args": {"message": error_message}}

def execute_action(action: dict):
    tool_name = action.get("action")
    tool_args = action.get("args")
    if tool_name in AVAILABLE_TOOLS:
        try:
            tool_function = AVAILABLE_TOOLS[tool_name]
            result = tool_function(**tool_args)
            return result
        except Exception as e:
            print(f"Error executing tool {tool_name}: {e}")
            return f"An error occurred while trying to perform the action: {e}"
    else:
        return "I'm sorry, I cannot perform that action."