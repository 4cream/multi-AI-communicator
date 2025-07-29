# main.py

import os
import asyncio
import google.generativeai as genai
from openai import OpenAI
from dotenv import load_dotenv
import datetime # Para el timestamp del log

# --- 1. Cargar las variables de entorno ---
load_dotenv()

# --- 2. Obtener las API Keys del entorno (después de cargar .env) ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY") # Para futura expansión
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY") # Para futura expansión

# --- 3. Configurar las APIs con tus claves ---

# Gemini
gemini_model = None
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        PREFERRED_GEMINI_MODEL = 'models/gemini-1.5-pro-latest'

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
else:
    print("Advertencia: GEMINI_API_KEY no encontrada.")


# OpenAI
openai_client = None
if OPENAI_API_KEY:
    try:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
    except Exception as e:
        print(f"Error al configurar OpenAI: {e}")
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

# DeepSeek - Placeholder
deepseek_client = None
# if DEEPSEEK_API_KEY:
#     try:
#         # DeepSeek configuration (e.g., using OpenAI-compatible client with base_url)
#         # from openai import OpenAI as DeepSeekOpenAIClient
#         # deepseek_client = DeepSeekOpenAIClient(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com/v1")
#         pass # Remove this pass when implementing
#     except Exception as e:
#         print(f"Error al configurar DeepSeek: {e}")


# --- 4. Funciones Asíncronas para obtener respuestas de cada IA ---
# Todas las funciones de llamada a API se vuelven 'async'
async def get_gemini_response(prompt):
    if not gemini_model:
        return "Gemini no configurado o modelo no disponible."
    try:
        # Para llamadas asíncronas con google-generativeai, a menudo puedes usar el método directo
        # o, si no es inherentemente async, ejecutarlo en un thread pool (concurrent.futures)
        # Por ahora, asumimos que generate_content es suficientemente rápido o no bloquea el event loop.
        # Si tienes problemas, investigaríamos cómo hacer llamadas async explícitas con este SDK.
        response = gemini_model.generate_content(prompt)
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
        # OpenAI SDK soporta llamadas asíncronas con un cliente async
        # 'create' es síncrono por defecto en el cliente normal.
        # Para verdadera concurrencia, necesitaríamos `from openai import AsyncOpenAI`
        # Por ahora, lo mantenemos síncrono pero envuelto en async para el run.
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"OpenAI Error: {e}"

# Función para Claude (por implementar de forma async)
async def get_claude_response(prompt):
    if not claude_client:
        return "Claude no configurado."
    try:
        # IMPLEMENTACIÓN ASÍNCRONA DE CLAUDE AQUÍ
        # response = await claude_client.messages.create( ... )
        return "Claude: [IMPLEMENTAR ASÍNCRONO]"
    except Exception as e:
        return f"Claude Error: {e}"

# Función para DeepSeek (por implementar de forma async)
async def get_deepseek_response(prompt):
    if not deepseek_client:
        return "DeepSeek no configurado."
    try:
        # IMPLEMENTACIÓN ASÍNCRONA DE DEEPSEEK AQUÍ
        # response = await deepseek_client.chat.completions.create( ... )
        return "DeepSeek: [IMPLEMENTAR ASÍNCRONO]"
    except Exception as e:
        return f"DeepSeek Error: {e}"

# --- 5. Funciones Auxiliares ---
def log_conversation(prompt, responses):
    """Guarda la conversación en un archivo de log."""
    log_file_path = "conversation_log.txt"
    with open(log_file_path, "a", encoding="utf-8") as f:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"--- Consulta {timestamp} ---\n")
        f.write(f"Pregunta: {prompt}\n\n")
        for ia_name, response_text in responses.items():
            f.write(f"--- {ia_name} ---\n")
            f.write(f"{response_text}\n")
            f.write(f"Longitud: {len(response_text)} caracteres\n")
            f.write(f"{'-' * 30}\n\n")
        f.write("=" * 60 + "\n\n")
    print(f"Conversación guardada en {log_file_path}")


# --- 6. Función Principal de Ejecución (Asíncrona) ---
async def main():
    print("===================================")
    print("  Bienvenido a tu Multi-AI Communicator  ")
    print("===================================")
    print("Escribe 'salir' para terminar en cualquier momento.")

    # Mensajes de estado de configuración
    print("\n--- Estado de Configuración ---")
    if gemini_model:
        print(f"✔️ Gemini: Listo (Modelo: {gemini_model.model_name})")
    else:
        print("❌ Gemini: No disponible")

    if openai_client:
        print("✔️ OpenAI: Listo (Modelo: gpt-3.5-turbo)") # O el modelo configurado
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

            # Ejecutar todas las peticiones en paralelo
            # Aquí es donde 'asyncio.gather' es clave para la concurrencia.
            gemini_task = asyncio.create_task(get_gemini_response(user_prompt))
            openai_task = asyncio.create_task(get_openai_response(user_prompt))
            # claud_task = asyncio.create_task(get_claude_response(user_prompt)) # Descomentar cuando implementes
            # deepseek_task = asyncio.create_task(get_deepseek_response(user_prompt)) # Descomentar cuando implementes

            # Esperar a que todas las tareas se completen
            # responses = await asyncio.gather(gemini_task, openai_task, claud_task, deepseek_task) # Versión completa
            responses_list = await asyncio.gather(gemini_task, openai_task) # Versión actual

            all_responses = {
                "Gemini": responses_list[0],
                "OpenAI (ChatGPT)": responses_list[1],
                # "Anthropic (Claude)": responses_list[2], # Descomentar
                # "DeepSeek": responses_list[3],          # Descomentar
            }

            # Formatear y mostrar las respuestas
            print("\n================================")
            print("  Respuestas Recibidas (Modo Comparación) ")
            print("================================")
            for ia_name, response_text in all_responses.items():
                print(f"\n--- {ia_name} ---")
                print(f"{response_text}\n")
                print(f"Longitud: {len(response_text)} caracteres")
                print("-" * 30)

            log_conversation(user_prompt, all_responses)
            print("\n==============================")
            print("  Comparación Finalizada  ")
            print("==============================")

        elif mode_choice == '2':
            print("\n--- Modo de Conversación Encadenada (Funcionalidad por Implementar) ---")
            print("Este modo permitirá a las IA pasarse el contexto y refinar una solución.")
            print("Por ahora, es un placeholder. Volviendo al menú principal.")
            # Aquí iría la lógica más compleja para el Modo 2.
            # Podríamos pedir al usuario la IA inicial y el orden de la cadena.
            # Ej:
            # chain_order_input = input("Define el orden de las IAs (ej. Gemini,OpenAI,Claude): ")
            # chain = [ia.strip() for ia in chain_order_input.split(',')]
            #
            # current_context = input("Dame el prompt inicial para la cadena: ")
            # for ia_in_chain in chain:
            #     if ia_in_chain == "Gemini":
            #         response = await get_gemini_response(current_context)
            #     elif ia_in_chain == "OpenAI":
            #         response = await get_openai_response(current_context)
            #     # ... otros
            #     print(f"\n--- {ia_in_chain} Responde ---")
            #     print(response)
            #     current_context = response # La salida se convierte en la entrada siguiente

        else:
            print("Opción no válida. Por favor, elige '1', '2' o 'salir'.")

# --- 7. Punto de entrada del script (Ejecución Asíncrona) ---
if __name__ == "__main__":
    asyncio.run(main())