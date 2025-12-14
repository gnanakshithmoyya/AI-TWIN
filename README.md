# VitaTwin 🧬

A Safe, Explainable AI Body Twin

VitaTwin is a non-diagnostic, AI-powered health companion that helps users understand their health data in a clear, calm, and human way. It combines deterministic medical logic with a hallucination-locked AI layer to provide educational health insights without diagnoses or medication advice.

> ⚠️ VitaTwin does not diagnose conditions or provide medication guidance.  
> It is designed for education, awareness, and health understanding only.

---

## Features

### Deterministic Health Engine

All medical logic is handled by a deterministic rules engine (`app/rules.py`). The AI model never makes medical decisions.

Supported signals include glucose, blood pressure, cholesterol, triglycerides, sleep, activity, BMI, nutrition-related labs, reproductive health indicators, and stress/mood signals. Each signal produces deterministic severity levels, risks, recommendations, and doctor flags.

---

### Explainability and Trends

Every health signal includes the rule that triggered, the thresholds used, why it matters, trend direction (improving / worsening / stable), confidence score (0–100), and sparkline-ready historical values. All trends are history-based and recency-weighted.

---

### Human-Style AI Chat (Hallucination Locked)

The AI chat only rephrases rule-generated facts. It cannot invent diseases, diagnoses, or medications. Unsafe questions are refused, and at most one clarifying question is asked when required data is missing. Responses are calm, supportive, and non-clinical.

---

### Safety and Privacy Guarantees

- No hallucinations  
- No diagnosis or medication advice  
- No learning from AI outputs  
- Learning only from user questions (intent and missing fields)  
- Privacy-safe logging with no raw medical values stored  

---

## Installation

### Prerequisites

- Python 3.9+
- Node.js 18+
- Ollama installed

```bash
brew install ollama
ollama pull llama3
ollama pull nomic-embed-text
```

Clone and set up the backend:
git clone https://github.com/your-username/vitatwin.git
cd vitatwin/twin_engine
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

Set up and run the frontend:
cd frontend_app
npm install

Create .env.local:
VITE_API_BASE=http://127.0.0.1:8000

Start the frontend:
npm run dev

Usage

Upload or enter health data, view explainable summaries and trends, ask natural-language questions in chat, and receive safe, non-diagnostic insights grounded strictly in your data.

⸻

Testing

Run the full backend test suite:
pytest app/evals -q

Tests cover deterministic rules, hallucination prevention, intent classification, trend confidence logic, safety refusals, and privacy-safe logging.

⸻

Disclaimer

VitaTwin provides educational health insights and trends only.
It does not diagnose, treat, or replace professional medical advice.
Always consult a qualified healthcare professional for medical decisions.

⸻

License

MIT License
