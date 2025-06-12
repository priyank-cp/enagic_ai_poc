# agent_logic.py

import os
import json
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.tools import Tool
from tools import (
    get_invoice_count, fetch_invoice_details, reconcile_es_system,
    list_upcoming_overdue_sales_orders, list_upcoming_overdue_invoices
)

def manually_render_text_descriptions(tools: list[Tool]) -> str:
    """
    Manually formats a list of Tool objects into a string for the prompt.
    """
    output = ""
    for tool in tools:
        description = tool.description.strip() if tool.description else "No description available."
        output += f"{tool.name}: {description}\n\n"
    return output

# --- Tool and Model Setup ---

AVAILABLE_TOOLS = {
    "get_invoice_count": get_invoice_count,
    "fetch_invoice_details": fetch_invoice_details,
    "reconcile_es_system": reconcile_es_system,
    "list_upcoming_overdue_sales_orders": list_upcoming_overdue_sales_orders,
    "list_upcoming_overdue_invoices": list_upcoming_overdue_invoices
}

tool_objects = [
    Tool(name="get_invoice_count", func=get_invoice_count, description=get_invoice_count.__doc__),
    Tool(name="fetch_invoice_details", func=fetch_invoice_details, description=fetch_invoice_details.__doc__),
    Tool(name="reconcile_es_system", func=reconcile_es_system, description=reconcile_es_system.__doc__),
    Tool(name="list_upcoming_overdue_sales_orders", func=list_upcoming_overdue_sales_orders, description=list_upcoming_overdue_sales_orders.__doc__),
    Tool(name="list_upcoming_overdue_invoices", func=list_upcoming_overdue_invoices, description=list_upcoming_overdue_invoices.__doc__),
]

llm = ChatOpenAI(model="gpt-4-turbo", temperature=0, api_key=os.getenv("OPENAI_API_KEY"))

prompt_template_string = """
You are an AI assistant that understands user requests and identifies the correct business action to take.
You do not execute the action, you only identify it.

Here are the available actions:
{tool_descriptions}

Based on the user's request: "{user_input}", determine which action to take.
Respond in one of two ways:

1. If the request maps to one of the available actions, provide a JSON object with the action name and parameters.
   Example: {{"action": "get_invoice_count", "args": {{"sales_date": "2025-06-12"}}}}

2. If the request does not map to any action (e.g., it's a greeting or a general question), respond with a conversational fallback message.
   Example: "I can only assist with business actions related to invoices and sales orders. How can I help you with that today?"

Your response should be ONLY the JSON object or the fallback message.
The current date is June 12, 2025.
"""

prompt = ChatPromptTemplate.from_template(prompt_template_string)

def get_planned_action(user_input: str):
    """
    First step: Understand the user's intent and plan the action without executing.
    Returns a dictionary with the planned tool and its arguments, or a conversational response.
    """
    tool_descriptions = manually_render_text_descriptions(tool_objects)
    
    chain = prompt | llm
    try:
        response = chain.invoke({
            "tool_descriptions": tool_descriptions,
            "user_input": user_input
        })
        content = response.content
        
        # --- THIS IS THE CORRECTED SECTION ---
        try:
            planned_action = json.loads(content)
            # Add a robust check to ensure the loaded JSON is a valid dictionary with the keys we expect.
            # This prevents errors if the AI returns `null` or a malformed dict.
            if isinstance(planned_action, dict) and "action" in planned_action and "args" in planned_action:
                return planned_action
            else:
                # If it's valid JSON but not what we expect, treat it as a conversational response.
                return {"action": "chitchat", "args": {"message": content}}
        except (json.JSONDecodeError, TypeError):
            # If the content isn't valid JSON at all, it's definitely a conversational response.
            return {"action": "chitchat", "args": {"message": content}}
    # --- END OF CORRECTION ---
            
    except Exception as e:
        error_message = f"An error occurred: {e}"
        print(f"Error in get_planned_action: {e}")
        return {"action": "chitchat", "args": {"message": error_message}}

def execute_action(action: dict):
    """
    Second step: Execute the confirmed action and return the result.
    """
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