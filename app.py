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
    # --- LÓGICA NUEVA PARA ACUMULAR RESULTADOS ---
    final_results = {}

    if mode == 'comparison':
        queue = asyncio.Queue()
        async def forward_stream(gen_func, p):
            ai_name = "Gemini" if gen_func.__name__ == "get_gemini_response_stream" else "OpenAI"
            final_results[ai_name] = "" # Inicializamos el acumulador
            
            async for item in gen_func(p):
                # Acumulamos el texto de cada chunk
                if item.get("full_text"): final_results[ai_name] += item["full_text"]
                elif item.get("text"): final_results[ai_name] += item["text"]
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
        final_results['steps'] = []
        
        for i, step in enumerate(preset['chain']):
            ia_name = step['ia_name']
            ia_func = AI_FUNCTIONS.get(ia_name)
            step_number = i + 1
            
            yield {"status": "step_start", "step": step_number, "ai": ia_name, "task": step['task_description']}
            
            step_prompt = f"Contexto previo: '{current_context}'" if i > 0 else f"Pregunta inicial: '{prompt}'"
            step_prompt += f"\n\nTu tarea específica es: '{step['task_description']}'"

            full_step_response = ""
            async for chunk in ia_func(step_prompt):
                chunk['step'] = step_number
                yield chunk
                
                if chunk.get("full_text"): full_step_response += chunk["full_text"]
                elif chunk.get("text"): full_step_response += chunk["text"]
            
            current_context = full_step_response
            final_results['steps'].append({"ai": ia_name, "response": full_step_response})
    
    # --- MENSAJE FINAL MEJORADO ---
    # Enviamos los resultados completos para que el frontend los guarde.
    yield {"status": "all_done", "final_results": final_results}


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