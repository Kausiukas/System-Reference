from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import asyncio
from typing import Dict, Any

# Lazy import to avoid heavy init at startup
from background_agents.ai_help.ai_help_agent import AIHelpAgent

app = FastAPI(title="AI Help Agent – Streaming API")

# Re-use a single agent instance for all websocket sessions
_agent: AIHelpAgent | None = None

async def get_agent() -> AIHelpAgent:
    global _agent
    if _agent is None:
        # NOTE: shared_state=None – the agent will fall back to internal mocks for this simple API.
        _agent = AIHelpAgent(shared_state=None)
        await _agent.initialize()
    return _agent


@app.websocket("/ws/help")
async def help_websocket(websocket: WebSocket):
    """Simple WebSocket endpoint that accepts a JSON payload::
        {"query": "..."}
    and streams the response back in small chunks so the client can render incrementally.
    """
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            query: str | None = data.get("query")
            if not query:
                await websocket.send_text("Error: `query` field missing")
                continue

            agent = await get_agent()
            # Currently process_help_request is sync wrapper – run in thread if needed
            loop = asyncio.get_running_loop()
            result: Dict[str, Any] = await loop.run_in_executor(None, agent.process_help_request, query)
            full_response: str = result.get("response", "") or result.get("error", "")

            # Chunk response by sentences to simulate streaming
            for sentence in full_response.split(". "):
                await websocket.send_text(sentence.strip() + ("." if not sentence.endswith(".") else ""))
                await asyncio.sleep(0.05)  # small delay so client can render progressively

            # Indicate completion
            await websocket.send_text("__END__")
    except WebSocketDisconnect:
        pass 