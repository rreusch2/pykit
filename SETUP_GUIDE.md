# ParleyApp ChatKit Python Server Setup Guide

## 🚀 Overview

This is your advanced ChatKit implementation with Professor Lock - a fully visual, widget-powered sports betting assistant. It runs as a separate Python service alongside your existing Node.js backend.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Frontend Apps                        │
│  (React Native Mobile / Next.js Web / Agent Builder UI)  │
└────────────┬────────────────────────┬───────────────────┘
             │                        │
             ▼                        ▼
┌──────────────────────┐  ┌─────────────────────────────┐
│  Node.js Backend     │  │  Python ChatKit Server      │
│  (Port 3000)         │  │  (Port 8000)                │
│  - Existing APIs     │  │  - Professor Lock Agent     │
│  - Auth/Users        │  │  - Visual Widgets           │
│  - Sports Data       │  │  - Search Progress          │
│  - Odds Integration  │  │  - Interactive Parlays      │
└──────────────────────┘  └─────────────────────────────┘
             │                        │
             └────────────┬───────────┘
                         ▼
              ┌───────────────────┐
              │    PostgreSQL      │
              │  Supabase/Local    │
              └───────────────────┘
```

## 🛠️ Local Development Setup

### 1. Install Dependencies

```bash
cd /home/reid/Desktop/parleyapp/chatkit-python

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install the chatkit package in development mode
pip install -e .
```

### 2. Configure Environment

```bash
cp .env.example .env

# Edit .env with your actual values:
# - DATABASE_URL: Your PostgreSQL connection string
# - OPENAI_API_KEY: Your OpenAI API key for GPT-4
# - BACKEND_URL: Your Node.js backend URL (http://localhost:3000)
# - SUPABASE_URL & SUPABASE_ANON_KEY: From your Supabase project
```

### 3. Set Up Database

The server will automatically create the required tables on first run:
- `chatkit_threads` - Stores chat threads
- `chatkit_thread_items` - Stores messages and widgets
- `chatkit_attachments` - Stores file attachments

```bash
# If using local PostgreSQL
createdb chatkit

# If using Supabase, tables will be created in your existing database
```

### 4. Run the Server

```bash
# Development mode with hot reload
uvicorn app:app --reload --port 8000

# Or use the Python script directly
python app.py
```

The server will be available at:
- ChatKit Endpoint: `http://localhost:8000/chatkit`
- Health Check: `http://localhost:8000/health`

## 🚀 Railway Deployment

### 1. Push to GitHub

```bash
git add .
git commit -m "Add ChatKit Python server"
git push origin main
```

### 2. Deploy on Railway

1. Go to [Railway](https://railway.app)
2. Create new project → Deploy from GitHub repo
3. Select your repository
4. Railway will detect the Dockerfile automatically

### 3. Add Environment Variables

In Railway dashboard, add these environment variables:

```
DATABASE_URL=${{Postgres.DATABASE_URL}}  # If using Railway PostgreSQL
OPENAI_API_KEY=sk-...your-key...
BACKEND_URL=https://your-node-backend.railway.app
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
PORT=8000
```

### 4. Add PostgreSQL (Optional)

If you want a dedicated database for ChatKit:

1. Add PostgreSQL service in Railway
2. It will automatically set DATABASE_URL

## 🎮 Features & Widgets

### Visual Search Progress
```python
# When searching, users see live progress
🔍 Web Search
Searching: "MLB injury report today"
├── ✅ Found result from ESPN
├── ✅ Found result from MLB.com
└── ✅ Found result from Rotoworld
```

### Interactive Odds Board
```python
📊 Live Odds Board
┌─────────────────────────────────────┐
│ Yankees @ Red Sox                  │
│ Spread: NYY -1.5 (+105)            │
│ O/U: 8.5 (-110)                    │
│ ML: NYY -140 / BOS +120            │
└─────────────────────────────────────┘
```

### Parlay Builder
```python
🎯 Parlay Builder (3-Leg)
1. Yankees ML @ -140
2. Dodgers -1.5 @ +105  
3. Under 8.5 (SF/SD) @ -110

Parlay Odds: +485
Stake: $100
To Win: $485
Total Payout: $585
[🔒 Lock It In]
```

## 🔧 Integration with Frontend

### React Native App
```typescript
// In your chat component
const response = await fetch('http://localhost:8000/chatkit', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-User-Id': userId,
  },
  body: JSON.stringify({
    type: 'threads.add_user_message',
    params: {
      thread_id: threadId,
      input: {
        content: [{ type: 'input_text', text: message }],
        attachments: [],
        inference_options: {}
      }
    }
  })
});

// Handle SSE streaming
const reader = response.body.getReader();
// ... process stream
```

### Agent Builder Integration
```python
# Use the /chatkit endpoint directly
workflow_backend = "http://localhost:8000/chatkit"
```

## 📊 Widget Customization

### Creating Custom Widgets

```python
# In parleyapp_widgets.py
def create_custom_widget(data):
    return Card(
        theme="dark",
        children=[
            Title(value="Your Title"),
            # Add any widget components
            Chart(...),
            ListView(...),
            Button(...)
        ]
    )
```

### Available Widget Components
- `Card` - Container with status, actions
- `Text`, `Title`, `Markdown` - Text display
- `Badge`, `Icon` - Status indicators  
- `ListView`, `ListViewItem` - Lists
- `Chart`, `Series` - Data visualization
- `Button`, `Form`, `Input` - Interactions
- `Row`, `Col`, `Box` - Layout
- `Divider`, `Spacer` - Spacing

## 🔍 Testing

### Test the ChatKit endpoint:

```bash
curl -X POST http://localhost:8000/chatkit \
  -H "Content-Type: application/json" \
  -d '{
    "type": "threads.create",
    "params": {
      "input": {
        "content": [{"type": "input_text", "text": "Show me MLB odds"}],
        "attachments": [],
        "inference_options": {}
      }
    }
  }'
```

## 🐛 Debugging

### Check logs:
```bash
# Local
tail -f chatkit.log

# Railway
railway logs
```

### Common Issues:

1. **Database Connection Error**
   - Check DATABASE_URL is correct
   - Ensure PostgreSQL is running
   - Check network connectivity

2. **OpenAI API Error**
   - Verify OPENAI_API_KEY is set
   - Check API quota/billing

3. **Widget Not Displaying**
   - Ensure widget IDs are unique
   - Check widget structure matches schema

## 📚 Resources

- [ChatKit Python Docs](https://openai.github.io/chatkit-python/)
- [Agent Builder](https://platform.openai.com/agents)
- [Widget Reference](https://openai.github.io/chatkit-python/widgets)

## 🎯 What's Next?

1. **Connect to Agent Builder**
   - Create workflow in Agent Builder
   - Get workflow ID
   - Update server configuration

2. **Enhance Widgets**
   - Add more sports (NFL, UFC)
   - Create bet tracking widgets
   - Add performance analytics

3. **Scale Up**
   - Add Redis caching
   - Implement rate limiting
   - Add monitoring/analytics

## Need Help?

The server is designed to work seamlessly with your existing:
- Node.js backend (port 3000)
- StatMuse API (port 5001)  
- Supabase database
- Frontend apps

Everything runs in parallel - this ChatKit server enhances but doesn't replace your current setup!
