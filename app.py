# app.py
from flask import Flask, render_template, Response, request
import asyncio
import json
from urllib.parse import unquote
from ai_core import get_gemini_response_stream, get_openai_response_stream, WORKFLOW_PRESETS

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html', presets=WORKFLOW_PRESETS)

async def stream_merger(prompt):
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
    
    # --- MENSAJE FINAL ---
    # Cuando ambos streams han terminado, enviamos un último mensaje.
    yield {"status": "all_done"}

@app.route('/api/stream_query')
def stream_query():
    prompt = unquote(request.args.get('prompt', ''))
    
    def generate_sync_bridge():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        async_gen = stream_merger(prompt)
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