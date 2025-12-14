VitaTwin 🧬

A Safe, Explainable AI Body Twin

VitaTwin is a non-diagnostic, AI-powered health companion that helps users understand their health data in a clear, calm, and explainable way.

It combines:
	•	a deterministic medical rules engine
	•	trend & explainability logic
	•	hallucination-locked AI responses
	•	privacy-safe learning from user questions

⚠️ VitaTwin does not diagnose conditions or provide medication advice.
It is designed for education, awareness, and health understanding only.

⸻

✨ Key Features

🧠 Deterministic Health Engine

All medical logic is handled by a rules engine (app/rules.py):
	•	Glucose, BP, lipids, sleep, activity, BMI, nutrition labs
	•	Reproductive health & mental/stress signals
	•	Clear severity levels, risks, recommendations, and doctor flags

No medical decisions are ever made by the AI model.

⸻

🔍 Explainability & Trends

Each health signal includes:
	•	Why the rule triggered
	•	Thresholds used
	•	Why it matters
	•	Trend direction (improving / worsening / stable)
	•	Confidence score (0–100)
	•	Sparkline-ready data for visualization

⸻

💬 Human-Style AI Chat (Hallucination-Locked)

The AI:
	•	Only rephrases rule-generated facts
	•	Cannot invent diseases, medications, or diagnoses
	•	Refuses unsafe questions (meds, diagnosis)
	•	Asks at most one clarifying question if data is missing

⸻

🛡️ AI Safety Guarantees
	•	❌ No hallucinations
	•	❌ No diagnosis or medication advice
	•	❌ No learning from AI outputs
	•	✅ Learning only from user questions (intent & missing fields)
	•	✅ Privacy-safe logging (no raw medical values stored)

⸻

🏗️ Tech Stack

Backend
	•	FastAPI
	•	Python 3.9+
	•	Deterministic rules engine
	•	Ollama (local LLM)
	•	Pytest (full test coverage)

Frontend
	•	React + TypeScript
	•	Vite
	•	Fetch-based API integration

⸻

🚀 Running VitaTwin Locally

1️⃣ Prerequisites
	•	Python 3.9+
	•	Node.js 18+
	•   Ollama

Install Ollama: 
•brew install ollama

Pull required models:
•ollama pull llama3
•ollama pull nomic-embed-text
Backend Setup
•git clone https://github.com/your-username/vitatwin.git
•cd vitatwin/twin_engine
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
Run backend:
uvicorn app.main:app --reload --port 8000
Frontend Setup
cd frontend_app
npm install
Create .env.local:
VITE_API_BASE=http://127.0.0.1:8000
Run frontend:
npm run dev
Visit:
👉 http://localhost:5173

⸻

🧪 Testing
Run all backend tests:
pytest app/evals -q
📜 Disclaimer

VitaTwin provides educational health insights and trends.
It does not diagnose, treat, or replace professional medical advice.
Always consult a qualified healthcare professional.
