# 🚀 Deployment Guide - Self-Hosted ChatKit for Predictive Play

This guide covers deploying your self-hosted Professor Lock ChatKit server.

## 📋 Prerequisites

- Railway account (or any Python hosting platform)
- Supabase project with database access
- OpenAI API key
- Your Predictive Play web app on Vercel

---

## 1️⃣ Database Setup (Supabase)

### Create the ChatKit Tables

1. Open your Supabase SQL Editor
2. Run the schema from `chatkit_supabase_schema.sql`:

```bash
# Copy the SQL and run it in Supabase SQL Editor
cat chatkit_supabase_schema.sql
```

This creates:
- `chatkit_threads` - Stores conversation threads
- `chatkit_thread_items` - Stores messages, widgets, tool calls
- `chatkit_attachments` - Stores file attachments
- Indexes for performance
- Row Level Security policies

### Get Your Credentials

From Supabase Project Settings > API:
- `SUPABASE_URL` - Your project URL
- `SUPABASE_SERVICE_ROLE_KEY` - Service role key (keep secret!)

---

## 2️⃣ Deploy to Railway

### Option A: Using Railway CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Navigate to pykit directory
cd pykit

# Initialize new project
railway init

# Add environment variables
railway variables set OPENAI_API_KEY=sk-proj-...
railway variables set SUPABASE_URL=https://...
railway variables set SUPABASE_SERVICE_ROLE_KEY=...
railway variables set PORT=8000

# Deploy
railway up
```

### Option B: Using Railway Dashboard

1. Go to [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your `parleyapp` repository
4. Set **Root Directory**: `pykit`
5. Railway will auto-detect `requirements.txt` and `app.py`

### Configure Start Command

In Railway Settings → Deploy:
```bash
uvicorn app:app --host 0.0.0.0 --port $PORT
```

### Set Environment Variables

In Railway Settings → Variables:
```env
OPENAI_API_KEY=sk-proj-your-key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-key
PORT=8000
ENVIRONMENT=production
ALLOWED_ORIGINS=https://predictive-play.com,https://www.predictive-play.com
```

### Get Your Deployment URL

After deployment, Railway provides a URL like:
```
https://pykit-production.up.railway.app
```

---

## 3️⃣ Configure Web App (Vercel)

### Add Environment Variable

In Vercel Project Settings → Environment Variables:

```env
NEXT_PUBLIC_CHATKIT_SERVER_URL=https://pykit-production.up.railway.app
```

### Redeploy Web App

```bash
cd pplayweb
git add .
git commit -m "Connect to self-hosted ChatKit server"
git push
```

Vercel will auto-deploy with the new environment variable.

---

## 4️⃣ Verify Deployment

### Test the Health Endpoint

```bash
curl https://pykit-production.up.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "ParleyApp ChatKit Server",
  "version": "1.0.0"
}
```

### Test the ChatKit Endpoint

```bash
curl https://pykit-production.up.railway.app/chatkit
```

Expected response:
```json
{
  "status": "ok",
  "message": "Use POST for ChatKit events"
}
```

### Test Session Creation

```bash
curl -X POST https://pykit-production.up.railway.app/api/chatkit/session \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-supabase-token" \
  -d '{"user_id": "test-user-id"}'
```

---

## 5️⃣ Monitoring & Logs

### Railway Logs

View real-time logs in Railway Dashboard or via CLI:
```bash
railway logs
```

Look for:
- `✅ Professor Lock Agent: Active`
- `📊 Supabase Store: Connected`
- Incoming ChatKit requests
- Agent tool calls
- Widget generation

### Common Log Patterns

**Successful Request:**
```
✅ Created ChatKit session for user: abc123
📡 ChatKit request to: /chatkit
```

**Error:**
```
❌ Error processing ChatKit request: ...
```

---

## 6️⃣ Testing the Full Flow

### From Your Web App

1. Visit `https://predictive-play.com/professor-lock`
2. Log in with your account
3. You should see "Self-Hosted" badge (green)
4. Try these prompts:
   - "Show me odds for tonight's games"
   - "Build me a 3-leg parlay"
   - "What's LeBron averaging this season?"

### Expected Behavior

✅ **Search Widget**: Shows live search progress with updating results
✅ **Odds Widget**: Displays odds comparison table
✅ **Parlay Widget**: Interactive parlay builder with odds calculator
✅ **StatMuse Widget**: Shows StatMuse query results in card format

---

## 🔧 Troubleshooting

### "Failed to connect to Professor Lock"

**Check:**
1. Railway service is running
2. `NEXT_PUBLIC_CHATKIT_SERVER_URL` is set in Vercel
3. CORS origins include your domain
4. Supabase credentials are correct

**Fix:**
```bash
# Check Railway status
railway status

# View logs
railway logs --tail

# Verify env vars
railway variables
```

### "Session creation failed"

**Check:**
1. `OPENAI_API_KEY` is valid
2. `SUPABASE_SERVICE_ROLE_KEY` is correct
3. User is authenticated in web app

### Widgets not showing

**Check:**
1. Tools are properly registered on agent
2. `pp_widgets.py` and `pp_tools.py` are imported
3. Agent is calling tools successfully (check logs)

---

## 🎯 Production Checklist

Before going live:

- [ ] Database schema deployed to Supabase
- [ ] Railway service deployed and healthy
- [ ] Environment variables set in Railway
- [ ] `NEXT_PUBLIC_CHATKIT_SERVER_URL` set in Vercel
- [ ] CORS configured for your domain
- [ ] Test all widget types (search, odds, parlay, statmuse)
- [ ] Test with real user account
- [ ] Monitor logs for errors
- [ ] Set up Railway alerts (optional)

---

## 🔄 Updates & Rollbacks

### Deploying Updates

```bash
cd pykit

# Make changes to code
git add .
git commit -m "Update Professor Lock tools"
git push

# Railway auto-deploys from GitHub
# Or manually: railway up
```

### Rollback

In Railway Dashboard → Deployments → Click on previous deployment → "Redeploy"

---

## 💡 Tips

1. **Cost Optimization**: Railway charges based on usage. Monitor your usage in the dashboard.

2. **Scaling**: Railway auto-scales, but you can set resource limits in Settings → Resources.

3. **Custom Domain**: You can add a custom domain like `api.predictive-play.com` in Railway Settings → Networking.

4. **Multiple Environments**: Create separate Railway services for `staging` and `production`.

5. **Database Performance**: Add indexes to Supabase tables for large datasets (already included in schema).

---

## 🎉 You're All Set!

Your self-hosted ChatKit server is now running with:
- ✅ Advanced interactive widgets
- ✅ Professor Lock personality
- ✅ StatMuse integration
- ✅ Real-time odds and analysis
- ✅ Parlay builder with calculations
- ✅ Full control and customization

Questions? Check the logs or review `pp_server.py` for agent configuration.

