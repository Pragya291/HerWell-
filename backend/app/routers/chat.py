import os
from fastapi import APIRouter
from dotenv import load_dotenv

from ..schemas import ChatMessage, ChatResponse
from ..utils import generate_fallback_chat_reply

load_dotenv()

router = APIRouter(prefix="/api/wellness", tags=["Vera AI Chatbot"])


@router.post("/chat", response_model=ChatResponse)
def chat_with_vera(payload: ChatMessage):
    """
    Proxy endpoint for Vera AI Chatbot companion.
    Uses OpenAI gpt-3.5-turbo if OPENAI_API_KEY is configured.
    Seamlessly falls back to an intelligent rule-based empathetic engine.
    """
    user_message = payload.message.strip()
    api_key = os.getenv("OPENAI_API_KEY")

    system_prompt = (
        "You are Vera, a supportive wellness companion for women. "
        "Provide empathy, CBT-based journaling prompts, breathing exercises, and positive affirmations. "
        "Never give medical diagnoses. If the user is in crisis, provide a helpline number."
    )

    if api_key and api_key != "your_openai_api_key_here":
        try:
            import openai
            client = openai.OpenAI(api_key=api_key)
            completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=350,
                temperature=0.7,
            )
            response_text = completion.choices[0].message.content
            return {"response": response_text, "source": "openai"}
        except Exception as e:
            # Fallback gracefully if OpenAI API call fails or quota exceeded
            fallback_text = generate_fallback_chat_reply(user_message)
            return {"response": fallback_text, "source": "fallback"}
    else:
        # Fallback when OPENAI_API_KEY is not set
        fallback_text = generate_fallback_chat_reply(user_message)
        return {"response": fallback_text, "source": "fallback"}
