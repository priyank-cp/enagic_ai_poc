# database.py

import os
import uuid
from datetime import datetime
import pymongo
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from bson.objectid import ObjectId
import streamlit as st

# --- In-Memory Storage Manager (No Database Required) ---
class MemoryManager:
    """
    A manager class that mimics MongoManager but uses st.session_state for storage.
    Chat history is not persisted and will be lost when the session ends.
    """
    def __init__(self):
        # Initialize the in-memory DB if it doesn't exist.
        if "in_memory_db" not in st.session_state:
            st.session_state.in_memory_db = {} # {chat_id: {"messages": [...], "timestamp": ...}}

    def _ensure_db_exists(self):
        """A private helper to ensure robustness in every method."""
        if "in_memory_db" not in st.session_state:
            st.session_state.in_memory_db = {}

    def get_chat_summaries(self):
        self._ensure_db_exists()
        sorted_chats = sorted(
            st.session_state.in_memory_db.items(),
            key=lambda item: item[1]['timestamp'],
            reverse=True
        )
        return [{
            "chat_id": chat_id,
            "title": next((msg['content'] for msg in data.get('messages', []) if msg['role'] == 'user'), "New Chat")
        } for chat_id, data in sorted_chats]

    def get_chat_messages(self, chat_id: str):
        self._ensure_db_exists()
        if not chat_id: return []
        return st.session_state.in_memory_db.get(chat_id, {}).get("messages", [])

    def save_message(self, chat_id: str, role: str, content: any):
        self._ensure_db_exists()
        message_doc = {"role": role, "content": content}
        if not chat_id:
            chat_id = str(uuid.uuid4())
            st.session_state.in_memory_db[chat_id] = {
                "messages": [message_doc],
                "timestamp": datetime.utcnow()
            }
            return chat_id
        else:
            if chat_id in st.session_state.in_memory_db:
                st.session_state.in_memory_db[chat_id]["messages"].append(message_doc)
                st.session_state.in_memory_db[chat_id]["timestamp"] = datetime.utcnow()
            else: # If chat_id somehow got lost, recreate it
                st.session_state.in_memory_db[chat_id] = {
                    "messages": [message_doc],
                    "timestamp": datetime.utcnow()
                }
            return chat_id

    def delete_chat(self, chat_id: str):
        self._ensure_db_exists()
        if chat_id in st.session_state.in_memory_db:
            del st.session_state.in_memory_db[chat_id]

    def clear_all_history(self):
        # This is the correct way to clear the in-memory history
        st.session_state.in_memory_db = {}


# --- MongoDB Storage Manager ---
class MongoManager:
    # ... (No changes needed for MongoManager)
    def __init__(self):
        mongo_uri = os.getenv("MONGO_URI")
        if not mongo_uri:
            raise ValueError("MONGO_URI environment variable not set.")
        self.client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        self.client.admin.command('ping')
        self.db = self.client.get_database("ai_poc_db")
        self.collection = self.db.get_collection("chat_history")

    def get_chat_summaries(self):
        try:
            chats = self.collection.find(
                {"messages.role": "user"},
                {"_id": 1, "messages.content": 1, "timestamp": 1}
            ).sort("timestamp", pymongo.DESCENDING)
            
            return [{
                "chat_id": str(chat["_id"]),
                "title": next((msg['content'] for msg in chat.get('messages', []) if msg['role'] == 'user'), "New Chat")
            } for chat in chats]
        except OperationFailure as e:
            st.error(f"Database error while fetching summaries: {e}")
            return []

    def get_chat_messages(self, chat_id: str):
        if not chat_id: return []
        try:
            session = self.collection.find_one({"_id": ObjectId(chat_id)})
            return session.get("messages", []) if session else []
        except OperationFailure as e:
            st.error(f"Database error while fetching messages: {e}")
            return []

    def save_message(self, chat_id: str, role: str, content: any):
        message_doc = {"role": role, "content": content}
        try:
            if not chat_id:
                result = self.collection.insert_one({
                    "messages": [message_doc], "timestamp": datetime.utcnow()
                })
                return str(result.inserted_id)
            else:
                self.collection.update_one(
                    {"_id": ObjectId(chat_id)},
                    {"$push": {"messages": message_doc}, "$set": {"timestamp": datetime.utcnow()}}
                )
                return chat_id
        except OperationFailure as e:
            st.error(f"Database error while saving message: {e}")
            return chat_id

    def delete_chat(self, chat_id: str):
        try:
            self.collection.delete_one({"_id": ObjectId(chat_id)})
        except OperationFailure as e:
            st.error(f"Database error while deleting chat: {e}")

    def clear_all_history(self):
        try:
            self.collection.delete_many({})
        except OperationFailure as e:
            st.error(f"Database error while clearing history: {e}")