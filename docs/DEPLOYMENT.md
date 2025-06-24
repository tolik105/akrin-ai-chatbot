# Deployment Guide - AKRIN AI Chatbot

## Deploying to Render.com

### Prerequisites
1. GitHub account with your code repository
2. Render.com account (free tier is sufficient)
3. API keys ready (OpenAI, Anthropic, Pinecone)

### Step 1: Prepare Your Repository

1. **Update your code for production**:
   ```python
   # In src/api/main.py, add:
   import os
   
   # Get port from environment
   if __name__ == "__main__":
       port = int(os.environ.get("PORT", 8000))
       uvicorn.run("src.api.main:app", host="0.0.0.0", port=port)
   ```

2. **Create a `.gitignore`** if you haven't:
   ```
   .env
   *.pyc
   __pycache__/
   venv/
   .coverage
   htmlcov/
   *.db
   logs/
   data/
   ```

3. **Commit and push to GitHub**:
   ```bash
   git add .
   git commit -m "Prepare for Render deployment"
   git push origin main
   ```

### Step 2: Deploy on Render

1. **Go to [Render Dashboard](https://dashboard.render.com/)**

2. **Click "New +" → "Web Service"**

3. **Connect your GitHub repository**:
   - Authorize Render to access your GitHub
   - Select your `akrin-ai-chatbot` repository

4. **Configure the service**:
   - **Name**: `akrin-chatbot-api`
   - **Region**: Choose closest to your users
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: 
     ```bash
     pip install -r requirements.txt && python -m spacy download en_core_web_md
     ```
   - **Start Command**:
     ```bash
     uvicorn src.api.main:app --host 0.0.0.0 --port $PORT
     ```

5. **Add Environment Variables** (click "Advanced"):
   ```
   OPENAI_API_KEY=your_openai_key
   ANTHROPIC_API_KEY=your_anthropic_key
   PINECONE_API_KEY=your_pinecone_key
   PINECONE_ENVIRONMENT=us-east-1-aws
   PINECONE_INDEX_NAME=akrin-knowledge-base
   JWT_SECRET_KEY=generate_a_secure_key_here
   DATABASE_URL=sqlite:///data/akrin_chatbot.db
   APP_ENV=production
   ```

6. **Add Disk** (for SQLite persistence):
   - Click "Add Disk"
   - Name: `akrin-data`
   - Mount Path: `/data`
   - Size: `1 GB` (free tier)

7. **Click "Create Web Service"**

### Step 3: Post-Deployment Setup

1. **Wait for deployment** (5-10 minutes)

2. **Test your API**:
   ```bash
   # Your API will be at: https://akrin-chatbot-api.onrender.com
   curl https://akrin-chatbot-api.onrender.com/api/health
   ```

3. **View API docs**:
   - Visit: `https://akrin-chatbot-api.onrender.com/api/docs`

### Step 4: Integrate Chat Widget

1. **Update WebSocket URL** in `chat-widget.html`:
   ```javascript
   // Change from:
   const WS_URL = 'ws://localhost:8000/ws/chat/';
   
   // To:
   const WS_URL = 'wss://akrin-chatbot-api.onrender.com/ws/chat/';
   ```

2. **Embed in your website**:
   ```html
   <!-- Add to your website -->
   <iframe 
     src="https://akrin-chat-widget.onrender.com/" 
     style="position: fixed; bottom: 20px; right: 20px; 
            width: 380px; height: 600px; border: none; 
            z-index: 9999;">
   </iframe>
   
   <!-- Or include directly -->
   <script>
     (function() {
       const script = document.createElement('script');
       script.src = 'https://akrin-chatbot-api.onrender.com/static/chat-widget.js';
       document.body.appendChild(script);
     })();
   </script>
   ```

## Real-Time Chat Features

### Customer Chat Widget
- **Location**: `/static/chat-widget.html`
- **Features**:
  - AI-powered responses
  - Human handoff request
  - Real-time messaging
  - Mobile responsive
  - Minimizable interface

### Agent Dashboard
- **Location**: `/static/agent-dashboard.html`
- **Access**: `https://akrin-chatbot-api.onrender.com/static/agent-dashboard.html`
- **Features**:
  - Real-time customer queue
  - Multiple chat management
  - Message history
  - Transfer capabilities

### WebSocket Endpoints
1. **Customer Chat**: `wss://your-app.onrender.com/ws/chat/{session_id}`
2. **Agent Dashboard**: `wss://your-app.onrender.com/ws/agent/{agent_id}`

## Monitoring and Maintenance

### View Logs
- In Render Dashboard → Your Service → "Logs" tab

### Monitor Performance
- Check Render metrics
- API health endpoint: `/api/health`
- Detailed health: `/api/health/detailed`

### Update Deployment
```bash
# Simply push to GitHub
git add .
git commit -m "Update features"
git push origin main

# Render auto-deploys!
```

## Cost Optimization

### Free Tier Limits
- **Render**: 750 hours/month (enough for 24/7)
- **Spins down**: After 15 min inactivity
- **Solution**: Use uptime monitors (UptimeRobot, Pingdom)

### Performance Tips
1. **Warm up**: Set up monitoring to ping every 10 min
2. **Cache**: Leverage in-memory cache
3. **Optimize**: Use SQLite for low memory usage

## Troubleshooting

### Common Issues

1. **"Application failed to respond"**
   - Check logs for errors
   - Ensure PORT environment variable is used
   - Verify all dependencies installed

2. **WebSocket connection failed**
   - Use `wss://` not `ws://` for HTTPS
   - Check CORS settings
   - Ensure WebSocket route included

3. **SQLite database errors**
   - Ensure disk is mounted at `/data`
   - Check file permissions
   - Use absolute path in DATABASE_URL

### Debug Commands
```bash
# SSH into container (paid plans only)
# Use Render Shell in dashboard instead

# Check disk usage
df -h /data

# View recent logs
tail -f logs/akrin_chatbot.log
```

## Production Checklist

- [ ] Environment variables set in Render
- [ ] Database disk attached
- [ ] WebSocket URLs updated to production
- [ ] CORS configured for your domain
- [ ] Health checks passing
- [ ] Monitoring configured
- [ ] SSL/TLS enabled (automatic on Render)
- [ ] Rate limiting configured
- [ ] Error tracking enabled

## Next Steps

1. **Add custom domain**: Settings → Custom Domains
2. **Enable auto-scaling**: Upgrade to paid plan
3. **Set up monitoring**: Connect to Datadog/New Relic
4. **Configure backups**: Automated database backups
5. **Implement CI/CD**: GitHub Actions integration