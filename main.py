# main.py

import os
import asyncio
import google.generativeai as genai
from openai import OpenAI  # <--- Importamos la versión SÍNCRONA de OpenAI
from dotenv import load_dotenv
import datetime
import textwrap

# --- 1. Cargar las variables de entorno ---
load_dotenv()

# --- 2. Obtener las API Keys del entorno (después de cargar .env) ---
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
                if 'gemini' in model_name.lower():
                    gemini_model = genai.GenerativeModel(model_name)
                    chosen_model_found = True
                    break
    except Exception as e:
        print(f"Error al configurar Gemini: {e}")
        gemini_model = None # Asegurarse de que sea None en caso de error
else:
    print("Advertencia: GEMINI_API_KEY no encontrada.")


# OpenAI
openai_client = None
if OPENAI_API_KEY:
    try:
        # Aquí se crea la instancia del cliente SÍNCRONO de OpenAI
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
    except Exception as e:
        print(f"Error al configurar OpenAI: {e}")
        openai_client = None # Asegurarse de que sea None en caso de error
else:
    print("Advertencia: OPENAI_API_KEY no encontrada.")


# Anthropic (Claude) - Placeholder
claude_client = None
# if CLAUDE_API_KEY:
#     try:
#         from anthropic import Anthropic # Usar la versión síncrona por simplicidad
#         claude_client = Anthropic(api_key=CLAUDE_API_KEY)
#     except Exception as e:
#         print(f"Error al configurar Anthropic: {e}")
#         claude_client = None

# DeepSeek - Placeholder
deepseek_client = None
# if DEEPSEEK_API_KEY:
#     try:
#         # DeepSeek configuration (e.g., using OpenAI-compatible client with base_url)
#         # from openai import OpenAI as DeepSeekOpenAIClient # Usar la versión síncrona
#         # deepseek_client = DeepSeekOpenAIClient(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com/v1")
#         pass
#     except Exception as e:
#         print(f"Error al configurar DeepSeek: {e}")
#         deepseek_client = None


# --- 4. Funciones Asíncronas para obtener respuestas de cada IA (usan asyncio.to_thread) ---

async def get_gemini_response(prompt):
    if not gemini_model:
        return "Gemini no configurado o modelo no disponible."
    try:
        # Ejecuta la llamada síncrona en un hilo separado para no bloquear el bucle de eventos
        response = await asyncio.to_thread(gemini_model.generate_content, prompt)
        if response.candidates and response.candidates[0].content.parts:
            return response.candidates[0].content.parts[0].text
        else:
            return "Gemini: No se pudo obtener una respuesta textual (posiblemente contenido bloqueado o vacío)."
    except Exception as e:
        return f"Gemini Error: {e}"

async def get_openai_response(prompt):
    if not openai_client:
        return "OpenAI no configurado."
    try:
        # Ejecuta la llamada síncrona en un hilo separado
        response = await asyncio.to_thread(
            openai_client.chat.completions.create, # Pasamos la función
            model="o4-mini-2025-04-16",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"OpenAI Error: {e}"

# Función para Claude (por implementar de forma async usando asyncio.to_thread)
async def get_claude_response(prompt):
    if not claude_client:
        return "Claude no configurado."
    try:
        # IMPLEMENTACIÓN ASÍNCRONA DE CLAUDE AQUÍ usando await asyncio.to_thread
        # response = await asyncio.to_thread(
        #     claude_client.messages.create,
        #     model="claude-3-opus-20240229",
        #     max_tokens=1024,
        #     messages=[
        #         {"role": "user", "content": prompt}
        #     ]
        # )
        # return response.content[0].text
        return "Claude: [IMPLEMENTAR ASÍNCRONO]" # Placeholder
    except Exception as e:
        return f"Claude Error: {e}"

# Función para DeepSeek (por implementar de forma async usando asyncio.to_thread)
async def get_deepseek_response(prompt):
    if not deepseek_client:
        return "DeepSeek no configurado."
    try:
        # IMPLEMENTACIÓN ASÍNCRONA DE DEEPSEEK AQUÍ usando await asyncio.to_thread
        # response = await asyncio.to_thread(
        #     deepseek_client.chat.completions.create, # O la función de tu cliente DeepSeek
        #     model="deepseek-chat",
        #     messages=[
        #         {"role": "user", "content": prompt}
        #     ]
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
            for i, (ia_name, step_prompt, response_text) in enumerate(responses):
                f.write(f"--- Paso {i+1}: {ia_name} ---\n")
                f.write(f"Prompt recibido: {textwrap.fill(step_prompt, width=80)}\n")
                f.write(f"Respuesta: {textwrap.fill(response_text, width=80)}\n")
                f.write(f"Longitud: {len(response_text)} caracteres\n")
                f.write(f"{'-' * 30}\n\n")

        f.write("=" * 60 + "\n\n")
    print(f"Conversación guardada en {log_file_path}")

# --- 6. Función para el Modo de Conversación Encadenada ---
async def run_chained_conversation():
    print("\n--- Modo de Conversación Encadenada ---")
    print("Define el orden de las IAs para la cadena (ej. Gemini,OpenAI).")

    available_ais_map = {
        "gemini": get_gemini_response,
        "openai": get_openai_response,
        # "claude": get_claude_response,
        # "deepseek": get_deepseek_response,
    }

    active_ais = {}
    if gemini_model: active_ais["gemini"] = get_gemini_response
    if openai_client: active_ais["openai"] = get_openai_response
    # if claude_client: active_ais["claude"] = get_claude_response
    # if deepseek_client: active_ais["deepseek"] = get_deepseek_response

    if not active_ais:
        print("¡Atención! No hay IAs configuradas y disponibles para el modo encadenado.")
        return

    print(f"IAs activas para la cadena: {', '.join(active_ais.keys())}")

    chain_order_input = input("Ingresa el orden de las IAs (separadas por coma, ej. Gemini,OpenAI): ").lower().strip()
    chain = [ia.strip() for ia in chain_order_input.split(',')]

    valid_chain = []
    for ia_name in chain:
        if ia_name in active_ais:
            valid_chain.append((ia_name, active_ais[ia_name]))
        else:
            print(f"Advertencia: '{ia_name}' no es una IA válida o no está configurada. Ignorando.")

    if not valid_chain:
        print("La cadena no contiene IAs válidas. Volviendo al menú principal.")
        return

    initial_prompt = input("Dame el prompt inicial para la cadena: ")
    max_turns_input = input("Máximo de turnos en la cadena (ej. 3, Enter para ilimitado): ")
    max_turns = int(max_turns_input) if max_turns_input.isdigit() else None

    current_context = initial_prompt
    conversation_history = []
    turn_count = 0

    print("\n--- Iniciando Conversación Encadenada ---")
    while True:
        if max_turns is not None and turn_count >= max_turns:
            print("\n--- Máximo de turnos alcanzado. Finalizando cadena. ---")
            break

        if not valid_chain:
            print("\n--- Todas las IAs de la cadena han respondido. Finalizando cadena. ---")
            break

        current_ia_name, current_ia_func = valid_chain[turn_count % len(valid_chain)]

        print(f"\n=== Turno {turn_count + 1}: {current_ia_name} procesando ===")
        print(f"Prompt enviado: '{textwrap.shorten(current_context, width=100, placeholder='...')}'")

        response_text = await current_ia_func(current_context)

        print(f"Respuesta de {current_ia_name}:\n{textwrap.fill(response_text, width=80)}")
        print(f"Longitud: {len(response_text)} caracteres")
        print("-" * 40)

        conversation_history.append((current_ia_name, current_context, response_text))
        current_context = response_text

        turn_count += 1

        if len(response_text.strip()) < 10 and turn_count > 1:
             print("\n--- Respuesta muy corta. Asumiendo fin de cadena. ---")
             break

        continue_choice = input("¿Continuar la cadena? (s/n, o Enter para continuar): ").lower().strip()
        if continue_choice == 'n':
            print("\n--- Usuario decidió finalizar la cadena. ---")
            break

    print("\n--- Conversación Encadenada Finalizada ---")
    log_conversation(initial_prompt, conversation_history, mode="encadenada")
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
        print("✔️ OpenAI: Listo (Modelo: o4-mini-2025-04-16)")
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