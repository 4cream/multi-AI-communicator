# ai_core.py

import os
import asyncio
import google.generativeai as genai
from openai import OpenAI
from dotenv import load_dotenv
import datetime
import textwrap

# --- 1. CARGAR VARIABLES DE ENTORNO ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- 2. CONFIGURACIÓN DE LAS APIS ---
gemini_model = None
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # Lógica robusta para seleccionar un modelo disponible
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Lista de modelos preferidos en orden de preferencia
        preferred_models = ['models/gemini-1.5-pro-latest', 'models/gemini-1.5-flash-latest']
        
        model_to_use = None
        for model in preferred_models:
            if model in available_models:
                model_to_use = model
                break
        
        if not model_to_use and available_models:
            model_to_use = available_models[0] # Usar el primero disponible como último recurso

        if model_to_use:
            gemini_model = genai.GenerativeModel(model_to_use)
            print(f"Gemini configurado con éxito usando: {model_to_use}")
        else:
            print("Advertencia: No se encontró ningún modelo de Gemini compatible.")
            
    except Exception as e:
        print(f"Error al configurar Gemini: {e}")
else:
    print("Advertencia: GEMINI_API_KEY no encontrada.")


openai_client = None
if OPENAI_API_KEY:
    try:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        print("OpenAI (ChatGPT) configurado con éxito.")
    except Exception as e:
        print(f"Error al configurar OpenAI: {e}")
else:
    print("Advertencia: OPENAI_API_KEY no encontrada.")


# --- 3. FUNCIONES ASÍNCRONAS DE IA ---
async def get_gemini_response(prompt, system_prompt=None):
    if not gemini_model:
        return "Gemini no configurado o modelo no disponible."
    try:
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"INSTRUCCIÓN DE SISTEMA: {system_prompt}\n\nTAREA: {prompt}"
        response = await asyncio.to_thread(gemini_model.generate_content, full_prompt)
        return response.text
    except Exception as e:
        return f"Gemini Error: {e}"

async def get_openai_response(prompt, system_prompt=None):
    if not openai_client:
        return "OpenAI no configurado."
    try:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        response = await asyncio.to_thread(
            openai_client.chat.completions.create,
            model="gpt-3.5-turbo",
            messages=messages
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"OpenAI Error: {e}"

# --- 4. FUNCIÓN DE LOG ---
def log_conversation(prompt, responses, mode="comparacion"):
    log_file_path = "conversation_log.txt"
    with open(log_file_path, "a", encoding="utf-8") as f:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"--- Consulta ({mode.upper()}) {timestamp} ---\n")
        f.write(f"Pregunta Inicial: {prompt}\n\n")
        if mode == "comparacion":
            for ia_name, response_text in responses.items():
                f.write(f"--- {ia_name} ---\n{textwrap.fill(response_text, width=80)}\n\n")
        elif mode == "encadenada":
            for i, step in enumerate(responses):
                f.write(f"--- Paso {i+1}: {step['ia_name']} ({step['task']}) ---\n")
                f.write(f"Respuesta: {textwrap.fill(step['response'], width=80)}\n\n")
        f.write("="*60 + "\n\n")
    print(f"Conversación guardada en {log_file_path}")

# --- 5. PRESETS DE FLUJO DE TRABAJO ---
WORKFLOW_PRESETS = {
    "1": {
        "description": "Estrategia de Apuestas Deportivas: Gemini analiza, OpenAI detalla el plan.",
        "chain": [
            {"ia_name": "gemini", "system_instruction": "Eres un experto en gestión de riesgos y estrategias de inversión. Sé conciso y estratégico.", "task_description": "Analiza la pregunta inicial. Ofrece una estrategia para la gestión del dinero, enfocándote en disciplina y riesgo."},
            {"ia_name": "openai", "system_instruction": "Eres un planificador de estrategias y un comunicador claro.", "task_description": "Basándote en la estrategia inicial, detalla 3-5 pasos concretos y un plan de acción para implementarla."}
        ]
    },
    "2": {
        "description": "Resumen y Crítica: OpenAI resume, Gemini ofrece puntos de mejora.",
        "chain": [
            {"ia_name": "openai", "system_instruction": "Eres un resumidor experto y conciso.", "task_description": "Resume el texto proporcionado en 50 palabras, extrayendo las ideas principales."},
            {"ia_name": "gemini", "system_instruction": "Eres un crítico constructivo y analítico.", "task_description": "Analiza el resumen proporcionado e identifica 3 posibles puntos débiles o áreas de mejora en el texto original."}
        ]
    },
    "3": {
        "description": "Brainstorming y Filtro: Gemini genera conceptos, OpenAI los filtra por viabilidad.",
        "chain": [
            {"ia_name": "gemini", "system_instruction": "Eres un generador de ideas creativo y original.", "task_description": "Genera una lista de 5 ideas creativas relacionadas con el tema propuesto."},
            {"ia_name": "openai", "system_instruction": "Eres un evaluador práctico y realista.", "task_description": "Evalúa las ideas recibidas en términos de viabilidad práctica. Ordena las restantes de mayor a menor viabilidad con una breve justificación."}
        ]
    }
}

# --- 6. FUNCIONES WRAPPER PARA FLASK ---
async def run_comparison_mode(prompt):
    if not gemini_model and not openai_client:
        return {"Error": "Ninguna IA está configurada."}
    tasks, active_ias = [], []
    if gemini_model:
        tasks.append(asyncio.create_task(get_gemini_response(prompt)))
        active_ias.append("Gemini")
    if openai_client:
        tasks.append(asyncio.create_task(get_openai_response(prompt)))
        active_ias.append("OpenAI (ChatGPT)")
    
    responses_list = await asyncio.gather(*tasks)
    all_responses = dict(zip(active_ias, responses_list))
    log_conversation(prompt, all_responses, mode="comparacion")
    return all_responses

async def run_chain_mode(prompt, preset_key):
    selected_preset = WORKFLOW_PRESETS.get(preset_key)
    if not selected_preset:
        return [{"Error": "Preset no válido."}]
    
    chain_definition = selected_preset["chain"]
    available_ais_info = {
        "gemini": {"func": get_gemini_response, "active": bool(gemini_model)},
        "openai": {"func": get_openai_response, "active": bool(openai_client)},
    }
    
    current_context = prompt
    full_conversation_log = []

    for step_config in chain_definition:
        ia_name = step_config["ia_name"]
        if not available_ais_info.get(ia_name, {}).get("active"):
            full_conversation_log.append({"ia_name": ia_name.upper(), "task": "SALTADO", "response": "Esta IA no está configurada."})
            continue

        ia_system_instruction = step_config["system_instruction"]
        ia_task_description = step_config["task_description"]
        ia_func = available_ais_info[ia_name]["func"]

        prompt_for_current_ia = f"CONTEXTO PREVIO: {current_context}\n\nTU TAREA ES: {ia_task_description}"
        response_text = await ia_func(prompt_for_current_ia, system_prompt=ia_system_instruction)
        
        full_conversation_log.append({
            "ia_name": ia_name.upper(),
            "task": ia_task_description,
            "response": response_text
        })
        current_context = response_text
    
    log_conversation(prompt, full_conversation_log, mode="encadenada")
    return full_conversation_log