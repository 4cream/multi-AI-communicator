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

# --- 4. WORKFLOW PRESETS (ACTUALIZADO) ---
WORKFLOW_PRESETS = {
    "1": {
        "description": "Análisis y Crítica (Gemini -> OpenAI)",
        "chain": [
            {
                "ia_name": "gemini", 
                "system_instruction": "Eres un analista experto y un generador de borradores. Tu objetivo es tomar un problema o una solicitud y producir una respuesta inicial completa y bien estructurada.",
                "task_description": "Genera una respuesta detallada o un borrador inicial basado en la pregunta del usuario."
            },
            {
                "ia_name": "openai", 
                "system_instruction": "Eres un editor y un crítico constructivo. Tu única función es revisar y mejorar el texto que se te proporciona.",
                "task_description": "Analiza la respuesta anterior. Identifica tres puntos clave de mejora, posibles errores o áreas de expansión. Proporciona una versión refinada o una crítica constructiva."
            }
        ]
    },
    "2": {
        "description": "Brainstorming y Filtro (OpenAI -> Gemini)",
         "chain": [
            {
                "ia_name": "openai", 
                "system_instruction": "Eres un generador de ideas creativo y sin restricciones. Tu objetivo es proponer una amplia variedad de conceptos.",
                "task_description": "Genera una lista de 5 a 7 ideas diversas sobre el tema propuesto por el usuario."
            },
            {
                "ia_name": "gemini", 
                "system_instruction": "Eres un estratega pragmático y un evaluador. Tu objetivo es filtrar ideas basándote en la viabilidad y el impacto.",
                "task_description": "Evalúa la lista de ideas anterior. Selecciona las 3 mejores, ordénalas por potencial y justifica brevemente tu elección."
            }
        ]
    }
    # Podemos añadir más presets aquí en el futuro.
}