# main.py

import os
import google.generativeai as genai
from openai import OpenAI
from dotenv import load_dotenv

# --- 1. Cargar las variables de entorno ---
load_dotenv()

# --- 2. Obtener las API Keys del entorno (después de cargar .env) ---
# Es CRUCIAL que estas líneas estén aquí, ANTES de cualquier bloque 'if' que las use.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY") # Para futura expansión
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY") # Para futura expansión


# --- 3. Configurar las APIs con tus claves ---

# Gemini
gemini_model = None # Inicializamos el modelo a None
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)

        # Nombre del modelo Gemini a usar.
        PREFERRED_GEMINI_MODEL = 'models/gemini-1.5-pro-latest' # Tu elección

        # Verificar si el modelo preferido está disponible y soporta generateContent
        chosen_model_found = False
        print("\n--- Verificando Modelos de Gemini Disponibles ---")
        available_gemini_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_gemini_models.append(m.name)
                print(f"- {m.name}") # Imprime todos los modelos compatibles para referencia

        print("-----------------------------------")

        if PREFERRED_GEMINI_MODEL in available_gemini_models:
            gemini_model = genai.GenerativeModel(PREFERRED_GEMINI_MODEL)
            chosen_model_found = True
            print(f"Gemini configurado con éxito usando: {PREFERRED_GEMINI_MODEL}")
        else:
            gemini_model = None
            print(f"Advertencia: El modelo preferido '{PREFERRED_GEMINI_MODEL}' no se encontró o no soporta generateContent.")
            print("Intentando buscar el primer modelo Gemini compatible con generateContent...")
            # Si el modelo preferido no funciona, intenta encontrar cualquier otro modelo Gemini válido.
            for model_name in available_gemini_models:
                if 'gemini' in model_name.lower(): # Busca cualquier modelo que contenga 'gemini'
                    print(f"Usando el modelo alternativo: {model_name}")
                    gemini_model = genai.GenerativeModel(model_name)
                    chosen_model_found = True
                    break
            if not chosen_model_found:
                print("No se encontró ningún modelo Gemini compatible. Gemini no estará disponible.")

    except Exception as e:
        print(f"Error al configurar Gemini: {e}")
        gemini_model = None
else:
    print("Advertencia: GEMINI_API_KEY no encontrada. Gemini no estará disponible.")


# OpenAI
openai_client = None # Inicializamos el cliente a None
if OPENAI_API_KEY:
    try:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        print("OpenAI (ChatGPT) configurado con éxito.")
    except Exception as e:
        print(f"Error al configurar OpenAI: {e}")
        openai_client = None
else:
    print("Advertencia: OPENAI_API_KEY no encontrada. OpenAI (ChatGPT) no estará disponible.")

# Anthropic (Claude) - Descomentar y configurar cuando tengas la clave
claude_client = None
# if CLAUDE_API_KEY:
#     try:
#         from anthropic import Anthropic
#         claude_client = Anthropic(api_key=CLAUDE_API_KEY)
#         print("Anthropic (Claude) configurado con éxito.")
#     except Exception as e:
#         print(f"Error al configurar Anthropic: {e}")
#         claude_client = None
# else:
#     print("Advertencia: CLAUDE_API_KEY no encontrada. Claude no estará disponible.")

# DeepSeek - Descomentar y configurar cuando tengas la clave
deepseek_client = None
# if DEEPSEEK_API_KEY:
#     try:
#         # La configuración de DeepSeek dependerá de su API.
#         # Podría ser similar a OpenAI si tienen un SDK o una URL base.
#         # from openai import OpenAI as DeepSeekOpenAIClient # Renombramos para evitar conflicto
#         # deepseek_client = DeepSeekOpenAIClient(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com/v1")
#         print("DeepSeek configurado con éxito. (Verificar implementación manual)")
#     except Exception as e:
#         print(f"Error al configurar DeepSeek: {e}")
#         deepseek_client = None
# else:
#     print("Advertencia: DEEPSEEK_API_KEY no encontrada. DeepSeek no estará disponible.")


# --- 4. Funciones para obtener respuestas de cada IA ---

def get_gemini_response(prompt):
    if not gemini_model:
        return "Gemini no configurado o modelo no disponible."
    try:
        response = gemini_model.generate_content(prompt)
        if response.candidates and response.candidates[0].content.parts:
            return response.candidates[0].content.parts[0].text
        else:
            return "Gemini: No se pudo obtener una respuesta textual (posiblemente contenido bloqueado o vacío)."
    except Exception as e:
        return f"Gemini Error: {e}"

def get_openai_response(prompt):
    if not openai_client:
        return "OpenAI no configurado."
    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo", # Puedes cambiar a "gpt-4o", "gpt-4-turbo", etc. si tienes acceso
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"OpenAI Error: {e}"

# Función para Claude (por implementar)
def get_claude_response(prompt):
    if not claude_client:
        return "Claude no configurado."
    try:
        # IMPLEMENTACIÓN DE CLAUDE AQUÍ
        # response = claude_client.messages.create(
        #     model="claude-3-opus-20240229",
        #     max_tokens=1024,
        #     messages=[
        #         {"role": "user", "content": prompt}
        #     ]
        # )
        # return response.content[0].text
        return "Claude: [IMPLEMENTAR]" # Placeholder
    except Exception as e:
        return f"Claude Error: {e}"

# Función para DeepSeek (por implementar)
def get_deepseek_response(prompt):
    if not deepseek_client:
        return "DeepSeek no configurado."
    try:
        # IMPLEMENTACIÓN DE DEEPSEEK AQUÍ
        # Si DeepSeek es compatible con la API de OpenAI (usando `base_url`):
        # response = deepseek_client.chat.completions.create(
        #     model="deepseek-chat", # O el nombre del modelo de DeepSeek
        #     messages=[
        #         {"role": "user", "content": prompt}
        #     ]
        # )
        # return response.choices[0].message.content
        return "DeepSeek: [IMPLEMENTAR]" # Placeholder
    except Exception as e:
        return f"DeepSeek Error: {e}"


# --- 5. Función Principal de Ejecución ---
def main():
    print("===================================")
    print("  Bienvenido a tu Multi-AI Communicator  ")
    print("===================================")
    print("Escribe 'salir' para terminar en cualquier momento.")

    # Mensajes de estado de configuración
    if gemini_model:
        print("✔️ Gemini: Listo")
    else:
        print("❌ Gemini: No disponible")
    
    if openai_client:
        print("✔️ OpenAI: Listo")
    else:
        print("❌ OpenAI: No disponible")

    if claude_client:
        print("✔️ Claude: Listo")
    else:
        print("❌ Claude: No disponible") # Ocultar si no se ha intentado configurar aún
    
    if deepseek_client:
        print("✔️ DeepSeek: Listo")
    else:
        print("❌ DeepSeek: No disponible") # Ocultar si no se ha intentado configurar aún

    print("===================================")


    while True:
        user_prompt = input("\nTu pregunta para las IAs (o 'salir'): ")
        if user_prompt.lower() == 'salir':
            print("¡Hasta luego!")
            break

        print("\n--- Obteniendo respuestas ---")

        # Petición a Gemini
        print("\n=== [Gemini] ===")
        gemini_response = get_gemini_response(user_prompt)
        print(gemini_response)

        # Petición a OpenAI (ChatGPT)
        print("\n=== [OpenAI (ChatGPT)] ===")
        openai_response = get_openai_response(user_prompt)
        print(openai_response)

        # Petición a Anthropic (Claude) - Descomentar cuando implementes
        # print("\n=== [Anthropic (Claude)] ===")
        # claude_response = get_claude_response(user_prompt)
        # print(claude_response)

        # Petición a DeepSeek - Descomentar cuando implementes
        # print("\n=== [DeepSeek] ===")
        # deepseek_response = get_deepseek_response(user_prompt)
        # print(deepseek_response)

        print("\n==============================")
        print("  Respuestas Recibidas  ")
        print("==============================")

# --- 6. Punto de entrada del script ---
if __name__ == "__main__":
    main()