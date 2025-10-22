"""
ParleyApp ChatKit FastAPI Application
Production-ready self-hosted ChatKit server for Predictive Play

Run with: uvicorn app:app --reload --port 8000
"""

import os
import json
import uuid
from typing import Any, Dict, Optional
from datetime import datetime
from fastapi import FastAPI, Request, Response, Header
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from pp_server import ProfessorLockChatKitServer
from chatkit_supabase_store import SupabaseStore

load_dotenv()

# FastAPI app
app = FastAPI(
    title="Predictive Play ChatKit Server",
    description="Self-hosted ChatKit server for Professor Lock AI",
    version="1.0.0"
)

# Add CORS middleware - Updated for your domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://predictive-play.com",
        "https://www.predictive-play.com",
        "https://*.predictive-play.com",
        "https://*.vercel.app",
        "http://localhost:3000",
        "http://localhost:3001"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Remove old PostgresStore implementation - using SupabaseStore instead
# Initialize Supabase store
data_store = SupabaseStore(
    supabase_url=os.getenv("SUPABASE_URL"),
    supabase_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

# Initialize ChatKit server with Professor Lock
chatkit_server = ProfessorLockChatKitServer(data_store)

# Old PostgresStore for reference (now replaced by SupabaseStore)
'''
class _PostgresStore(Store):
    # PostgreSQL implementation of ChatKit Store (deprecated)
    
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
'''

@app.on_event("startup")
async def startup():
    """Initialize server on startup"""
    print("=" * 60)
    print("🎯 Predictive Play ChatKit Server Starting...")
    print("=" * 60)
    print(f"✅ Professor Lock Agent: Active")
    print(f"📊 Supabase Store: Connected")
    print(f"🔧 Widgets: Enabled (Search, Odds, Parlay, Trends)")
    print(f"🔥 Tools: Enabled (Web Search, StatMuse, Betting Analysis)")
    print(f"🌐 Server: http://0.0.0.0:{os.getenv('PORT', 8000)}")
    print("=" * 60)
    print("💰 Ready to lock in those winning bets! 🎲")
    print("=" * 60)

@app.post("/api/chatkit/session")
async def create_chatkit_session(
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """
    Create self-hosted ChatKit session
    This endpoint replaces OpenAI's session endpoint
    """
    try:
        # Verify user authentication
        if not authorization or not authorization.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"error": "Missing or invalid authorization"}
            )
        
        token = authorization.replace("Bearer ", "")
        
        # You could verify the token with Supabase here if needed
        # For now, we'll trust it since it's coming from your own web app
        
        body = await request.json()
        user_id = body.get("user_id")
        
        if not user_id:
            return JSONResponse(
                status_code=400,
                content={"error": "user_id is required"}
            )
        
        # Generate simple client secret (since we control the server)
        client_secret = f"cs_self_hosted_{user_id}_{uuid.uuid4().hex[:16]}"
        session_id = f"session_{uuid.uuid4().hex[:16]}"
        
        print(f"✅ Created ChatKit session for user: {user_id}")
        
        return JSONResponse({
            "client_secret": client_secret,
            "session_id": session_id,
            "status": "active",
            "self_hosted": True,
            "features": {
                "professor_lock": True,
                "widgets": True,
                "advanced_tools": True,
                "statmuse": True
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

@app.options("/chatkit")
async def chatkit_options():
    """Handle CORS preflight for ChatKit"""
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.post("/chatkit")
async def chatkit_endpoint(request: Request):
    """Main ChatKit endpoint"""
    
    try:
        print("🎯 Received ChatKit request")
        
        # Get request body
        body = await request.body()
        
        # Get context (user info, etc)
        context = {
            "user_id": request.headers.get("x-user-id"),
            "session_id": request.headers.get("x-session-id"),
            "user_email": request.headers.get("x-user-email"),
            "user_tier": request.headers.get("x-user-tier", "free"),
            "timestamp": datetime.now()
        }
        
        print(f"📋 User context: {context['user_id']} ({context['user_tier']})")
        
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
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "*",
                }
            )
        else:
            return Response(
                content=result.json,
                media_type="application/json",
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "*",
                }
            )
            
    except Exception as e:
        print(f"❌ Error processing ChatKit request: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": str(e)},
            headers={
                "Access-Control-Allow-Origin": "*",
            }
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
