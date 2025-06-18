# tools/daily_ops.py

import re
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
from database import MongoManager

def recover_sap_commission(order_id: str, reason: str) -> dict:
    """Recovers commission from SAP for a specific cancelled order ID and reason."""
    print(f"Executing recover_sap_commission for order: {order_id}")
    return {"status": "success", "message": f"Commission for cancelled order {order_id} is being recovered from SAP."}


def reconcile_sap_vs_es_sales(start_date: str, end_date: str) -> dict:
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Initialize MongoDB connection
        mongo_manager = MongoManager()
        db = mongo_manager.client.get_database("ai_poc_db")
        
        # Fetch records from both collections
        es_records = list(db.es.find({
            "Sale date": {
                "$gte": start_dt,
                "$lte": end_dt
            }
        }))
        print(f"ES Records: {len(es_records)}")
        
        sap_records = list(db.sap.find({
            "Sale date": {
                "$gte": start_dt,
                "$lte": end_dt
            }
        }))
        print(f"SAP Records: {len(sap_records)}")
        
        # Initialize result arrays
        unmatched_amounts = []
        payment_block_removal = []

        def get_numeric_value(value):
            """Helper function to handle both Int64 and $numberLong formats"""
            if isinstance(value, dict) and "$numberLong" in value:
                return int(value["$numberLong"])
            return int(value)

        def get_slip_value(record):
            """Helper function to get Slip value"""
            if isinstance(record.get("Slip"), dict) and "$numberLong" in record["Slip"]:
                return record["Slip"]["$numberLong"]
            return str(record.get("Slip", ""))

        def get_buyer_id_value(record):
            """Helper function to get Buyer ID value"""
            if isinstance(record.get("Buyer id"), dict) and "$numberLong" in record["Buyer id"]:
                return record["Buyer id"]["$numberLong"]
            return str(record.get("Buyer id", ""))
        
        # Process ES records
        for es_record in es_records:
            # Find matching SAP record
            matching_sap = next(
                (sap for sap in sap_records 
                 if get_slip_value(sap) == get_slip_value(es_record)
                 and sap["Distribtutor id"] == es_record["Distribtutor id"]
                 and get_buyer_id_value(sap) == get_buyer_id_value(es_record)),
                None
            )
            
            if matching_sap:
                # Check if amounts match
                es_amount = get_numeric_value(es_record["Amount"])
                sap_amount = get_numeric_value(matching_sap["Amount"])
                
                if es_amount != sap_amount:
                    unmatched_amounts.append({
                        "Slip": get_slip_value(es_record),
                        "Distributor ID": es_record["Distribtutor id"],
                        "Buyer ID": get_buyer_id_value(es_record),
                        "Sale date": es_record["Sale date"],
                        "ES Amount": es_amount,
                        "SAP Amount": sap_amount,
                        "Distributor Name": es_record.get("Distributor name", "")
                    })
                # Check if payment document number exists
                elif not matching_sap.get("Payment document number"):
                    payment_block_removal.append({
                        "Slip": get_slip_value(es_record),
                        "Distributor ID": es_record["Distribtutor id"],
                        "Buyer ID": get_buyer_id_value(es_record),
                        "Sale date": es_record["Sale date"],
                        "Amount": es_amount,
                        "Distributor Name": es_record.get("Distributor name", "")
                    })
        
        return {
            "status": "success",
            "message": f"Reconciliation completed for period {start_date} to {end_date}",
            "details": {
                "start_date": start_date,
                "end_date": end_date,
                "total_unmatched": len(unmatched_amounts),
                "total_payment_block": len(payment_block_removal),
                "unmatched_amounts": unmatched_amounts,
                "payment_block_removal": payment_block_removal
            }
        }
        
    except ValueError as e:
        return {
            "status": "error",
            "message": "Invalid date format. Please use YYYY-MM-DD format.",
            "details": None
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"An error occurred during reconciliation: {str(e)}",
            "details": None
        }

def remove_payment_block(records: list) -> dict:
    """Function to handle payment block removal via SAP API"""
    # TODO: Implement actual SAP API call
    print(f"Executing remove_payment_block for {len(records)} records")
    return {
        "status": "success",
        "message": f"Successfully removed payment block for {len(records)} records from SAP",
        "details": {
            "processed_records": len(records)
        }
    }

def check_recovery_status() -> dict:
    """Checks if today's order cancellations are fully recovered in payment."""
    print("Executing check_recovery_status for today.")
    return {"status": "success", "message": "All of today's cancelled orders have been fully recovered in the payment systems."}

def process_sales_payment(sales_date: str) -> dict:
    """Makes payment for a specific sales date."""
    print(f"Executing process_sales_payment for date: {sales_date}")
    return {"status": "success", "message": f"Payments for sales on {sales_date} are being processed."}

def issue_payment(payment_method: str, recipient: str, amount: float) -> dict:
    """Transfers payment via bank or prints a check for a recipient and amount."""
    print(f"Executing issue_payment for {recipient} via {payment_method}")
    return {"status": "success", "message": f"A payment of {amount} has been issued to {recipient} via {payment_method}."}

def update_es_payment_result(file_name: str) -> dict:
    """Updates payment results in the ES system from a given file."""
    print(f"Executing update_es_payment_result with file: {file_name}")
    return {"status": "success", "message": f"Payment results from file '{file_name}' are being updated in the ES system."}

def recover_canceled_orders() -> dict:
    """Recovers all cancelled orders from the ES system."""
    print("Executing recover_canceled_orders.")
    return {"status": "success", "message": "Recovery process for all cancelled orders from ES has been started."}