# app.py

from flask import Flask, render_template, request
import asyncio
from ai_core import run_comparison_mode, run_chain_mode, WORKFLOW_PRESETS

app = Flask(__name__)

# Asegurarnos de que las IAs se configuren al iniciar la app
# (Las impresiones de configuración de ai_core.py aparecerán en la consola aquí)

@app.route('/', methods=['GET', 'POST'])
def index():
    results = None
    if request.method == 'POST':
        prompt = request.form['prompt']
        mode = request.form['mode']

        if mode == 'comparison':
            # asyncio.run() ejecuta nuestra función async desde un entorno síncrono (Flask)
            results = asyncio.run(run_comparison_mode(prompt))
        
        elif mode == 'chained':
            preset_key = request.form['preset']
            results = asyncio.run(run_chain_mode(prompt, preset_key))

    # Pasamos la lista de presets a la plantilla para poder mostrarlos en un dropdown
    return render_template('index.html', results=results, presets=WORKFLOW_PRESETS)

if __name__ == '__main__':
    app.run(debug=True)