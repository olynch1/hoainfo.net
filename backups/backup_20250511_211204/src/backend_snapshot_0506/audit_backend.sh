#!/bin/bash

echo "📦 Running HOA Backend System Audit..."
echo "🕒 Timestamp: $(date)"
echo "📁 Current Directory: $(pwd)"

echo "----------------------------------------"
echo "🔍 Checking project structure..."
ls -la

echo "----------------------------------------"
echo "🐍 Checking Python & venv..."
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "🟢 venv activated"
else
    echo "⚠️  No venv found. Run: python3 -m venv venv"
fi

if command -v python3 &> /dev/null; then
    echo "✅ Python3 path: $(which python3)"
    echo "✅ Python3 version: $(python3 --version)"
else
    echo "❌ Python3 not found. Install via Homebrew: brew install python3"
fi

echo "----------------------------------------"
echo "📦 Checking requirements.txt..."
if [ -f "requirements.txt" ]; then
    echo "Installing packages..."
    pip install -r requirements.txt > /dev/null
    echo "✅ Packages installed"
else
    echo "⚠️  No requirements.txt found. Run: pip freeze > requirements.txt"
fi

echo "----------------------------------------"
echo "🔐 Checking .env variables..."
if [ -f ".env" ]; then
    echo "✅ Found .env file"
    grep -E 'SECRET|STRIPE|RESEND' .env || echo "⚠️  No matching env vars found"
else
    echo "⚠️  .env file missing. Create one with: touch .env"
fi

echo "----------------------------------------"
echo "🗃️  Checking SQLite database (hoa.db)..."
if [ -f "hoa.db" ]; then
    echo "✅ hoa.db exists"
    echo "📂 Tables:"
    sqlite3 hoa.db ".tables"
else
    echo "❌ hoa.db not found"
fi

echo "----------------------------------------"
echo "🚀 Testing FastAPI/Uvicorn launch..."
uvicorn main:app --host 127.0.0.1 --port 8000 --reload &
PID=$!
sleep 5

if ps -p $PID > /dev/null; then
   echo "✅ Uvicorn launched (PID $PID)"
   kill $PID
else
   echo "❌ Uvicorn failed to launch. Check main.py and FastAPI app instance"
fi

echo "----------------------------------------"
echo "📌 HOA Backend Audit Complete."

# 🔧 1. Create and activate your virtual environment
python3 -m venv venv
source venv/bin/activate

