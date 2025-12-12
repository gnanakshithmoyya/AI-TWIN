import json
import ollama

class TwinEngine:
    def explain_health(self, health_state: dict) -> str:
        prompt = f"""
You are a friendly AI Body Twin.
Explain the following health information in very simple, supportive language.
Do NOT diagnose. Do NOT scare the user.
Focus on trends and small, realistic improvements.

Health data:
{json.dumps(health_state, indent=2)}
"""

        response = ollama.chat(
            model="llama3",
            messages=[{"role": "user", "content": prompt}]
        )

        return response["message"]["content"]