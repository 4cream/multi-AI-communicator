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

# Gemini (CAMBIOS AQUÍ)
gemini_model = None
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        PREFERRED_GEMINI_MODEL = 'models/gemini-2.5-flash-lite' 

        chosen_model_found = False
        available_gemini_models = []
        print("\n--- Verificando Modelos de Gemini Disponibles ---") # Debugging
        for m in genai.list_models():
            # Simplificamos la verificación. Si soporta generateContent, debería funcionar para texto.
            # Los modelos más nuevos (1.5/2.5) suelen soportar chat a través de generateContent.
            if 'generateContent' in m.supported_generation_methods: 
                available_gemini_models.append(m.name)
                print(f"- {m.name}") # Mostrar todos los compatibles encontrados

        print("-----------------------------------") # Debugging

        if PREFERRED_GEMINI_MODEL in available_gemini_models:
            gemini_model = genai.GenerativeModel(PREFERRED_GEMINI_MODEL)
            chosen_model_found = True
            print(f"Gemini configurado con éxito usando: {gemini_model.model_name}")
        else:
            # Si el modelo preferido no se encontró o no soporta generateContent, buscar un alternativo
            print(f"Advertencia: El modelo preferido '{PREFERRED_GEMINI_MODEL}' no se encontró o no soporta generateContent.")
            for model_name in available_gemini_models:
                if 'gemini' in model_name.lower(): # Buscamos cualquier modelo Gemini que funcione
                    gemini_model = genai.GenerativeModel(model_name)
                    chosen_model_found = True
                    print(f"Usando modelo alternativo: {model_name}")
                    break
            
            if not chosen_model_found:
                print(f"Error: No se encontró ningún modelo Gemini compatible. Gemini no estará disponible.")

    except Exception as e:
        print(f"Error al configurar Gemini: {e}")
        gemini_model = None # Asegurarse de que sea None en caso de error
else:
    print("Advertencia: GEMINI_API_KEY no encontrada.")


# OpenAI (No hay cambios significativos aquí)
openai_client = None
if OPENAI_API_KEY:
    try:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
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
#     except Exception as e:
#         print(f"Error al configurar Anthropic: {e}")
#         claude_client = None

# DeepSeek - Placeholder
deepseek_client = None
# if DEEPSEEK_API_KEY:
#     try:
#         # from openai import OpenAI as DeepSeekOpenAIClient
#         # deepseek_client = DeepSeekOpenAIClient(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com/v1")
#         pass
#     except Exception as e:
#         print(f"Error al configurar DeepSeek: {e}")
#         deepseek_client = None


# --- 4. Funciones Asíncronas para obtener respuestas de cada IA (usan asyncio.to_thread) ---

# Gemini (Revertimos a un enfoque más simple para el system_prompt en generate_content)
async def get_gemini_response(prompt, system_prompt=None):
    if not gemini_model:
        return "Gemini no configurado o modelo no disponible."
    try:
        # Para modelos Gemini 1.5/2.5 con generate_content y system_prompt,
        # la forma más robusta es inyectar el system_prompt directamente en el prompt.
        # Crear una nueva sesión de chat temporal por cada llamada es costoso
        # y no es el uso principal de generate_content.
        
        full_prompt = prompt
        if system_prompt:
            # Una forma efectiva de infundir el rol es al principio del prompt
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

# Función para Claude (por implementar de forma async usando asyncio.to_thread)
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

# Función para DeepSeek (por implementar de forma async usando asyncio.to_thread)
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

# --- 6. Función para el Modo de Conversación Encadenada ---
async def run_chained_conversation():
    print("\n--- Modo de Conversación Encadenada ---")
    print("Este modo permite encadenar IAs, pasando la salida de una como entrada a la siguiente.")
    print("Cada IA puede tener un 'rol' específico para guiar su respuesta.")

    available_ais_info = {
        "gemini": {"func": get_gemini_response, "active": bool(gemini_model)},
        "openai": {"func": get_openai_response, "active": bool(openai_client)},
        # "claude": {"func": get_claude_response, "active": bool(claude_client)},
        # "deepseek": {"func": get_deepseek_response, "active": bool(deepseek_client)},
    }

    active_ais_names = [name for name, info in available_ais_info.items() if info["active"]]

    if not active_ais_names:
        print("¡Atención! No hay IAs configuradas y disponibles para el modo encadenado.")
        return

    print(f"IAs activas para la cadena: {', '.join(active_ais_names)}")

    print("\nDefine tu cadena de IA y sus roles. Ejemplo:")
    print("  Gemini:Analiza la idea y genera preguntas clave.")
    print("  OpenAI:Responde a las preguntas clave basándose en el análisis anterior.")
    print("  (Escribe 'salir' para terminar la configuración de la cadena)")

    chain_definition = []
    step_num = 1
    while True:
        step_input = input(f"Paso {step_num} (IA_nombre:Rol_o_Instruccion, ej. Gemini:Analista, o 'salir'): ").strip()
        if step_input.lower() == 'salir':
            break

        if ':' not in step_input:
            print("Formato incorrecto. Usa IA_nombre:Rol_o_Instruccion.")
            continue

        ia_name, role = step_input.split(':', 1)
        ia_name = ia_name.lower().strip()
        role = role.strip()

        if ia_name not in active_ais_names:
            print(f"Error: '{ia_name}' no es una IA activa o válida. Intenta de nuevo.")
            continue

        chain_definition.append({"ia_name": ia_name, "role": role})
        step_num += 1

    if not chain_definition:
        print("No se definió ninguna cadena. Volviendo al menú principal.")
        return

    initial_prompt = input("\nDame el prompt inicial para la cadena: ")
    max_turns_input = input("Máximo de turnos en la cadena (Enter para 5 turnos): ")
    max_turns = int(max_turns_input) if max_turns_input.isdigit() else 5

    current_context = initial_prompt
    full_conversation_log = []

    print("\n--- Iniciando Conversación Encadenada ---")
    print(f"Pregunta inicial: {textwrap.fill(initial_prompt, width=80)}")

    for i, step_config in enumerate(chain_definition):
        if i >= max_turns:
            print("\n--- Máximo de turnos alcanzado. Finalizando cadena. ---")
            break

        ia_name = step_config["ia_name"]
        ia_role = step_config["role"]
        ia_func = available_ais_info[ia_name]["func"]

        # Construir el prompt para la IA actual
        prompt_for_current_ia = (
            f"La pregunta original que inició el proceso es: '{initial_prompt}'\n\n"
            f"Tu rol en este paso de la conversación es: {ia_role}\n\n"
            f"El contexto y la información recibida del paso anterior es:\n{current_context}\n\n"
            "Basándote en todo lo anterior, genera tu respuesta o análisis."
        )

        print(f"\n=== Paso {i + 1}: {ia_name} (Rol: {ia_role}) ===")
        print(f"Prompt enviado: '{textwrap.shorten(prompt_for_current_ia, width=100, placeholder='...')}'")

        response_text = await ia_func(prompt_for_current_ia, system_prompt=ia_role)

        print(f"Respuesta de {ia_name}:\n{textwrap.fill(response_text, width=80)}")
        print(f"Longitud: {len(response_text)} caracteres")
        print("-" * 40)

        full_conversation_log.append({
            "ia_name": ia_name,
            "prompt_sent": prompt_for_current_ia,
            "response_text": response_text
        })
        current_context = response = response_text

        if i < len(chain_definition) -1:
            continue_choice = input("¿Continuar al siguiente paso en la cadena? (s/n, o Enter para continuar): ").lower().strip()
            if continue_choice == 'n':
                print("\n--- Usuario decidió finalizar la cadena. ---")
                break
        else:
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