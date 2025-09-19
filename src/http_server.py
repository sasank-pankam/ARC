import logging
import os
from pathlib import Path
from typing import Callable

from src.models import FeedBack
from src.notifier.__ws_notifier import WsNotifier
from . import log
from aiohttp import web
import re

LOCALHOST_ORIGIN_PATTERN = re.compile(r"^http://localhost(:\d+)?$")


@web.middleware
async def cors_middleware(request, handler):
    # Get Origin header (if any)
    origin = request.headers.get("Origin")

    # Handle preflight (OPTIONS) before reaching route handlers
    if request.method == "OPTIONS":
        response = web.Response(status=204)
    else:
        response = await handler(request)

    # Only apply CORS if the origin is from localhost
    if origin and LOCALHOST_ORIGIN_PATTERN.match(origin):
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"

    return response


logger = logging.getLogger(__name__)


class HTTPServer:
    def __init__(self, notifier: WsNotifier, fb_handler: Callable) -> None:
        self.app = web.Application(middlewares=[cors_middleware])
        self.fb_handler = fb_handler
        self.w_sockets = set()
        self.notifier = notifier
        self.app.add_routes(
            [
                web.post("/api/feedback", self.receive_feedback),
                web.get("/api/ws", self.web_socket_handler),
                web.delete("/api/batch", self.batch_delete_handler),
            ]
        )

        static_path = Path(os.getcwd()) / "dist"

        async def index(request):
            return web.FileResponse(static_path / "index.html")

        self.app.router.add_route("*", "/", index)
        self.app.router.add_static("/", path=static_path)

        self.runner = web.AppRunner(self.app)
        self.site = None

    async def listen(self):
        await self.runner.setup()
        host = "0.0.0.0"
        port = 8080
        self.site = web.TCPSite(self.runner, host=host, port=port)
        log.info(f"HTTPListener is running on http://{host}:{port}")
        await self.site.start()

    async def receive_feedback(self, request: web.Request):
        """Processes the feedback from json to custom Feedback type and sends to detector"""
        # add logic to change feedback to normal thing
        fb = FeedBack(await request.json())  # change

        if self.fb_handler:
            self.fb_handler(fb)

        return web.Response(status=200)

    async def batch_delete_handler(self, request: web.Request):
        gid = request.query.get("group_id")
        if gid is None:
            return
        await self.notifier.delete_group(gid)
        return web.Response(status=200)

    async def web_socket_handler(self, request: web.Request):
        logger.info("A new ws request arrived.")
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        logger.debug("Upgraded to websocket")
        self.w_sockets.add(ws)

        await self.notifier.add_wsocket(ws)
        logger.debug("sent all batches.")
        async for msg in ws:
            # if an incoming msg, then exit
            break

        await self.notifier.delete_websocket(ws)

        return ws

    async def close(self):
        log.info("Stopping http server.")
        await self.site.stop()
