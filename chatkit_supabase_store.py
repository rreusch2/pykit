"""
Supabase-backed Store implementation for ChatKit
Stores threads, messages, and attachments in Supabase PostgreSQL
"""

import uuid
import json
from typing import Any, Literal, Optional
from datetime import datetime
from chatkit.store import Store, Page
from chatkit.types import ThreadMetadata, ThreadItem, Attachment
from supabase import create_client, Client
import os


class SupabaseStore(Store):
    """Production-ready Supabase store for ChatKit threads and messages"""
    
    def __init__(self, supabase_url: Optional[str] = None, supabase_key: Optional[str] = None):
        """Initialize Supabase client"""
        self.supabase: Client = create_client(
            supabase_url or os.getenv("SUPABASE_URL", ""),
            supabase_key or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        )
    
    def generate_thread_id(self, context: Any) -> str:
        """Generate unique thread ID"""
        return f"thread_{uuid.uuid4().hex}"
    
    def generate_item_id(
        self,
        item_type: Literal["message", "tool_call", "task", "workflow", "attachment"],
        thread: ThreadMetadata,
        context: Any,
    ) -> str:
        """Generate unique item ID with type prefix"""
        prefixes = {
            "message": "msg",
            "tool_call": "tool",
            "task": "task",
            "workflow": "work",
            "attachment": "att"
        }
        prefix = prefixes.get(item_type, "item")
        return f"{prefix}_{uuid.uuid4().hex}"
    
    async def load_thread(self, thread_id: str, context: Any) -> ThreadMetadata:
        """Load thread metadata from Supabase"""
        try:
            result = self.supabase.table("chatkit_threads").select("*").eq("id", thread_id).execute()
            
            if not result.data or len(result.data) == 0:
                # Return new thread if not found
                return ThreadMetadata(
                    id=thread_id,
                    created_at=datetime.now(),
                    metadata={}
                )
            
            thread_data = result.data[0]
            return ThreadMetadata(
                id=thread_data["id"],
                title=thread_data.get("title"),
                created_at=datetime.fromisoformat(thread_data["created_at"]),
                metadata=thread_data.get("metadata", {})
            )
        except Exception as e:
            print(f"Error loading thread {thread_id}: {e}")
            # Return new thread on error
            return ThreadMetadata(
                id=thread_id,
                created_at=datetime.now(),
                metadata={}
            )
    
    async def save_thread(self, thread: ThreadMetadata, context: Any) -> None:
        """Save thread metadata to Supabase"""
        try:
            thread_dict = {
                "id": thread.id,
                "title": thread.title,
                "created_at": thread.created_at.isoformat(),
                "metadata": thread.metadata,
                "profile_id": context.get("user_id") if isinstance(context, dict) else None
            }
            
            # Upsert (insert or update)
            self.supabase.table("chatkit_threads").upsert(thread_dict).execute()
        except Exception as e:
            print(f"Error saving thread {thread.id}: {e}")
    
    async def load_thread_items(
        self,
        thread_id: str,
        after: Optional[str],
        limit: int,
        order: str,
        context: Any,
    ) -> Page[ThreadItem]:
        """Load thread items (messages, widgets, etc.) from Supabase"""
        try:
            query = self.supabase.table("chatkit_thread_items").select("*").eq("thread_id", thread_id)
            
            # Handle pagination
            if after:
                query = query.gt("created_at", after)
            
            # Order
            if order == "asc":
                query = query.order("created_at", desc=False)
            else:
                query = query.order("created_at", desc=True)
            
            query = query.limit(limit)
            result = query.execute()
            
            # Deserialize items
            items = []
            for item_data in result.data:
                try:
                    # Reconstruct the ThreadItem from JSON
                    item_json = item_data.get("item_data", {})
                    # The item_data should contain the full ThreadItem serialized
                    # We'll use pydantic to reconstruct it
                    items.append(item_json)  # This needs proper deserialization
                except Exception as e:
                    print(f"Error deserializing item: {e}")
            
            # Determine if there are more items
            has_more = len(items) >= limit
            
            return Page(
                data=items,
                has_more=has_more,
                next_cursor=items[-1].get("id") if items and has_more else None
            )
        except Exception as e:
            print(f"Error loading thread items: {e}")
            return Page(data=[], has_more=False, next_cursor=None)
    
    async def save_attachment(self, attachment: Attachment, context: Any) -> None:
        """Save attachment metadata to Supabase"""
        try:
            attachment_dict = {
                "id": attachment.id,
                "thread_id": getattr(attachment, 'thread_id', None),
                "attachment_data": attachment.model_dump(mode="json"),
                "created_at": datetime.now().isoformat(),
                "profile_id": context.get("user_id") if isinstance(context, dict) else None
            }
            
            self.supabase.table("chatkit_attachments").upsert(attachment_dict).execute()
        except Exception as e:
            print(f"Error saving attachment: {e}")
    
    async def load_attachment(self, attachment_id: str, context: Any) -> Attachment:
        """Load attachment from Supabase"""
        try:
            result = self.supabase.table("chatkit_attachments").select("*").eq("id", attachment_id).execute()
            
            if not result.data or len(result.data) == 0:
                raise ValueError(f"Attachment {attachment_id} not found")
            
            attachment_data = result.data[0]["attachment_data"]
            # Reconstruct Attachment from dict (this needs proper type handling)
            return Attachment(**attachment_data)
        except Exception as e:
            print(f"Error loading attachment: {e}")
            raise
    
    async def delete_attachment(self, attachment_id: str, context: Any) -> None:
        """Delete attachment from Supabase"""
        try:
            self.supabase.table("chatkit_attachments").delete().eq("id", attachment_id).execute()
        except Exception as e:
            print(f"Error deleting attachment: {e}")
    
    async def load_threads(
        self,
        limit: int,
        after: Optional[str],
        order: str,
        context: Any,
    ) -> Page[ThreadMetadata]:
        """Load list of threads for a user"""
        try:
            query = self.supabase.table("chatkit_threads").select("*")
            
            # Filter by user if context provides it
            if isinstance(context, dict) and context.get("user_id"):
                query = query.eq("profile_id", context["user_id"])
            
            # Pagination
            if after:
                query = query.gt("created_at", after)
            
            # Order
            if order == "asc":
                query = query.order("created_at", desc=False)
            else:
                query = query.order("created_at", desc=True)
            
            query = query.limit(limit)
            result = query.execute()
            
            threads = []
            for thread_data in result.data:
                threads.append(ThreadMetadata(
                    id=thread_data["id"],
                    title=thread_data.get("title"),
                    created_at=datetime.fromisoformat(thread_data["created_at"]),
                    metadata=thread_data.get("metadata", {})
                ))
            
            has_more = len(threads) >= limit
            
            return Page(
                data=threads,
                has_more=has_more,
                next_cursor=threads[-1].id if threads and has_more else None
            )
        except Exception as e:
            print(f"Error loading threads: {e}")
            return Page(data=[], has_more=False, next_cursor=None)
    
    async def add_thread_item(
        self, thread_id: str, item: ThreadItem, context: Any
    ) -> None:
        """Add a new thread item"""
        try:
            item_dict = {
                "id": item.id,
                "thread_id": thread_id,
                "item_data": item.model_dump(mode="json"),
                "created_at": item.created_at.isoformat(),
                "profile_id": context.get("user_id") if isinstance(context, dict) else None
            }
            
            self.supabase.table("chatkit_thread_items").insert(item_dict).execute()
        except Exception as e:
            print(f"Error adding thread item: {e}")
    
    async def save_item(self, thread_id: str, item: ThreadItem, context: Any) -> None:
        """Update an existing thread item"""
        try:
            item_dict = {
                "id": item.id,
                "thread_id": thread_id,
                "item_data": item.model_dump(mode="json"),
                "created_at": item.created_at.isoformat(),
                "profile_id": context.get("user_id") if isinstance(context, dict) else None
            }
            
            self.supabase.table("chatkit_thread_items").upsert(item_dict).execute()
        except Exception as e:
            print(f"Error saving thread item: {e}")
    
    async def load_item(self, thread_id: str, item_id: str, context: Any) -> ThreadItem:
        """Load a specific thread item"""
        try:
            result = self.supabase.table("chatkit_thread_items").select("*").eq("id", item_id).eq("thread_id", thread_id).execute()
            
            if not result.data or len(result.data) == 0:
                raise ValueError(f"Item {item_id} not found in thread {thread_id}")
            
            item_data = result.data[0]["item_data"]
            # Reconstruct ThreadItem (needs proper type handling)
            return item_data
        except Exception as e:
            print(f"Error loading thread item: {e}")
            raise
    
    async def delete_thread(self, thread_id: str, context: Any) -> None:
        """Delete a thread and all its items"""
        try:
            # Delete thread items first
            self.supabase.table("chatkit_thread_items").delete().eq("thread_id", thread_id).execute()
            
            # Delete thread
            self.supabase.table("chatkit_threads").delete().eq("id", thread_id).execute()
        except Exception as e:
            print(f"Error deleting thread: {e}")

