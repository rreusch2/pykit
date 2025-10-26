# Professor Lock PyKit - Railway Deployment Guide

## Critical Environment Variables for Railway

Make sure ALL of these are set in your Railway environment:

### Required Variables

**Copy these from your local `.env` file** - DO NOT commit actual secrets to Git!

```bash
# OpenAI
OPENAI_API_KEY=<your-openai-api-key>

# Supabase (CRITICAL - Need service role key)
SUPABASE_URL=<your-supabase-url>
NEXT_PUBLIC_SUPABASE_URL=<your-supabase-url>
SUPABASE_ANON_KEY=<your-supabase-anon-key>
SUPABASE_SERVICE_ROLE_KEY=<your-supabase-service-role-key>

# Backend URL (for tools to call your backend)
BACKEND_URL=<your-backend-url>
NEXT_PUBLIC_BACKEND_URL=<your-backend-url>

# Google Search API (for web search tool)
GOOGLE_SEARCH_API_KEY=<your-google-api-key>
GOOGLE_SEARCH_ENGINE_ID=<your-google-cx-id>

# Server Config
FRONTEND_URL=https://www.predictive-play.com
```

**To set in Railway Dashboard:**
1. Go to your Railway project
2. Click "Variables" tab
3. Add each variable above with your actual values from `pykit/.env`
4. Redeploy

## How to Deploy

### Option 1: Push to Git (Recommended)
```bash
# From pykit directory
git add .
git commit -m "Fix: Add missing env vars and database tools"
git push origin main
```

Railway will auto-deploy from your repo.

### Option 2: Railway CLI
```bash
# Install Railway CLI if needed
npm i -g @railway/cli

# Login
railway login

# Link to your project
railway link

# Deploy
railway up
```

## Verify Deployment

After deployment, check:

1. **Health endpoint**: `https://pykit-production.up.railway.app/health`
2. **ChatKit endpoint**: `https://pykit-production.up.railway.app/chatkit` (should return status ok)
3. **Logs**: Check Railway logs for startup messages

Expected startup logs:
```
🎯 Predictive Play ChatKit Server Starting...
✅ Professor Lock Agent: Active
📊 Supabase Store: Connected
🔧 Widgets: Enabled (Search, Odds, Parlay, Trends)
🔥 Tools: Enabled (Web Search, StatMuse, Betting Analysis)
💰 Ready to lock in those winning bets! 🎲
```

## Testing the Fix

After deployment, test in the web app:

1. Go to `/professor-lock`
2. Try: "NBA Props"
3. Should now call `get_nba_props()` tool and return real picks from database
4. Try: "/parlay" 
5. Should work with picks from database

## What Was Fixed

1. ✅ Added `SUPABASE_SERVICE_ROLE_KEY` - needed to query database
2. ✅ Added `NEXT_PUBLIC_BACKEND_URL` - tools need this
3. ✅ Added Google Search API keys - for web search
4. ✅ Created `get_nba_props()` tool - fetches from ai_predictions table
5. ✅ Created `get_todays_picks()` tool - fetches any sport picks
6. ✅ Improved agent instructions - tells it to USE database tools
7. ✅ Added error handling - tools won't crash, will fallback gracefully
8. ✅ Simplified tool outputs - removed widget complexity that was failing

## Common Issues

### "No picks available"
- Check if ai_predictions table has data for today
- Run your prediction generation scripts

### Tools timing out
- Check Railway logs for actual errors
- Tools have 30s timeout, might need adjustment

### Agent not calling tools
- Check OpenAI API key is valid
- Verify agent model is gpt-4o (has function calling)
- Check Railway logs for tool call attempts
