"""
Simple ParleyApp ChatKit Server - Minimal working version
"""

import os
import json
from typing import Any, AsyncIterator
from datetime import datetime
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from agents import Agent
from chatkit.server import ChatKitServer
from chatkit.agents import AgentContext, stream_agent_response, simple_to_agent_input
from chatkit.types import ThreadMetadata, UserMessageItem, ThreadStreamEvent
from chatkit.store import Store
from chatkit.types import Page, ThreadItem, Attachment

load_dotenv()

# Simple in-memory store for testing
class MemoryStore(Store):
    def __init__(self):
        self.threads = {}
        self.thread_items = {}
        self.attachments = {}
    
    def generate_thread_id(self, context):
        import uuid
        return f"thread_{uuid.uuid4().hex[:8]}"
    
    def generate_item_id(self, item_type, thread, context):
        import uuid
        return f"{item_type}_{uuid.uuid4().hex[:8]}"
    
    async def load_thread(self, thread_id, context):
        from chatkit.types import ThreadMetadata, ActiveStatus
        if thread_id in self.threads:
            return self.threads[thread_id]
        # Return new thread
        thread = ThreadMetadata(
            id=thread_id,
            created_at=datetime.now(),
            status=ActiveStatus(),
            metadata={}
        )
        self.threads[thread_id] = thread
        return thread
    
    async def save_thread(self, thread, context):
        self.threads[thread.id] = thread
    
    async def load_thread_items(self, thread_id, after, limit, order, context):
        items = self.thread_items.get(thread_id, [])
        return Page(data=items[:limit], has_more=False, after=None)
    
    async def add_thread_item(self, thread_id, item, context):
        if thread_id not in self.thread_items:
            self.thread_items[thread_id] = []
        self.thread_items[thread_id].append(item)
    
    async def save_item(self, thread_id, item, context):
        pass  # Simple implementation
    
    async def load_item(self, thread_id, item_id, context):
        items = self.thread_items.get(thread_id, [])
        for item in items:
            if item.id == item_id:
                return item
        raise ValueError(f"Item {item_id} not found")
    
    async def delete_thread_item(self, thread_id, item_id, context):
        pass  # Simple implementation
    
    async def load_threads(self, limit, after, order, context):
        threads = list(self.threads.values())[:limit]
        return Page(data=threads, has_more=False, after=None)
    
    async def delete_thread(self, thread_id, context):
        if thread_id in self.threads:
            del self.threads[thread_id]
        if thread_id in self.thread_items:
            del self.thread_items[thread_id]
    
    async def save_attachment(self, attachment, context):
        self.attachments[attachment.id] = attachment
    
    async def load_attachment(self, attachment_id, context):
        return self.attachments.get(attachment_id)
    
    async def delete_attachment(self, attachment_id, context):
        if attachment_id in self.attachments:
            del self.attachments[attachment_id]

# FastAPI app
app = FastAPI(title="ParleyApp ChatKit Server")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Simplified for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SimpleProfessorLockServer(ChatKitServer):
    """Simplified ChatKit server for testing"""
    
    def __init__(self, data_store):
        super().__init__(data_store)
        
        # Simple agent definition
        self.professor_lock_agent = Agent(
            name="Professor Lock",
            instructions="You are Professor Lock, a sharp sports betting analyst. Provide confident betting advice with gambling slang. Keep responses short and witty."
        )
    
    async def respond(
        self,
        thread: ThreadMetadata,
        input_user_message: UserMessageItem | None,
        context: Any
    ) -> AsyncIterator[ThreadStreamEvent]:
        """Simple response handler"""
        
        # Create agent context
        agent_context = AgentContext(
            thread=thread,
            store=self.store,
            request_context=context
        )
        
        # Convert input and run agent
        from agents import Runner
        
        agent_input = await simple_to_agent_input(input_user_message) if input_user_message else []
        
        result = Runner.run_streamed(
            self.professor_lock_agent,
            agent_input,
            context=agent_context
        )
        
        # Stream the response
        async for event in stream_agent_response(agent_context, result):
            yield event

# Initialize with memory store for testing
data_store = MemoryStore()
chatkit_server = SimpleProfessorLockServer(data_store)

@app.post("/chatkit")
async def chatkit_endpoint(request: Request):
    """Main ChatKit endpoint"""
    
    try:
        body = await request.body()
        
        context = {
            "user_id": request.headers.get("X-User-Id", "test-user"),
            "timestamp": datetime.now()
        }
        
        result = await chatkit_server.process(body, context)
        
        # Handle streaming vs non-streaming
        if hasattr(result, '__aiter__'):  # Streaming
            return StreamingResponse(
                result,
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                }
            )
        else:  # Non-streaming
            return Response(
                content=result.json,
                media_type="application/json"
            )
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "service": "Simple ParleyApp ChatKit Server",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Simple ParleyApp ChatKit Server",
        "description": "Testing Professor Lock AI",
        "endpoints": {
            "chatkit": "/chatkit",
            "health": "/health"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
