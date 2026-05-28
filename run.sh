#!/usr/bin/env bash
# run.sh — Start both backend and frontend in parallel

set -e

echo "═══════════════════════════════════════════════"
echo "  ✦ TaskFlow — Starting up"
echo "═══════════════════════════════════════════════"

# Install backend deps
echo ""
echo "▸ Installing backend dependencies..."
cd "$(dirname "$0")/backend"
pip install -r requirements.txt --quiet

# Install frontend deps
echo "▸ Installing frontend dependencies..."
cd ../frontend
pip install -r requirements.txt --quiet

echo ""
echo "▸ Starting FastAPI backend on http://localhost:8000"
cd ../backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

sleep 2

echo "▸ Starting Streamlit frontend on http://localhost:8501"
cd ../frontend
streamlit run app.py --server.port 8501 --server.address 0.0.0.0 &
FRONTEND_PID=$!

echo ""
echo "═══════════════════════════════════════════════"
echo "  Backend  → http://localhost:8000"
echo "  API Docs → http://localhost:8000/docs"
echo "  Frontend → http://localhost:8501"
echo "═══════════════════════════════════════════════"
echo ""
echo "Press Ctrl+C to stop both servers."

wait $BACKEND_PID $FRONTEND_PID
