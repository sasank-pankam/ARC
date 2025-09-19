from abc import ABC
from src.graph import BaseGraph
from src.models import FeedBack
from src.message_queue import BaseMessageQueue
from src.models import Alert
from src.notifier import BaseNotifier
from src.storage import BaseAlertStore
from . import log


START_AT = "startsAt"


class BaseDetector(ABC):
    def __init__(
        self,
        graph: BaseGraph,
        work_queue: BaseMessageQueue,
        store: BaseAlertStore,
        notifier: BaseNotifier,
    ) -> None:
        self.service_graph = graph
        self.queue = work_queue
        self.store = store
        self.notifier = notifier
        self.notify_tasks = set()

    async def start(self):
        """this is the main func that needs to start and then listen for alerts and process it."""
        while True:
            batch = await self.queue.get()
            log.debug(f"consuming a alert batch from message queue length={len(batch)}")
            for raw in sorted(batch, key=lambda x: x[START_AT]):
                alert = Alert(raw)
                if alert.service == -1:
                    log.debug("debug cannot find this alert ")
                    continue
                placed = await self.store.put(alert.id, alert)
                if placed:
                    await self.process_alert(alert)

    async def process_alert(self, alert: Alert):
        pass

    async def feedback_handler(self, fb: FeedBack):
        pass
