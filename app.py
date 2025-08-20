# app.py

from flask import Flask, render_template, Response, request
import asyncio
import json
from urllib.parse import unquote
from ai_core import get_gemini_response_stream, get_openai_response_stream, WORKFLOW_PRESETS

app = Flask(__name__)

AI_FUNCTIONS = {
    "gemini": get_gemini_response_stream,
    "openai": get_openai_response_stream
}

@app.route('/')
def index():
    return render_template('index.html', presets=WORKFLOW_PRESETS)


async def stream_merger(prompt, mode, preset_key=None):
    if mode == 'comparison':
        queue = asyncio.Queue()
        async def forward_stream(gen_func, p):
            async for item in gen_func(p):
                await queue.put(item)
            await queue.put({"status": "one_stream_done"})

        asyncio.create_task(forward_stream(get_gemini_response_stream, prompt))
        asyncio.create_task(forward_stream(get_openai_response_stream, prompt))
        
        finished_streams = 0
        while finished_streams < 2:
            item = await queue.get()
            if item.get("status") == "one_stream_done":
                finished_streams += 1
            else:
                yield item

    elif mode == 'chained':
        preset = WORKFLOW_PRESETS.get(preset_key)
        if not preset:
            yield {"error": "Preset no válido."}
            return

        current_context = prompt
        
        for i, step in enumerate(preset['chain']):
            ia_name = step['ia_name']
            ia_func = AI_FUNCTIONS.get(ia_name)
            step_number = i + 1
            
            if not ia_func:
                yield {"ai": ia_name, "error": f"Función para {ia_name} no encontrada.", "step": step_number}
                continue

            yield {"status": "step_start", "step": step_number, "ai": ia_name, "task": step['task_description']}
            
            step_prompt = f"Contexto previo: '{current_context}'\n\nTu tarea específica es: '{step['task_description']}'"
            if i == 0:
                step_prompt = f"Pregunta inicial del usuario: '{prompt}'\n\nTu tarea específica es: '{step['task_description']}'"

            full_step_response = ""
            # --- ¡¡¡CAMBIO CLAVE AQUÍ!!! ---
            # Añadimos el número de paso a cada chunk que retransmitimos.
            async for chunk in ia_func(step_prompt):
                chunk['step'] = step_number 
                yield chunk
                
                if chunk.get("full_text"):
                    full_step_response += chunk["full_text"]
                elif chunk.get("text"):
                    full_step_response += chunk["text"]
            
            current_context = full_step_response

    yield {"status": "all_done"}


@app.route('/api/stream_query')
def stream_query():
    prompt = unquote(request.args.get('prompt', ''))
    mode = request.args.get('mode', '')
    preset_key = request.args.get('preset', '')
    
    def generate_sync_bridge():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        async_gen = stream_merger(prompt, mode, preset_key)
        try:
            while True:
                chunk = loop.run_until_complete(async_gen.__anext__())
                yield f"data: {json.dumps(chunk)}\n\n"
        except StopAsyncIteration:
            pass
        finally:
            loop.close()

    return Response(generate_sync_bridge(), mimetype='text/event-stream')


if __name__ == '__main__':
    app.run(debug=True)