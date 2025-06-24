# Supabase Setup Guide for AKRIN AI Chatbot

## 1. Create Supabase Account

1. Go to [https://supabase.com](https://supabase.com)
2. Click "Start your project" 
3. Sign up with GitHub or email

## 2. Create New Project

1. Click "New project"
2. Fill in:
   - **Project name**: `akrin-chatbot`
   - **Database Password**: Generate a strong password (save this!)
   - **Region**: Choose closest to your users
   - **Pricing Plan**: Free tier is fine

3. Click "Create new project" (takes ~2 minutes)

## 3. Get Your Database URL

1. Go to your project dashboard
2. Click "Settings" (gear icon) → "Database"
3. Find "Connection string" → "URI"
4. Copy the connection string. It looks like:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.xxxxxxxxxxxx.supabase.co:5432/postgres
   ```

## 4. Configure Render Environment

In your Render dashboard, add this environment variable:

```
DATABASE_URL = postgresql://postgres:[YOUR-PASSWORD]@db.xxxxxxxxxxxx.supabase.co:5432/postgres
```

**Important**: Replace `[YOUR-PASSWORD]` with the database password you created.

## 5. Alternative Connection String (if needed)

If you get connection errors, try using the "Connection pooling" string instead:
1. In Supabase: Settings → Database → Connection pooling → Connection string
2. This uses port 6543 instead of 5432

## 6. Initialize Database (Optional)

After deployment, you can initialize the database with sample data:

1. SSH into your Render service (or use Render Shell)
2. Run:
   ```bash
   python scripts/init_db.py
   ```

## Database Features with Supabase

- **Persistent Storage**: Unlike SQLite on free tier, your data persists
- **Concurrent Connections**: Handles multiple users simultaneously
- **Full-text Search**: PostgreSQL's powerful search capabilities
- **Real-time Updates**: Can enable Supabase real-time features later
- **Automatic Backups**: Daily backups on free tier

## Monitoring Your Database

1. In Supabase dashboard → "Database"
2. You can see:
   - Active connections
   - Database size
   - Query performance
   - Table data

## Troubleshooting

### Connection Refused
- Check your DATABASE_URL format
- Ensure password is URL-encoded if it contains special characters
- Try the pooled connection string

### SSL Error
- Supabase requires SSL. The asyncpg library handles this automatically

### Performance Issues
- Free tier has limits: 500MB database, 2 concurrent connections
- Upgrade if needed

## Security Notes

- Never commit DATABASE_URL to git
- Use Render's environment variables
- Enable Row Level Security (RLS) in Supabase for production
- Regularly rotate database passwords