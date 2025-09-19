from pathlib import Path
import sys
import os
import csv


from src.graph import BaseGraph
from src.http_server import HTTPServer
from src.ingress import HTTPIngress
from src.storage import BaseAlertStore

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio

from src import log

from src.notifier import WsNotifier
from src.graph import ServiceGraph
from src.message_queue import AsyncQueue
from src.detector import ProbabilityDetector
from src.storage import DictStore
from src.preprocessing.causal_inference import compute_alpha_beta_links
from src.models import Alert


async def preprocess(graph: BaseGraph, store: BaseAlertStore, data_path: Path):
    if not data_path.exists() or not data_path.is_file():
        log.info(
            f"Skipping preprocessing as the directory is not present in the disk path={data_path.absolute()}"
        )
        return

    alert_dicts = []
    with open(data_path, "r", newline="") as fp:
        alerts = csv.DictReader(fp)
        alert_dicts.extend(alerts)
    historical_alerts = list(
        filter(lambda x: x.service != -1, (Alert(a) for a in alert_dicts))
    )

    # Compute α/β link strengths using valid historical alerts
    precomputed_links = await compute_alpha_beta_links(historical_alerts, store, graph)
    print("***********   Preprocessing summary   *************")
    print(f"Total historical alerts used : {len(historical_alerts)}")
    print(f"Total computed links         : {len(precomputed_links)}")

    print("Head of the computed links.")
    links_out_file = "links.csv" if cfg.output.emit_links else os.devnull
    with open(links_out_file, "w", newline="") as f:
        wr = csv.DictWriter(
            f, fieldnames=["index", "source", "destination", "alpha", "beta"]
        )
        wr.writeheader()

        for i, ((src, dst), (alpha, beta)) in enumerate(precomputed_links.items()):
            if i <= 4:
                print(f"Link {i + 1}: {src} → {dst} | α={alpha},β={beta}")

            wr.writerow(
                {
                    "index": i + 1,
                    "source": src,
                    "destination": dst,
                    "alpha": alpha,
                    "beta": beta,
                }
            )

    print("***************************************************")
    if cfg.output.emit_links:
        log.info(f"Dumped link properties into {links_out_file}")

    return precomputed_links


async def main(config):
    notifier = WsNotifier()
    graph = ServiceGraph(cfg.service_graph.path)
    mq = AsyncQueue()
    store = DictStore(cfg.store.path)
    precomputed_links = await preprocess(graph, store, cfg.historic_data.path)

    # Initialize detector
    store.active.clear()
    detector = ProbabilityDetector(graph, mq, store, notifier, precomputed_links)
    # p_ingress = (
    #     # 1 minute.
    #     PollerIngress(mq, 1).with_url(cfg.polling.url).with_token(cfg.polling.token)
    # )

    h_ingress = HTTPIngress(mq)

    httpserver = HTTPServer(notifier, detector.feedback_handler)
    try:
        await asyncio.gather(detector.start(), httpserver.listen(), h_ingress.begin())
    except asyncio.CancelledError:
        print()
        await httpserver.close()
        await notifier.free_wsockets()
        raise
    except Exception as e:
        log.warning(f"Error in system {e}")
        raise


def start():
    try:
        asyncio.run(main(cfg))
    except KeyboardInterrupt:
        print("Exiting the application.")


if __name__ == "__main__":
    from src.config import cfg

    start()
