from src.message_queue import BaseMessageQueue
import traceback
from . import log, BaseIngress
from aiohttp import web


class HTTPIngress(BaseIngress):
    def __init__(self, work_queue: BaseMessageQueue) -> None:
        super().__init__(work_queue)
        self.app = web.Application()
        self.app.add_routes(
            [
                web.post("/webhook/alerts", self.receive_alerts),
            ]
        )

        self.runner = web.AppRunner(self.app)
        self.site = None

    async def begin(self):
        await self.runner.setup()
        host = "0.0.0.0"
        port = 9090
        self.site = web.TCPSite(self.runner, host=host, port=port)
        log.info(f"HTTPListener is running on http://{host}:{port}")
        await self.site.start()

    async def receive_alerts(self, request: web.Request):
        try:
            alerts = await request.json()
        except Exception as e:
            log.error(
                "Http large payload cannot handle split the alerts.",
                extra={
                    "error": e,
                    "stack_trace": traceback.extract_tb(e.__traceback__),
                },
            )
            return web.json_response({"message": str(e)}, status=400)

        alerts = convert_to_alerts(alerts)
        log.debug(f"alerts are put to message queue lenght={len(alerts)}")
        self.mq.put_nowait(alerts)

        return web.json_response({"processing": True}, status=200)

    async def stop(self):
        await self.site.stop()


def convert_to_alerts(json_data):
    log.debug("Alert came processing it.", json_data)
    return json_data["alerts"]
