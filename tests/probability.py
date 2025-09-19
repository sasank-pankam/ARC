import asyncio
import itertools
import json
from pathlib import Path
import _path
import logging
from src.message_queue import AsyncQueue
from src.graph import ServiceGraph
from src.models import Alert
from src.storage import DictStore
from src.preprocessing.causal_inference import batch_alerts, compute_alpha_beta_links
from src.detector import ProbabilityDetector
from src.notifier import BaseNotifier, ConsoleNotifier
from src.models import AlertGroup

_path.thing = None  # this is to make sure the import is not removed.

data_path = Path(__file__).parent.parent / "test_data/data"

log = logging.getLogger(__package__)

graph = ServiceGraph("test_data/test_service_map.yaml")
pattren = batch_alerts(
    list(
        map(
            Alert,
            [
                {
                    "labels": {
                        "job": "product-catalog-service",
                        "instance": "1",
                        "severity": "critical",
                    },
                    "startsAt": "2027-02-01T15:07:56.789624",
                    "endsAt": "2027-02-01T15:09:56.789624",
                    "status": "firing",
                    "annotations": {
                        "description": "Metadata sync delay",
                        "summary": "'database instance 1 down'",
                    },
                },
                {
                    "labels": {
                        "job": "inventory-service",
                        "instance": "1",
                        "severity": "critical",
                    },
                    "startsAt": "2027-02-01T15:08:31.789624",
                    "endsAt": "2027-02-01T15:10:31.789624",
                    "status": "firing",
                    "annotations": {
                        "description": "Stock consistency warning",
                        "summary": "'database instance 1 down'",
                    },
                },
                {
                    "labels": {
                        "job": "shipping-service",
                        "instance": "2",
                        "severity": "critical",
                    },
                    "startsAt": "2027-02-01T15:09:36.789624",
                    "endsAt": "2027-02-01T15:11:36.789624",
                    "status": "firing",
                    "annotations": {
                        "description": "Carrier API failure surge",
                        "summary": "'database instance 1 down'",
                    },
                },
                {
                    "labels": {
                        "job": "user-service",
                        "instance": "2",
                        "severity": "critical",
                    },
                    "startsAt": "2027-02-01T15:39:56.789624",
                    "endsAt": "2027-02-01T15:41:56.789624",
                    "status": "firing",
                    "annotations": {
                        "description": "Session latency high",
                        "summary": "'database instance 1 down'",
                    },
                },
                {
                    "labels": {
                        "job": "recommendation-service",
                        "instance": "1",
                        "severity": "critical",
                    },
                    "startsAt": "2027-02-01T15:40:13.789624",
                    "endsAt": "2027-02-01T15:42:13.789624",
                    "status": "firing",
                    "annotations": {
                        "description": "Recommendation latency warning",
                        "summary": "'database instance 1 down'",
                    },
                },
                {
                    "labels": {
                        "job": "user-service",
                        "instance": "2",
                        "severity": "critical",
                    },
                    "startsAt": "2027-02-01T16:16:56.789624",
                    "endsAt": "2027-02-01T16:18:56.789624",
                    "status": "firing",
                    "annotations": {
                        "description": "Session latency high",
                        "summary": "'database instance 1 down'",
                    },
                },
                {
                    "labels": {
                        "job": "recommendation-service",
                        "instance": "1",
                        "severity": "critical",
                    },
                    "startsAt": "2027-02-01T16:17:22.789624",
                    "endsAt": "2027-02-01T16:19:22.789624",
                    "status": "firing",
                    "annotations": {
                        "description": "Recommendation latency warning",
                        "summary": "'database instance 1 down'",
                    },
                },
                {
                    "labels": {
                        "job": "user-service",
                        "instance": "2",
                        "severity": "critical",
                    },
                    "startsAt": "2027-02-01T16:17:43.789624",
                    "endsAt": "2027-02-01T16:19:43.789624",
                    "status": "firing",
                    "annotations": {
                        "description": "Session latency high",
                        "summary": "'database instance 1 down'",
                    },
                },
                {
                    "labels": {
                        "job": "user-service",
                        "instance": "2",
                        "severity": "critical",
                    },
                    "startsAt": "2027-02-01T16:56:56.789624",
                    "endsAt": "2027-02-01T16:58:56.789624",
                    "status": "firing",
                    "annotations": {
                        "description": "Session latency high",
                        "summary": "'database instance 1 down'",
                    },
                },
                {
                    "labels": {
                        "job": "shipping-service",
                        "instance": "1",
                        "severity": "critical",
                    },
                    "startsAt": "2027-02-01T16:57:18.789624",
                    "endsAt": "2027-02-01T16:59:18.789624",
                    "status": "firing",
                    "annotations": {
                        "description": "Shipping delay warning",
                        "summary": "'database instance 1 down'",
                    },
                },
                {
                    "labels": {
                        "job": "order-service",
                        "instance": "1",
                        "severity": "critical",
                    },
                    "startsAt": "2027-02-01T16:57:33.789624",
                    "endsAt": "2027-02-01T16:59:33.789624",
                    "status": "firing",
                    "annotations": {
                        "description": "Order backlog risk",
                        "summary": "'database instance 1 down'",
                    },
                },
                {
                    "labels": {
                        "job": "product-catalog-service",
                        "instance": "2",
                        "severity": "critical",
                    },
                    "startsAt": "2027-02-01T17:43:56.789624",
                    "endsAt": "2027-02-01T17:45:56.789624",
                    "status": "firing",
                    "annotations": {
                        "description": "Read error surge",
                        "summary": "'database instance 1 down'",
                    },
                },
                {
                    "labels": {
                        "job": "order-service",
                        "instance": "2",
                        "severity": "critical",
                    },
                    "startsAt": "2027-02-01T17:44:28.789624",
                    "endsAt": "2027-02-01T17:46:28.789624",
                    "status": "firing",
                    "annotations": {
                        "description": "Validation error surge",
                        "summary": "'database instance 1 down'",
                    },
                },
                {
                    "labels": {
                        "job": "inventory-service",
                        "instance": "2",
                        "severity": "critical",
                    },
                    "startsAt": "2027-02-01T17:44:34.789624",
                    "endsAt": "2027-02-01T17:46:34.789624",
                    "status": "firing",
                    "annotations": {
                        "description": "Update failure increase",
                        "summary": "'database instance 1 down'",
                    },
                },
                {
                    "labels": {
                        "job": "payment-service",
                        "instance": "2",
                        "severity": "critical",
                    },
                    "startsAt": "2027-02-01T17:44:47.789624",
                    "endsAt": "2027-02-01T17:46:47.789624",
                    "status": "firing",
                    "annotations": {
                        "description": "High retry rate",
                        "summary": "'database instance 1 down'",
                    },
                },
                {
                    "labels": {
                        "job": "product-catalog-service",
                        "instance": "1",
                        "severity": "critical",
                    },
                    "startsAt": "2027-02-01T18:18:56.789624",
                    "endsAt": "2027-02-01T18:20:56.789624",
                    "status": "firing",
                    "annotations": {
                        "description": "Metadata sync delay",
                        "summary": "'database instance 1 down'",
                    },
                },
                {
                    "labels": {
                        "job": "inventory-service",
                        "instance": "1",
                        "severity": "critical",
                    },
                    "startsAt": "2027-02-01T18:19:26.789624",
                    "endsAt": "2027-02-01T18:21:26.789624",
                    "status": "firing",
                    "annotations": {
                        "description": "Stock consistency warning",
                        "summary": "'database instance 1 down'",
                    },
                },
                {
                    "labels": {
                        "job": "shipping-service",
                        "instance": "2",
                        "severity": "critical",
                    },
                    "startsAt": "2027-02-01T18:20:26.789624",
                    "endsAt": "2027-02-01T18:22:26.789624",
                    "status": "firing",
                    "annotations": {
                        "description": "Carrier API failure surge",
                        "summary": "'database instance 1 down'",
                    },
                },
                {
                    "labels": {
                        "job": "user-service",
                        "instance": "2",
                        "severity": "critical",
                    },
                    "startsAt": "2027-02-01T18:53:56.789624",
                    "endsAt": "2027-02-01T18:55:56.789624",
                    "status": "firing",
                    "annotations": {
                        "description": "Session latency high",
                        "summary": "'database instance 1 down'",
                    },
                },
                {
                    "labels": {
                        "job": "recommendation-service",
                        "instance": "1",
                        "severity": "critical",
                    },
                    "startsAt": "2027-02-01T18:54:43.789624",
                    "endsAt": "2027-02-01T18:56:43.789624",
                    "status": "firing",
                    "annotations": {
                        "description": "Recommendation latency warning",
                        "summary": "'database instance 1 down'",
                    },
                },
                {
                    "labels": {
                        "job": "inventory-service",
                        "instance": "2",
                        "severity": "critical",
                    },
                    "startsAt": "2027-02-01T19:32:56.789624",
                    "endsAt": "2027-02-01T19:34:56.789624",
                    "status": "firing",
                    "annotations": {
                        "description": "Update failure increase",
                        "summary": "'database instance 1 down'",
                    },
                },
                {
                    "labels": {
                        "job": "inventory-service",
                        "instance": "1",
                        "severity": "critical",
                    },
                    "startsAt": "2027-02-01T19:33:20.789624",
                    "endsAt": "2027-02-01T19:35:20.789624",
                    "status": "firing",
                    "annotations": {
                        "description": "Stock consistency warning",
                        "summary": "'database instance 1 down'",
                    },
                },
                {
                    "labels": {
                        "job": "shipping-service",
                        "instance": "2",
                        "severity": "critical",
                    },
                    "startsAt": "2027-02-01T19:33:24.789624",
                    "endsAt": "2027-02-01T19:35:24.789624",
                    "status": "firing",
                    "annotations": {
                        "description": "Carrier API failure surge",
                        "summary": "'database instance 1 down'",
                    },
                },
                {
                    "labels": {
                        "job": "recommendation-service",
                        "instance": "2",
                        "severity": "critical",
                    },
                    "startsAt": "2027-02-01T19:35:08.789624",
                    "endsAt": "2027-02-01T19:37:08.789624",
                    "status": "firing",
                    "annotations": {
                        "description": "Recommendation model errors",
                        "summary": "'database instance 1 down'",
                    },
                },
                {
                    "labels": {
                        "job": "user-service",
                        "instance": "2",
                        "severity": "critical",
                    },
                    "startsAt": "2027-02-01T20:07:56.789624",
                    "endsAt": "2027-02-01T20:09:56.789624",
                    "status": "firing",
                    "annotations": {
                        "description": "Session latency high",
                        "summary": "'database instance 1 down'",
                    },
                },
                {
                    "labels": {
                        "job": "order-service",
                        "instance": "1",
                        "severity": "critical",
                    },
                    "startsAt": "2027-02-01T20:08:34.789624",
                    "endsAt": "2027-02-01T20:10:34.789624",
                    "status": "firing",
                    "annotations": {
                        "description": "Order backlog risk",
                        "summary": "'database instance 1 down'",
                    },
                },
                {
                    "labels": {
                        "job": "recommendation-service",
                        "instance": "1",
                        "severity": "critical",
                    },
                    "startsAt": "2027-02-01T20:09:34.789624",
                    "endsAt": "2027-02-01T20:11:34.789624",
                    "status": "firing",
                    "annotations": {
                        "description": "Recommendation latency warning",
                        "summary": "'database instance 1 down'",
                    },
                },
            ],
        )
    )
)


class TestNotifier(BaseNotifier):
    def __init__(self) -> None:
        self.to_raise = set()

    async def notify(self, alertg: AlertGroup):
        root = alertg.root
        if root.id not in self.to_raise:
            log.critical("A false prediction.")
        else:
            log.info(f"found an alert with needed root `{alertg.root}`")


async def test_detector():
    pattren = [
        *map(
            Alert,
            [
                {
                    "labels": {
                        "job": "inventory-service",
                        "instance": "2",
                        "severity": "critical",
                    },
                    "startsAt": "2027-01-01T12:32:00",
                    "endsAt": "2027-01-01T12:33:00",
                    "status": "firing",
                    "annotations": {
                        "description": "Update failure increase",
                        "summary": "'database instance 1 down'",
                    },
                    "id": "",
                },
                {
                    "labels": {
                        "job": "shipping-service",
                        "instance": "2",
                        "severity": "critical",
                    },
                    "startsAt": "2027-01-01T12:34:00",
                    "endsAt": "2027-01-01T12:35:00",
                    "status": "firing",
                    "annotations": {
                        "description": "Carrier API failure surge",
                        "summary": "'database instance 1 down'",
                    },
                    "id": "",
                },
                {
                    "labels": {
                        "job": "inventory-service",
                        "instance": "1",
                        "severity": "critical",
                    },
                    "startsAt": "2027-01-01T12:36:00",
                    "endsAt": "2027-01-01T12:37:00",
                    "status": "firing",
                    "annotations": {
                        "description": "Stock consistency warning",
                        "summary": "'database instance 1 down'",
                    },
                    "id": "",
                },
                {
                    "labels": {
                        "job": "recommendation-service",
                        "instance": "2",
                        "severity": "critical",
                    },
                    "startsAt": "2027-01-01T12:38:00",
                    "endsAt": "2027-01-01T12:39:00",
                    "status": "firing",
                    "annotations": {
                        "description": "Recommendation model errors",
                        "summary": "'database instance 1 down'",
                    },
                    "id": "",
                },
                {
                    "labels": {
                        "job": "recommendation-service",
                        "instance": "1",
                        "severity": "critical",
                    },
                    "startsAt": "2027-01-01T12:38:00",
                    "endsAt": "2027-01-01T12:39:00",
                    "status": "firing",
                    "annotations": {
                        "description": "Recommendation latency warning",
                        "summary": "'database instance 1 down'",
                    },
                    "id": "",
                },
            ],
        )
    ]

    mq = AsyncQueue()
    nf = ConsoleNotifier()
    a_store = DictStore("test/probability")

    alert_jsons = []
    for f in data_path.iterdir():
        with open(f, "r") as fp:
            alerts = json.load(fp)
            alert_jsons.extend(alerts)
    historical_alerts = [Alert(a) for a in alert_jsons]

    for a in historical_alerts:
        await a_store.put(a.id, a)

    # Compute α/β strengths
    precomputed_links = compute_alpha_beta_links(historical_alerts, graph)
    print(precomputed_links)

    gd = ProbabilityDetector(graph, mq, a_store, nf, precomputed_links)

    for a in pattren:
        await a_store.put(a.id, a)
        await gd.process_alert(a)

    # for p, res, f in zip(patterns, results, fbs):
    # print(precomputed_links)
    # print("********************************")
    # for r in res:
    #     nf.to_raise.add(r.id)
    # for al in p:
    #     await a_store.put(al.id, al)
    #     await gd.process_alert(al)
    #
    await asyncio.gather(
        *itertools.chain(*[t.notify_tasks.values() for t in gd.batches])
    )
    #
    # for al in p:
    #     await a_store.remove(al.id)
    # nf.to_raise.clear()
    # await gd.feedback_handler(f)


async def test():
    await test_detector()


if __name__ == "__main__":
    asyncio.run(test())
