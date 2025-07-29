# main.py

import os
import asyncio
import google.generativeai as genai
from openai import OpenAI
from dotenv import load_dotenv
import datetime
import textwrap

# --- 1. Cargar las variables de entorno ---
load_dotenv()

# --- 2. Obtener las API Keys del entorno ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")


# --- 3. Configurar las APIs con tus claves ---

# Gemini
gemini_model = None
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        PREFERRED_GEMINI_MODEL = 'models/gemini-2.5-flash-lite' 

        chosen_model_found = False
        available_gemini_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods: 
                available_gemini_models.append(m.name)
        
        if PREFERRED_GEMINI_MODEL in available_gemini_models:
            gemini_model = genai.GenerativeModel(PREFERRED_GEMINI_MODEL)
            chosen_model_found = True
        else:
            for model_name in available_gemini_models:
                if 'gemini' in model_name.lower() and 'generateContent' in genai.get_model(model_name).supported_generation_methods:
                    gemini_model = genai.GenerativeModel(model_name)
                    chosen_model_found = True
                    break
            
        if gemini_model:
            print(f"Gemini configurado con éxito usando: {gemini_model.model_name}")
        else:
            print(f"Error: No se encontró ningún modelo Gemini compatible.")

    except Exception as e:
        print(f"Error al configurar Gemini: {e}")
        gemini_model = None
else:
    print("Advertencia: GEMINI_API_KEY no encontrada.")


# OpenAI
openai_client = None
if OPENAI_API_KEY:
    try:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        print("OpenAI (ChatGPT) configurado con éxito.")
    except Exception as e:
        print(f"Error al configurar OpenAI: {e}")
        openai_client = None
else:
    print("Advertencia: OPENAI_API_KEY no encontrada.")


# Anthropic (Claude) - Placeholder
claude_client = None
# if CLAUDE_API_KEY:
#     try:
#         from anthropic import Anthropic
#         claude_client = Anthropic(api_key=CLAUDE_API_KEY)
#         print("Anthropic (Claude) configurado con éxito.")
#     except Exception as e:
#         print(f"Error al configurar Anthropic: {e}")
#         claude_client = None

# DeepSeek - Placeholder
deepseek_client = None
# if DEEPSEEK_API_KEY:
#     try:
#         # from openai import OpenAI as DeepSeekOpenAIClient
#         # deepseek_client = DeepSeekOpenAIClient(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com/v1")
#         print("DeepSeek configurado con éxito.")
#     except Exception as e:
#         print(f"Error al configurar DeepSeek: {e}")
#         deepseek_client = None


# --- 4. Funciones Asíncronas para obtener respuestas de cada IA (usan asyncio.to_thread) ---

async def get_gemini_response(prompt, system_prompt=None):
    if not gemini_model:
        return "Gemini no configurado o modelo no disponible."
    try:
        full_prompt = prompt
        if system_prompt:
            # Para Gemini, inyectamos el system_prompt al inicio del prompt principal
            # ya que generate_content no tiene un parámetro 'system' directo como chat.completions
            full_prompt = f"INSTRUCCIÓN DE SISTEMA PARA EL ROL: {system_prompt}\n\n" \
                          f"Aquí está la tarea principal y el contexto:\n{prompt}"

        response = await asyncio.to_thread(gemini_model.generate_content, full_prompt)
        
        if response.candidates and response.candidates[0].content.parts:
            return response.candidates[0].content.parts[0].text
        else:
            return "Gemini: No se pudo obtener una respuesta textual (posiblemente contenido bloqueado o vacío)."
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

async def get_claude_response(prompt, system_prompt=None):
    if not claude_client:
        return "Claude no configurado."
    try:
        # IMPLEMENTACIÓN ASÍNCRONA DE CLAUDE AQUÍ
        # messages = []
        # if system_prompt:
        #     messages.append({"role": "user", "content": f"<system_prompt>{system_prompt}</system_prompt>"})
        # messages.append({"role": "user", "content": prompt})
        #
        # response = await asyncio.to_thread(
        #     claude_client.messages.create,
        #     model="claude-3-opus-20240229",
        #     max_tokens=1024,
        #     messages=messages
        # )
        # return response.content[0].text
        return "Claude: [IMPLEMENTAR ASÍNCRONO]" # Placeholder
    except Exception as e:
        return f"Claude Error: {e}"

async def get_deepseek_response(prompt, system_prompt=None):
    if not deepseek_client:
        return "DeepSeek no configurado."
    try:
        # IMPLEMENTACIÓN ASÍNCRONA DE DEEPSEEK AQUÍ
        # messages = []
        # if system_prompt:
        #     messages.append({"role": "system", "content": system_prompt})
        # messages.append({"role": "user", "content": prompt})
        #
        # response = await asyncio.to_thread(
        #     deepseek_client.chat.completions.create,
        #     model="deepseek-chat",
        #     messages=messages
        # )
        # return response.choices[0].message.content
        return "DeepSeek: [IMPLEMENTAR ASÍNCRONO]" # Placeholder
    except Exception as e:
        return f"DeepSeek Error: {e}"


# --- 5. Funciones Auxiliares ---
def log_conversation(prompt, responses, mode="comparacion"):
    """Guarda la conversación en un archivo de log."""
    log_file_path = "conversation_log.txt"
    with open(log_file_path, "a", encoding="utf-8") as f:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"--- Consulta ({mode.upper()}) {timestamp} ---\n")
        f.write(f"Pregunta Inicial: {prompt}\n\n")

        if mode == "comparacion":
            for ia_name, response_text in responses.items():
                f.write(f"--- {ia_name} ---\n")
                f.write(textwrap.fill(response_text, width=80) + "\n")
                f.write(f"Longitud: {len(response_text)} caracteres\n")
                f.write(f"{'-' * 30}\n\n")
        elif mode == "encadenada":
            for i, step in enumerate(responses):
                f.write(f"--- Paso {i+1}: {step['ia_name']} ---\n")
                f.write(f"Prompt enviado: {textwrap.fill(step['prompt_sent'], width=80)}\n")
                f.write(f"Respuesta: {textwrap.fill(step['response_text'], width=80)}\n")
                f.write(f"Longitud: {len(step['response_text'])} caracteres\n")
                f.write(f"{'-' * 30}\n\n")

        f.write("=" * 60 + "\n\n")
    print(f"Conversación guardada en {log_file_path}")

# --- Definición de Presets de Flujo de Trabajo (¡ACTUALIZADO!) ---
WORKFLOW_PRESETS = {
    "1": {
        "description": "Estrategia de Apuestas Deportivas: Gemini analiza, OpenAI detalla el plan.",
        "chain": [
            {
                "ia_name": "gemini", 
                "system_instruction": "Eres un experto en gestión de riesgos y estrategias de inversión en mercados volátiles, incluyendo apuestas deportivas. Tu objetivo es proporcionar un análisis inicial conciso y estratégico.", 
                "task_description": "Analiza la pregunta inicial sobre cómo gestionar $50 en apuestas deportivas. Ofrece una estrategia inicial para la gestión del dinero, enfocándote en la disciplina, el tamaño de las apuestas y la gestión del riesgo."
            },
            {
                "ia_name": "openai", 
                "system_instruction": "Eres un planificador de estrategias y un comunicador claro. Tu objetivo es tomar un análisis previo y expandirlo en pasos accionables y detallados para un público general.", 
                "task_description": "Basándote en la estrategia inicial proporcionada, detalla 3-5 pasos concretos y un plan de acción para implementar esa gestión de $50 en apuestas deportivas. Incluye consejos prácticos y un ejemplo de cómo se podría aplicar."
            }
        ]
    },
    "2": {
        "description": "Resumen y Crítica: OpenAI resume, Gemini ofrece puntos de mejora.",
        "chain": [
            {
                "ia_name": "openai", 
                "system_instruction": "Eres un resumidor experto y conciso. Tu objetivo es extraer la esencia de un texto.", 
                "task_description": "Resume el siguiente texto en 50 palabras, extrayendo las ideas principales."
            },
            {
                "ia_name": "gemini", 
                "system_instruction": "Eres un crítico constructivo y analítico. Tu objetivo es identificar áreas de mejora en un texto.", 
                "task_description": "Analiza el resumen proporcionado e identifica 3 posibles puntos débiles o áreas de mejora en el texto original, justificando tu crítica."
            }
        ]
    },
    "3": {
        "description": "Brainstorming y Filtro: Gemini genera conceptos, OpenAI los filtra por viabilidad.",
        "chain": [
            {
                "ia_name": "gemini", 
                "system_instruction": "Eres un generador de ideas creativo y original. Tu objetivo es proponer conceptos diversos.", 
                "task_description": "Genera una lista de 5 ideas creativas sobre cómo reciclar materiales comunes en el hogar."
            },
            {
                "ia_name": "openai", 
                "system_instruction": "Eres un evaluador práctico y un optimizador de procesos. Tu objetivo es discernir la viabilidad y el impacto.", 
                "task_description": "Evalúa las ideas recibidas en términos de viabilidad práctica y potencial impacto ambiental. Elimina las menos viables y ordena las restantes de mayor a menor impacto, con una breve justificación."
            }
        ]
    },
    # Puedes añadir más presets aquí.
}


# --- 6. Función para el Modo de Conversación Encadenada ---
async def run_chained_conversation():
    print("\n--- Modo de Conversación Encadenada ---")
    print("Elige un flujo de trabajo predefinido para encadenar las IAs.")

    # Mostrar presets disponibles
    print("\n--- Flujos de Trabajo Predefinidos ---")
    for key, preset in WORKFLOW_PRESETS.items():
        print(f"{key}. {preset['description']}")
    print("---------------------------------------")
    print("(Escribe 'salir' para volver al menú principal)")

    while True:
        preset_choice = input("Selecciona un número de preset: ").strip()
        if preset_choice.lower() == 'salir':
            return # Salir del modo encadenado

        selected_preset = WORKFLOW_PRESETS.get(preset_choice)
        if selected_preset:
            break
        else:
            print("Selección inválida. Por favor, elige un número de preset válido.")

    chain_definition = selected_preset["chain"]
    
    available_ais_info = {
        "gemini": {"func": get_gemini_response, "active": bool(gemini_model)},
        "openai": {"func": get_openai_response, "active": bool(openai_client)},
        # "claude": {"func": get_claude_response, "active": bool(claude_client)},
        # "deepseek": {"func": get_deepseek_response, "active": bool(deepseek_client)},
    }

    # Verificar que todas las IA en el preset seleccionado estén activas
    for step in chain_definition:
        ia_name = step["ia_name"]
        if ia_name not in available_ais_info or not available_ais_info[ia_name]["active"]:
            print(f"Error: La IA '{ia_name}' requerida por este preset no está configurada o activa. Volviendo al menú principal.")
            return

    initial_prompt = input("\nDame el prompt inicial para este flujo de trabajo: ")
    max_turns = len(chain_definition) # El número de turnos es el número de pasos en la cadena definida

    current_context = initial_prompt
    full_conversation_log = []

    print("\n--- Iniciando Conversación Encadenada ---")
    print(f"Pregunta inicial: {textwrap.fill(initial_prompt, width=80)}")

    for i, step_config in enumerate(chain_definition):
        if i >= max_turns:
            print("\n--- Máximo de turnos alcanzado. Finalizando cadena. ---")
            break

        ia_name = step_config["ia_name"]
        ia_system_instruction = step_config["system_instruction"] # NUEVO: La instrucción de sistema/persona
        ia_task_description = step_config["task_description"]     # NUEVO: La descripción de la tarea específica
        ia_func = available_ais_info[ia_name]["func"]

        # Construir el prompt para la IA actual
        # Ahora el prompt principal se enfoca en la pregunta del usuario y el contexto,
        # y la "tarea_específica" le dice qué hacer con eso.
        prompt_for_current_ia = (
            f"PREGUNTA INICIAL DEL USUARIO: '{initial_prompt}'\n\n"
            f"CONTEXTO PREVIO Y RESPUESTA ANTERIOR:\n{current_context}\n\n"
            f"TU TAREA ES: {ia_task_description}\n\n"
            "Genera tu respuesta o análisis."
        )

        print(f"\n=== Paso {i + 1}: {ia_name.upper()} (Tarea: {ia_task_description}) ===") # Muestra la tarea en el output
        print(f"Prompt enviado: '{textwrap.shorten(prompt_for_current_ia, width=100, placeholder='...')}'")

        # Se pasa la 'system_instruction' como system_prompt a la función de la IA
        response_text = await ia_func(prompt_for_current_ia, system_prompt=ia_system_instruction) 

        print(f"Respuesta de {ia_name.upper()}:\n{textwrap.fill(response_text, width=80)}")
        print(f"Longitud: {len(response_text)} caracteres")
        print("-" * 40)

        full_conversation_log.append({
            "ia_name": ia_name,
            "prompt_sent": prompt_for_current_ia,
            "response_text": response_text
        })
        current_context = response_text

        if i == len(chain_definition) - 1:
            print("\n--- Todas las IAs de la cadena definida han respondido. Finalizando cadena. ---")
            break

    print("\n--- Conversación Encadenada Finalizada ---")
    log_conversation(initial_prompt, full_conversation_log, mode="encadenada")
    print("Volviendo al menú principal.")


# --- 7. Función Principal de Ejecución (Asíncrona) ---
async def main():
    print("===================================")
    print("  Bienvenido a tu Multi-AI Communicator  ")
    print("===================================")
    print("Escribe 'salir' para terminar en cualquier momento.")

    print("\n--- Estado de Configuración ---")
    if gemini_model:
        print(f"✔️ Gemini: Listo (Modelo: {gemini_model.model_name})")
    else:
        print("❌ Gemini: No disponible")

    if openai_client:
        print("✔️ OpenAI: Listo (Modelo: gpt-3.5-turbo)")
    else:
        print("❌ OpenAI: No disponible")

    if claude_client:
        print("✔️ Claude: Listo")
    else:
        print("❌ Claude: No disponible (API Key no encontrada o error de configuración)")

    if deepseek_client:
        print("✔️ DeepSeek: Listo")
    else:
        print("❌ DeepSeek: No disponible (API Key no encontrada o error de configuración)")
    print("===================================")


    while True:
        print("\nElige un modo:")
        print("1. Modo de Comparación Directa (Mismo Prompt a todas las IA)")
        print("2. Modo de Conversación Encadenada (IA se pasan la respuesta)")
        print("   (Escribe 'salir' para terminar)")

        mode_choice = input("Selecciona un modo (1 o 2): ").strip()
        if mode_choice.lower() == 'salir':
            print("¡Hasta luego!")
            break

        if mode_choice == '1':
            user_prompt = input("\nTu pregunta para las IAs (Modo Comparación): ")
            if user_prompt.lower() == 'salir':
                print("¡Hasta luego!")
                break

            print("\n--- Obteniendo respuestas (Modo Comparación) ---")

            gemini_task = asyncio.create_task(get_gemini_response(user_prompt))
            openai_task = asyncio.create_task(get_openai_response(user_prompt))
            # claud_task = asyncio.create_task(get_claude_response(user_prompt))
            # deepseek_task = asyncio.create_task(get_deepseek_response(user_prompt))

            responses_list = await asyncio.gather(gemini_task, openai_task)

            all_responses = {
                "Gemini": responses_list[0],
                "OpenAI (ChatGPT)": responses_list[1],
                # "Anthropic (Claude)": responses_list[2],
                # "DeepSeek": responses_list[3],
            }

            print("\n================================")
            print("  Respuestas Recibidas (Modo Comparación) ")
            print("================================")
            for ia_name, response_text in all_responses.items():
                print(f"\n--- {ia_name} ---")
                print(textwrap.fill(response_text, width=80))
                print(f"Longitud: {len(response_text)} caracteres")
                print("-" * 30)

            log_conversation(user_prompt, all_responses, mode="comparacion")
            print("\n==============================")
            print("  Comparación Finalizada  ")
            print("==============================")

        elif mode_choice == '2':
            await run_chained_conversation()

        else:
            print("Opción no válida. Por favor, elige '1', '2' o 'salir'.")

# --- 8. Punto de entrada del script (Ejecución Asíncrona) ---
if __name__ == "__main__":
    asyncio.run(main())