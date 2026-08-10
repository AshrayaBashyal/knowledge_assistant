import os
import random
from langchain_google_genai import ChatGoogleGenerativeAI

def get_chat_model(*, streaming: bool = True) -> ChatGoogleGenerativeAI:
    # 1. Try to read and parse multiple keys
    api_keys_raw = os.getenv("GEMINI_API_KEYS", "").strip()
    
    if api_keys_raw:
        # Filter out empty strings from malformed lists like "key1,,key2"
        api_keys = [key.strip() for key in api_keys_raw.split(",") if key.strip()]
        selected_key = random.choice(api_keys) if api_keys else None
    else:
        selected_key = None

    # 2. Fall back to single key if multiple keys weren't found
    if not selected_key:
        selected_key = os.getenv("GEMINI_API_KEY")

    # 3. Fail early with a clear message if completely missing keys
    if not selected_key:
        raise ValueError(
            "Missing API Key: Please set either 'GEMINI_API_KEYS' or "
            "'GEMINI_API_KEY' in your environment variables."
        )

    # 4. Safely parse temperature to avoid ValueError on empty strings
    temp_env = os.getenv("GEMINI_TEMPERATURE", "0.3").strip()
    temperature = float(temp_env) if temp_env else 0.3

    # 5. Initialize and return the model
    return ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite"),
        temperature=temperature,
        google_api_key=selected_key,
        streaming=streaming,
        convert_system_message_to_human=False,
    )




# import os
# from langchain_google_genai import ChatGoogleGenerativeAI

# def get_chat_model(*, streaming: bool = True) -> ChatGoogleGenerativeAI:
#     """Factory for the chat model used across the app."""


#     return ChatGroq(
#         model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
#         temperature=float(os.getenv("GROQ_TEMPERATURE", "0.7")),
#         api_key=os.getenv("GROQ_API_KEY"),
#         streaming=streaming,
#     )
    
#     return ChatGoogleGenerativeAI(
#         model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
#         temperature=float(os.getenv("GEMINI_TEMPERATURE", "0.7")),
#         google_api_key=os.getenv("GEMINI_API_KEY"),
#         streaming=streaming,
#         # Gemini handles function calling/tool usage natively
#         convert_system_message_to_human=False, 
#     )