# Zomato EdgeVision - Quick Setup Guide

## Task 1: Project Scaffolding ✓ COMPLETED

The project structure has been created with:
- ✅ Next.js 14 frontend with TypeScript and Tailwind CSS
- ✅ FastAPI backend with Python 3.11+ support
- ✅ MongoDB connection setup
- ✅ Environment variable templates
- ✅ Core dependencies installed
- ✅ Basic project structure (routers, services, models)

## What Was Created

### Backend Structure
```
backend/
├── main.py              # FastAPI app with MongoDB connection
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables (configure this!)
├── .env.example         # Template for environment variables
├── routers/            # API route handlers (empty, ready for Task 4)
├── services/           # Business logic (empty, ready for Task 5)
├── models/             # Pydantic models (empty, ready for Task 2)
├── run.sh              # Linux/Mac startup script
└── run.bat             # Windows startup script
```

### Frontend Structure
```
frontend/
├── app/
│   ├── page.tsx         # Main page with welcome screen
│   ├── components/      # React components (ready for Task 9)
│   └── lib/
│       ├── api.ts       # Axios API client
│       └── crypto.ts    # SHA-256 hash generation
├── .env.local           # Environment variables (configure this!)
├── .env.example         # Template for environment variables
└── package.json         # Dependencies: axios, recharts
```

## Next Steps to Get Running

### 1. Install Backend Dependencies

```bash
cd backend
python -m venv venv
venv\Scripts\activate    # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### 2. Configure Backend Environment

Edit `backend/.env`:
```env
MONGODB_URI=mongodb://localhost:27017
SECRET_SALT=your-secret-salt-here
GEMINI_API_KEY=your-api-key-here
```

### 3. Start MongoDB

**Option A: Local MongoDB**
```bash
mongod --dbpath C:\data\db  # Windows
# mongod --dbpath /data/db  # Linux/Mac
```

**Option B: MongoDB Atlas**
- Create free cluster at https://cloud.mongodb.com
- Get connection string and update `MONGODB_URI`

### 4. Start Backend Server

```bash
cd backend
venv\Scripts\activate
uvicorn main:app --reload --port 8000
```

Visit http://localhost:8000/docs to see API documentation

### 5. Configure Frontend Environment

Edit `frontend/.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SECRET_SALT=your-secret-salt-here
NEXT_PUBLIC_GEMINI_API_KEY=your-api-key-here
```

### 6. Start Frontend Server

```bash
cd frontend
npm run dev
```

Visit http://localhost:3000 to see the app

## Verification Checklist

- [ ] Backend starts without errors at http://localhost:8000
- [ ] Frontend starts without errors at http://localhost:3000
- [ ] MongoDB is running and accessible
- [ ] Environment variables are configured
- [ ] API docs are accessible at http://localhost:8000/docs

## What's Next?

Task 1 is complete! The next tasks in the implementation plan are:

- **Task 2**: Database schema and seed data
- **Task 3**: Cryptographic payload validation
- **Task 4**: Ingestion endpoint
- **Task 5**: Fraud detection

See `.kiro/specs/zomato-edgevision/tasks.md` for the complete task list.

## Troubleshooting

### Backend won't start
- Check Python version: `python --version` (need 3.10+)
- Verify dependencies: `pip list`
- Check MongoDB connection in `.env`

### Frontend won't start
- Check Node version: `node --version` (need 18+)
- Reinstall dependencies: `npm install`
- Clear Next.js cache: `rm -rf .next`

### MongoDB connection issues
- Verify MongoDB is running: `mongosh` or `mongo`
- Check connection string format
- For Atlas: whitelist your IP address

## API Keys

You'll need one of these for AI verification:
- **Gemini API**: https://makersuite.google.com/app/apikey
- **OpenAI API**: https://platform.openai.com/api-keys

Add the key to both `backend/.env` and `frontend/.env.local`
