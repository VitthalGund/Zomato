# Zomato EdgeVision - Hackathon Demo

Edge-computing system that replaces manual "Food Ready" merchant signals with AI-verified timestamps using cryptographic proof.

## Project Structure

```
.
├── frontend/          # Next.js 14 frontend with TypeScript and Tailwind CSS
│   ├── app/
│   │   ├── components/  # React components
│   │   ├── lib/         # Utility functions (API client, crypto)
│   │   └── page.tsx     # Main page
│   ├── .env.local       # Environment variables (not committed)
│   └── package.json
│
├── backend/           # FastAPI backend with Python 3.11+
│   ├── routers/       # API route handlers
│   ├── services/      # Business logic (fraud detection, velocity calculation)
│   ├── models/        # Pydantic models
│   ├── main.py        # FastAPI application entry point
│   ├── .env           # Environment variables (not committed)
│   └── requirements.txt
│
└── .kiro/specs/zomato-edgevision/  # Specification documents
```

## Setup Instructions

### Prerequisites

- Node.js 18+ and npm
- Python 3.11+
- MongoDB (local or Atlas)

### Backend Setup

1. Navigate to backend directory:
   ```bash
   cd backend
   ```

2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   - Copy `.env.example` to `.env`
   - Update `MONGODB_URI` with your MongoDB connection string
   - Set `SECRET_SALT` to a secure random string
   - Add your `GEMINI_API_KEY` or `OPENAI_API_KEY`

5. Run the server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

   The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Configure environment variables:
   - Copy `.env.example` to `.env.local`
   - Update `NEXT_PUBLIC_API_URL` if backend is not on localhost:8000
   - Set `NEXT_PUBLIC_SECRET_SALT` to match backend SECRET_SALT
   - Add your `NEXT_PUBLIC_GEMINI_API_KEY` or `NEXT_PUBLIC_OPENAI_API_KEY`

4. Run the development server:
   ```bash
   npm run dev
   ```

   The app will be available at `http://localhost:3000`

### MongoDB Setup

#### Option 1: Local MongoDB

1. Install MongoDB Community Edition
2. Start MongoDB service:
   ```bash
   mongod --dbpath /path/to/data/directory
   ```
3. Use connection string: `mongodb://localhost:27017`

#### Option 2: MongoDB Atlas (Cloud)

1. Create free cluster at https://www.mongodb.com/cloud/atlas
2. Get connection string from Atlas dashboard
3. Update `MONGODB_URI` in backend `.env` file

## API Documentation

Once the backend is running, visit:
- API docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

## Core Features

1. **Edge Camera Capture**: Webcam capture at 3 FPS with 640x640 resolution
2. **AI Verification**: Detect food parcels and KOT receipts using Gemini/GPT-4o Vision API
3. **Spatial Verification**: Ensure receipt is attached to food package (bounding box intersection)
4. **Temporal Debouncing**: Require 3 consecutive successful detections
5. **Cryptographic Payload**: SHA-256 hash for tamper-proof verification
6. **Fraud Detection**: Flag premature scans (empty bag detection)
7. **Velocity Calculation**: Calculate kitchen throughput using Little's Law
8. **Invisible Load Detection**: Detect congestion from non-Zomato orders
9. **Dynamic KPT Adjustment**: Automatically adjust Kitchen Prep Time based on velocity
10. **Real-time Dashboard**: Visualize velocity metrics and verification logs

## Development Workflow

1. Start MongoDB
2. Start backend server (`uvicorn main:app --reload`)
3. Start frontend dev server (`npm run dev`)
4. Open browser to `http://localhost:3000`

## Next Steps

See `.kiro/specs/zomato-edgevision/tasks.md` for the complete implementation plan.

Current status: Task 1 (Project scaffolding) completed ✓

Next tasks:
- Task 2: Database schema and seed data
- Task 3: Cryptographic payload validation
- Task 4: Ingestion endpoint
- Task 5: Fraud detection
