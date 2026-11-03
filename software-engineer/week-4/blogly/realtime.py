"""Real-time updates: every connected browser gets new posts, comments and likes over a WebSocket."""
import asyncio
import json

from fastapi import WebSocket, WebSocketDisconnect


class Hub:
    def __init__(self, metrics, max_clients=500):
        self._clients: set[WebSocket] = set()
        self.metrics = metrics
        self.max_clients = max_clients
        self.loop = None

    async def connect(self, ws: WebSocket):
        if len(self._clients) >= self.max_clients:
            await ws.close(code=1013)  # try again later
            return False
        await ws.accept()
        self.loop = asyncio.get_running_loop()
        self._clients.add(ws)
        self.metrics.ws_clients.set(len(self._clients))
        return True

    def disconnect(self, ws: WebSocket):
        self._clients.discard(ws)
        self.metrics.ws_clients.set(len(self._clients))

    async def broadcast(self, message: dict):
        data = json.dumps(message)
        for ws in list(self._clients):
            try:
                await ws.send_text(data)
            except Exception:
                self.disconnect(ws)

    def publish(self, type_, **payload):
        """Called from sync route handlers (which FastAPI runs in a worker thread)."""
        self.metrics.events.labels(type_).inc()
        if self.loop is not None and self._clients:
            asyncio.run_coroutine_threadsafe(self.broadcast({"type": type_, **payload}), self.loop)

    async def serve(self, ws: WebSocket):
        if not await self.connect(ws):
            return
        try:
            await ws.send_text(json.dumps({"type": "hello", "clients": len(self._clients)}))
            while True:
                if await ws.receive_text() == "ping":  # keep-alive from the browser
                    await ws.send_text('{"type":"pong"}')
        except WebSocketDisconnect:
            pass
        finally:
            self.disconnect(ws)
