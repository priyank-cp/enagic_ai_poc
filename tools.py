# tools.py

import datetime
import random
import requests
import os
import pandas as pd
from pymongo import MongoClient
from datetime import datetime, timedelta

def get_db_collection():
    """Connects to MongoDB and returns the sales collection."""
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        return None
    client = MongoClient(mongo_uri)
    db = client.get_database("ai_poc_db")
    return db.get_collection("sales")

# --- THIS IS THE UPDATED TOOL ---
def get_shipment_report(date_query: str) -> pd.DataFrame:
    """
    Gets a shipment report based on a delivery date. The input must be a single string for the 'date_query' parameter.
    Valid values for 'date_query' are keywords like 'this month', 'overdue', 'last 7 days', or a specific date in 'YYYY/MM/DD' format.
    """
    collection = get_db_collection()
    if collection is None:
        return pd.DataFrame({"Error": ["Could not connect to the database."]})

    today = datetime.now()
    query = {}
    
    # --- New Validation Logic ---
    normalized_query = date_query.lower().strip()
    
    if "this month" in normalized_query:
        first_day_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        query["Delivery Date"] = {"$gte": first_day_of_month.strftime("%Y/%m/%d")}
    elif "overdue" in normalized_query:
        query["Delivery Date"] = {"$lt": today.strftime("%Y/%m/%d")}
    elif "last 7 days" in normalized_query:
        seven_days_ago = today - timedelta(days=7)
        query["Delivery Date"] = {"$gte": seven_days_ago.strftime("%Y/%m/%d")}
    else:
        # Try to parse the query as a specific date
        try:
            # This is just for validation, not for the query itself
            datetime.strptime(normalized_query, "%Y/%m/%d")
            query["Delivery Date"] = normalized_query
        except ValueError:
            # If it's not a known keyword or a valid date format, return a helpful error.
            error_message = f"I didn't understand the date '{date_query}'. Please try a specific date like '2025/05/30', or a period like 'this month' or 'overdue'."
            return pd.DataFrame({"Error": [error_message]})

    projection = {
        "_id": 0, "Name": 1, "ItemCode": 1, "quantity": 1, "price": 1,
        "Delivery Date": 1, "ship to address": 1, "ship to city": 1,
        "ship to country": 1, "GWS Order number": 1
    }

    try:
        records = list(collection.find(query, projection).sort("Delivery Date", -1).limit(200))
        if not records:
            return pd.DataFrame()
        
        for record in records:
            if 'GWS Order number' in record and isinstance(record['GWS Order number'], dict):
                record['GWS Order number'] = record['GWS Order number'].get('$numberLong', None)

        return pd.DataFrame(records)
    except Exception as e:
        print(f"Database query failed: {e}")
        return pd.DataFrame({"Error": [f"Failed to execute query: {e}"]})

# --- Existing Tools (Unchanged) ---
# ... (all other tool functions remain the same) ...
def get_invoice_count(sales_date: str) -> str:
    """Finds the total number of invoices for a given sales date (YYYY-MM-DD)."""
    try:
        count = random.randint(50, 250)
        return f"There were {count} invoices for the sales date {sales_date}."
    except Exception as e:
        return f"An error occurred while fetching invoice count: {e}"

def fetch_invoice_details(sales_date: str) -> list[dict] | str:
    """
    Fetches details for invoices on a specific sales date (YYYY-MM-DD) from an external system.
    Returns a list of dictionaries with invoice data if successful, otherwise an error message.
    """
    data = _call_external_invoice_api(sales_date)
    if data:
        return data
    else:
        return f"Sorry, I was unable to retrieve invoice details for {sales_date} from the external system."

def reconcile_es_system(vendor: str, sales_date: str) -> str:
    """Reconciles the ES system for a specific vendor and sales date (YYYY-MM-DD)."""
    try:
        return f"Reconciliation process for vendor '{vendor}' on {sales_date} has been successfully initiated."
    except Exception as e:
        return f"An error occurred during reconciliation: {e}"

def list_upcoming_overdue_sales_orders() -> str:
    """Gets a list of sales orders that are about to become overdue."""
    return ("Upcoming Overdue Sales Orders:\n"
            "- SO #7890 (Vendor: 'TechCorp', Due in 1 day)\n"
            "- SO #7891 (Vendor: 'Gadgets Inc', Due in 2 days)\n"
            "- SO #7895 (Vendor: 'Global Imports', Due in 3 days)")

def list_upcoming_overdue_invoices() -> str:
    """Gets a list of invoices that are about to become overdue."""
    return ("Upcoming Overdue Invoices:\n"
            "- INV #9901 (Customer: 'Innovate LLC', Due in 2 days)\n"
            "- INV #9905 (Customer: 'Data Systems', Due in 3 days)\n"
            "- INV #9908 (Customer: 'NextGen Solutions', Due in 4 days)")

def _call_external_invoice_api(sales_date: str):
    print(f"Simulating external API call for invoices on {sales_date}...")
    try:
        if random.random() > 0.1:
            return [
                {"Invoice ID": f"INV-{random.randint(1000, 2000)}", "Amount": f"${random.uniform(100, 5000):.2f}", "Status": random.choice(["Paid", "Unpaid", "Overdue"])},
                {"Invoice ID": f"INV-{random.randint(2001, 3000)}", "Amount": f"${random.uniform(100, 5000):.2f}", "Status": random.choice(["Paid", "Unpaid"])},
                {"Invoice ID": f"INV-{random.randint(3001, 4000)}", "Amount": f"${random.uniform(100, 5000):.2f}", "Status": "Paid"},
            ]
        else:
            return None
    except requests.RequestException as e:
        print(f"External API call failed: {e}")
        return None