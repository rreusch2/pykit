"""
ParleyApp ChatKit FastAPI Application
Run with: uvicorn app:app --reload --port 8000
"""

import os
import json
from typing import Any, Dict, Optional
from datetime import datetime
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import asyncio
import asyncpg

from chatkit.store import Store
from chatkit.types import ThreadMetadata, ThreadItem, Page, Attachment
from pp_server import ProfessorLockChatKitServer

load_dotenv()

# FastAPI app
app = FastAPI(title="ParleyApp ChatKit Server")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://localhost:19006",
        "https://www.predictive-play.com",
        os.getenv("FRONTEND_URL", "*")
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PostgresStore(Store):
    """PostgreSQL implementation of ChatKit Store"""
    
    def __init__(self):
        self.pool = None
        
    async def init_pool(self):
        """Initialize connection pool"""
        if not self.pool:
            self.pool = await asyncpg.create_pool(
                os.getenv("DATABASE_URL", "postgresql://localhost/chatkit"),
                min_size=1,
                max_size=10
            )
            
            # Create tables if they don't exist
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS chatkit_threads (
                        id TEXT PRIMARY KEY,
                        title TEXT,
                        created_at TIMESTAMP,
                        status JSONB,
                        metadata JSONB
                    )
                """)
                
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS chatkit_thread_items (
                        id TEXT PRIMARY KEY,
                        thread_id TEXT REFERENCES chatkit_threads(id) ON DELETE CASCADE,
                        type TEXT,
                        data JSONB,
                        created_at TIMESTAMP
                    )
                """)
                
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS chatkit_attachments (
                        id TEXT PRIMARY KEY,
                        thread_id TEXT REFERENCES chatkit_threads(id) ON DELETE CASCADE,
                        data JSONB,
                        created_at TIMESTAMP
                    )
                """)
    
    def generate_thread_id(self, context: Any) -> str:
        """Generate unique thread ID"""
        import uuid
        return f"thread_{uuid.uuid4().hex[:12]}"
    
    def generate_item_id(
        self, 
        item_type: str,
        thread: ThreadMetadata,
        context: Any
    ) -> str:
        """Generate unique item ID"""
        import uuid
        return f"{item_type}_{uuid.uuid4().hex[:12]}"
    
    async def load_thread(self, thread_id: str, context: Any) -> ThreadMetadata:
        """Load thread metadata"""
        if not self.pool:
            await self.init_pool()
            
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM chatkit_threads WHERE id = $1",
                thread_id
            )
            
            if row:
                return ThreadMetadata(
                    id=row["id"],
                    title=row["title"],
                    created_at=row["created_at"],
                    status=json.loads(row["status"]) if row["status"] else {"type": "active"},
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {}
                )
            
            # Return new thread if not found
            return ThreadMetadata(
                id=thread_id,
                created_at=datetime.now(),
                status={"type": "active"},
                metadata={}
            )
    
    async def save_thread(self, thread: ThreadMetadata, context: Any) -> None:
        """Save thread metadata"""
        if not self.pool:
            await self.init_pool()
            
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO chatkit_threads (id, title, created_at, status, metadata)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (id) DO UPDATE SET
                    title = EXCLUDED.title,
                    status = EXCLUDED.status,
                    metadata = EXCLUDED.metadata
            """,
            thread.id,
            thread.title,
            thread.created_at,
            json.dumps(thread.status.model_dump()),
            json.dumps(thread.metadata)
        )
    
    async def load_thread_items(
        self,
        thread_id: str,
        after: Optional[str],
        limit: int,
        order: str,
        context: Any
    ) -> Page[ThreadItem]:
        """Load thread items with pagination"""
        if not self.pool:
            await self.init_pool()
            
        async with self.pool.acquire() as conn:
            # Build query
            query = """
                SELECT * FROM chatkit_thread_items 
                WHERE thread_id = $1
            """
            params = [thread_id]
            
            if after:
                query += " AND id > $2"
                params.append(after)
            
            query += f" ORDER BY created_at {order.upper()}"
            query += f" LIMIT {limit + 1}"
            
            rows = await conn.fetch(query, *params)
            
            items = []
            for row in rows[:limit]:
                item_data = json.loads(row["data"])
                # Reconstruct ThreadItem from JSON
                # This is simplified - you'd need proper deserialization
                items.append(ThreadItem(**item_data))
            
            return Page(
                data=items,
                has_more=len(rows) > limit,
                after=rows[limit - 1]["id"] if len(rows) > limit else None
            )
    
    async def add_thread_item(
        self,
        thread_id: str,
        item: ThreadItem,
        context: Any
    ) -> None:
        """Add item to thread"""
        if not self.pool:
            await self.init_pool()
            
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO chatkit_thread_items (id, thread_id, type, data, created_at)
                VALUES ($1, $2, $3, $4, $5)
            """,
            item.id,
            thread_id,
            item.type,
            json.dumps(item.model_dump()),
            item.created_at
        )
    
    async def save_item(
        self,
        thread_id: str,
        item: ThreadItem,
        context: Any
    ) -> None:
        """Update existing item"""
        if not self.pool:
            await self.init_pool()
            
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE chatkit_thread_items 
                SET data = $1
                WHERE id = $2 AND thread_id = $3
            """,
            json.dumps(item.model_dump()),
            item.id,
            thread_id
        )
    
    async def load_item(
        self,
        thread_id: str,
        item_id: str,
        context: Any
    ) -> ThreadItem:
        """Load single item"""
        if not self.pool:
            await self.init_pool()
            
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM chatkit_thread_items 
                WHERE id = $1 AND thread_id = $2
            """,
            item_id,
            thread_id
        )
            
            if row:
                item_data = json.loads(row["data"])
                return ThreadItem(**item_data)
            
            raise ValueError(f"Item {item_id} not found")
    
    async def delete_thread_item(
        self,
        thread_id: str,
        item_id: str,
        context: Any
    ) -> None:
        """Delete thread item"""
        if not self.pool:
            await self.init_pool()
            
        async with self.pool.acquire() as conn:
            await conn.execute("""
                DELETE FROM chatkit_thread_items 
                WHERE id = $1 AND thread_id = $2
            """,
            item_id,
            thread_id
        )
    
    async def load_threads(
        self,
        limit: int,
        after: Optional[str],
        order: str,
        context: Any
    ) -> Page[ThreadMetadata]:
        """Load threads list"""
        if not self.pool:
            await self.init_pool()
            
        async with self.pool.acquire() as conn:
            query = "SELECT * FROM chatkit_threads"
            params = []
            
            if after:
                query += " WHERE id > $1"
                params.append(after)
            
            query += f" ORDER BY created_at {order.upper()}"
            query += f" LIMIT {limit + 1}"
            
            rows = await conn.fetch(query, *params)
            
            threads = []
            for row in rows[:limit]:
                threads.append(ThreadMetadata(
                    id=row["id"],
                    title=row["title"],
                    created_at=row["created_at"],
                    status=json.loads(row["status"]) if row["status"] else {"type": "active"},
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {}
                ))
            
            return Page(
                data=threads,
                has_more=len(rows) > limit,
                after=rows[limit - 1]["id"] if len(rows) > limit else None
            )
    
    async def delete_thread(self, thread_id: str, context: Any) -> None:
        """Delete thread and all its items"""
        if not self.pool:
            await self.init_pool()
            
        async with self.pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM chatkit_threads WHERE id = $1",
                thread_id
            )
    
    async def save_attachment(self, attachment: Attachment, context: Any) -> None:
        """Save attachment metadata"""
        if not self.pool:
            await self.init_pool()
            
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO chatkit_attachments (id, thread_id, data, created_at)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (id) DO UPDATE SET data = EXCLUDED.data
            """,
            attachment.id,
            context.get("thread_id"),
            json.dumps(attachment.model_dump()),
            datetime.now()
        )
    
    async def load_attachment(self, attachment_id: str, context: Any) -> Attachment:
        """Load attachment"""
        if not self.pool:
            await self.init_pool()
            
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM chatkit_attachments WHERE id = $1",
                attachment_id
            )
            
            if row:
                data = json.loads(row["data"])
                return Attachment(**data)
            
            raise ValueError(f"Attachment {attachment_id} not found")
    
    async def delete_attachment(self, attachment_id: str, context: Any) -> None:
        """Delete attachment"""
        if not self.pool:
            await self.init_pool()
            
        async with self.pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM chatkit_attachments WHERE id = $1",
                attachment_id
            )

# Initialize store and server
data_store = PostgresStore()
chatkit_server = ProfessorLockChatKitServer(data_store)

@app.on_event("startup")
async def startup():
    """Initialize database pool on startup"""
    await data_store.init_pool()
    print("✅ ChatKit server started on http://localhost:8000")
    print("📊 Professor Lock is ready to analyze your bets!")

@app.post("/create-session")
async def create_session(request: Request):
    """Create Professor Lock ChatKit session"""
    
    try:
        body = await request.json()
        user_id = body.get("user_id")
        user_email = body.get("user_email", "")
        tier = body.get("tier", "free")
        preferences = body.get("preferences", {})
        
        # Generate session ID and client secret
        import uuid
        session_id = f"prof_lock_{uuid.uuid4().hex[:16]}"
        client_secret = f"cs_{uuid.uuid4().hex[:24]}"
        
        # Store session context
        context = {
            "user_id": user_id,
            "user_email": user_email,
            "session_id": session_id,
            "tier": tier,
            "preferences": preferences,
            "timestamp": datetime.now()
        }
        
        return JSONResponse({
            "session_id": session_id,
            "client_secret": client_secret,
            "status": "active",
            "features": {
                "professor_lock_personality": True,
                "advanced_widgets": True,
                "betting_analysis": True,
                "parlay_builder": True,
                "statmuse_integration": True,
                "live_odds": True
            }
        })
        
    except Exception as e:
        print(f"❌ Error creating session: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.options("/chatkit")
async def chatkit_options():
    """CORS preflight support for ChatKit."""
    return Response(status_code=204)

@app.get("/chatkit")
async def chatkit_get():
    """Health/handshake route to satisfy ChatKit GET checks."""
    return JSONResponse({
        "status": "ok",
        "message": "Use POST for ChatKit events",
        "timestamp": datetime.now().isoformat()
    })

@app.post("/chatkit")
async def chatkit_endpoint(request: Request):
    """Main ChatKit endpoint"""
    
    try:
        # Get request body
        body = await request.body()
        
        # Get context (user info, etc)
        context = {
            "user_id": request.headers.get("X-User-Id"),
            "session_id": request.headers.get("X-Session-Id"),
            "user_email": request.headers.get("X-User-Email"),
            "user_tier": request.headers.get("X-User-Tier", "free"),
            "timestamp": datetime.now()
        }
        
        # Process request
        result = await chatkit_server.process(body, context)
        
        # Return streaming or JSON response
        if hasattr(result, '__aiter__'):  # It's a streaming result
            return StreamingResponse(
                result,
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                }
            )
        else:
            return Response(
                content=result.json,
                media_type="application/json"
            )
            
    except Exception as e:
        print(f"❌ Error processing ChatKit request: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ParleyApp ChatKit Server",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/")
async def root():
    """Root endpoint with info"""
    return {
        "service": "ParleyApp ChatKit Server",
        "description": "Professor Lock AI Sports Betting Assistant",
        "endpoints": {
            "chatkit": "/chatkit",
            "health": "/health"
        },
        "features": [
            "Visual web search with progress widgets",
            "Live odds comparison tables",
            "Interactive parlay builders",
            "StatMuse integration",
            "Trend charts and analytics"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )
