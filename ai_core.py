# ai_core.py
import os
import asyncio
import google.generativeai as genai
from openai import OpenAI
from dotenv import load_dotenv
import json

_sentinel = object()

def safe_next(iterator):
    try:
        return next(iterator)
    except StopIteration:
        return _sentinel

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

gemini_model = None
openai_client = None

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY, transport='rest')
        gemini_model = genai.GenerativeModel("gemini-2.5-flash-lite")
        print("Gemini configurado con éxito usando: gemini-2.5-flash-lite")
    except Exception as e:
        print(f"Error al configurar Gemini: {repr(e)}")
else:
    print("Advertencia: GEMINI_API_KEY no encontrada.")

if OPENAI_API_KEY:
    try:
        openai_client = OpenAI(api_key=OPENAI_API_KEY, timeout=120.0)
        print("OpenAI (ChatGPT) configurado con éxito.")
    except Exception as e:
        print(f"Error al configurar OpenAI: {repr(e)}")
else:
    print("Advertencia: OPENAI_API_KEY no encontrada.")

async def get_gemini_response_stream(prompt):
    if not gemini_model:
        yield {"ai": "Gemini", "error": "Gemini no está configurado."}
        return
    try:
        response = await asyncio.to_thread(gemini_model.generate_content, prompt)
        yield {"ai": "Gemini", "full_text": response.text, "simulated": True}
    except Exception as e:
        yield {"ai": "Gemini", "error": f"Gemini Error: {repr(e)}"}

async def get_openai_response_stream(prompt):
    if not openai_client:
        yield {"ai": "OpenAI", "error": "OpenAI no está configurado."}
        return
    try:
        response_iterator = iter(openai_client.chat.completions.create(
            model="o4-mini-2025-04-16",
            messages=[{"role": "user", "content": prompt}],
            stream=True
        ))
        while True:
            chunk = await asyncio.to_thread(safe_next, response_iterator)
            if chunk is _sentinel:
                break
            content = chunk.choices[0].delta.content
            if content:
                yield {"ai": "OpenAI", "text": content}
    except Exception as e:
        yield {"ai": "OpenAI", "error": f"OpenAI Error: {repr(e)}"}

WORKFLOW_PRESETS = {"1": {"description": "...", "chain": []}}