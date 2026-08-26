# MannMitra Prototype

A working prototype: a private, voice-enabled AI chat companion for students,
with a basic crisis-detection safety layer.

## What's inside
- `backend/` - FastAPI server that talks to Claude and runs the safety check
- `frontend/` - a simple, no-build-tools chat interface (just HTML/CSS/JS)

## How to run it (step by step)

### 1. Set up the backend
```
cd backend
python -m venv venv
venv\Scripts\activate        (Windows)
source venv/bin/activate     (Mac/Linux)
pip install -r requirements.txt
```

### 2. Add your API key
Copy `.env.example` to `.env`, and paste your real Anthropic API key into it:
```
ANTHROPIC_API_KEY=sk-ant-xxxxxxxx
```
Never share this file or upload it to GitHub.

### 3. Start the backend
```
uvicorn main:app --reload
```
You should see it running at http://127.0.0.1:8000

### 4. Open the frontend
Just double-click `frontend/index.html` to open it in your browser
(Chrome recommended, since voice input works best there).

### 5. Try it
Type a message, or tap the mic button and speak. You should get a
reply back, spoken aloud automatically.

## What to show your HOD
- The chat working end to end (type or speak, get a warm, natural reply)
- The privacy disclaimer at the bottom of the screen
- Try typing something like "I'm feeling really hopeless" to show the
  crisis banner and helpline numbers appearing automatically

## What's still a placeholder (be upfront about this)
- The ML stress/anxiety scoring model isn't wired in yet - the safety
  layer currently uses keyword detection only, which is a real and
  useful first layer, but the trained ML model is the next step.
- The RAG knowledge base (LPU handbook, policies) isn't connected yet -
  right now Claude answers from its system prompt only.
- This is meant to be embedded into the college portal eventually -
  right now it runs as a standalone page for demo purposes.

Being clear about these gaps is a good thing to say out loud in your
demo - it shows you know exactly what's built versus what's next.
