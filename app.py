# app.py

from flask import Flask, render_template, request, jsonify
import asyncio
# Asegúrate de que ai_core.py está en la misma carpeta
from ai_core import run_comparison_mode, run_chain_mode, WORKFLOW_PRESETS

app = Flask(__name__)

# Esta ruta solo se encarga de mostrar la página web inicial.
@app.route('/')
def index():
    # Pasamos los presets a la plantilla para que el menú desplegable se construya
    return render_template('index.html', presets=WORKFLOW_PRESETS)


# Esta es nuestra nueva ruta de API. Solo se comunica con datos (JSON).
@app.route('/api/query', methods=['POST'])
def api_query():
    data = request.get_json()
    prompt = data.get('prompt')
    mode = data.get('mode')

    if not prompt or not mode:
        return jsonify({"error": "Faltan 'prompt' o 'mode' en la solicitud."}), 400

    results = {}
    if mode == 'comparison':
        # asyncio.run() ejecuta nuestra función asíncrona
        results = asyncio.run(run_comparison_mode(prompt))
    
    elif mode == 'chained':
        preset_key = data.get('preset')
        if not preset_key:
            return jsonify({"error": "Falta 'preset' para el modo encadenado."}), 400
        results = asyncio.run(run_chain_mode(prompt, preset_key))

    return jsonify(results)


if __name__ == '__main__':
    app.run(debug=True)