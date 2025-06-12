# tools.py

import datetime
import random
import requests # To simulate external API calls

def _call_external_invoice_api(sales_date: str):
    """
    A mock function that simulates calling an external API to get invoice data.
    In a real application, this would use 'requests' to call a real endpoint.
    Returns structured data or None on failure.
    """
    print(f"Simulating external API call for invoices on {sales_date}...")
    try:
        # Simulate API call latency
        # requests.get(f"https://api.mycompany.com/invoices?date={sales_date}", timeout=5)
        
        # Mocking a successful response with structured data
        if random.random() > 0.1: # 90% success rate
            return [
                {"Invoice ID": f"INV-{random.randint(1000, 2000)}", "Amount": f"${random.uniform(100, 5000):.2f}", "Status": random.choice(["Paid", "Unpaid", "Overdue"])},
                {"Invoice ID": f"INV-{random.randint(2001, 3000)}", "Amount": f"${random.uniform(100, 5000):.2f}", "Status": random.choice(["Paid", "Unpaid"])},
                {"Invoice ID": f"INV-{random.randint(3001, 4000)}", "Amount": f"${random.uniform(100, 5000):.2f}", "Status": "Paid"},
            ]
        else: # Simulate an API error
            return None
    except requests.RequestException as e:
        print(f"External API call failed: {e}")
        return None


def get_invoice_count(sales_date: str) -> str:
    """Finds the total number of invoices for a given sales date (YYYY-MM-DD). """
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
        # The agent will pass this structured data back to the application
        return data
    else:
        return f"Sorry, I was unable to retrieve invoice details for {sales_date} from the external system."

def reconcile_es_system(vendor: str, sales_date: str) -> str:
    """Reconciles the ES system for a specific vendor and sales date (YYYY-MM-DD). """
    try:
        return f"Reconciliation process for vendor '{vendor}' on {sales_date} has been successfully initiated."
    except Exception as e:
        return f"An error occurred during reconciliation: {e}"

def list_upcoming_overdue_sales_orders() -> str:
    """Gets a list of sales orders that are about to become overdue. """
    return ("Upcoming Overdue Sales Orders:\n"
            "- SO #7890 (Vendor: 'TechCorp', Due in 1 day)\n"
            "- SO #7891 (Vendor: 'Gadgets Inc', Due in 2 days)\n"
            "- SO #7895 (Vendor: 'Global Imports', Due in 3 days)")

def list_upcoming_overdue_invoices() -> str:
    """Gets a list of invoices that are about to become overdue. """
    return ("Upcoming Overdue Invoices:\n"
            "- INV #9901 (Customer: 'Innovate LLC', Due in 2 days)\n"
            "- INV #9905 (Customer: 'Data Systems', Due in 3 days)\n"
            "- INV #9908 (Customer: 'NextGen Solutions', Due in 4 days)")