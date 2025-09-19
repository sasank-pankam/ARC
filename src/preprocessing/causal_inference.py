from collections import defaultdict
from hashlib import sha256
import itertools
import sys
from typing import List, Dict, Tuple
from statistics import mean
import random

from src.models import Alert
from src.storage import BaseAlertStore
from src.config import cfg
from datetime import timedelta

td = timedelta(minutes=cfg.detector.time_delta)


def is_temporally_valid(parent_alert, child_alert, delta=td) -> bool:
    return (
        parent_alert.startsAt <= child_alert.startsAt <= parent_alert.startsAt + delta
    )


def batch_alerts(
    alerts: List[Alert], gap_threshold=timedelta(cfg.detector.batch_gap_threshold)
) -> List[List[Alert]]:
    alerts = sorted(alerts, key=lambda a: a.startsAt)
    batches = []
    current_batch = []

    for alert in alerts:
        if not current_batch:
            current_batch.append(alert)
            continue

        if alert.startsAt - current_batch[-1].startsAt > gap_threshold:
            batches.append(current_batch)
            current_batch = [alert]
        else:
            current_batch.append(alert)

    if current_batch:
        batches.append(current_batch)

    return batches


def normalize_batches(batches: List[List[Alert]]) -> List[List[Alert]]:
    """
    Balances batch type frequencies by resampling to the median count across unique batch hashes.
    """

    batch_counter = defaultdict(int)
    batch_map = defaultdict(list)

    for batch in batches:
        batch_ids = sorted([alert.id for alert in batch])
        hash_key = sha256("".join(batch_ids).encode()).hexdigest()
        batch_counter[hash_key] += 1
        batch_map[hash_key].append(batch)

    # Use median as target frequency
    freq_values = list(batch_counter.values())
    if not freq_values:
        return []

    target_count = int(mean(freq_values))

    normalized_batches = []
    for hash_key, instances in batch_map.items():
        if len(instances) > target_count:
            s = random.sample(instances, target_count)
            normalized_batches.extend(s)
        else:
            s = instances
            # s = random.choices(instances, k=target_count)
            normalized_batches.extend(s)

    return normalized_batches


def process_batch(
    batch: List[Alert], graph, delta=td
) -> Dict[Tuple[str, str], List[int]]:
    links = defaultdict(lambda: [cfg.detector.initial_alpha, cfg.detector.initial_beta])
    service_to_alerts = defaultdict(list)

    for alert in batch:
        service_to_alerts[alert.service].append(alert)

    for alert in batch:
        parent_services = graph.get_connected(
            alert.service
        )  # connect the most suitable alert.
        # parent_services = graph.get_parents(alert.service)
        a: set[Alert] = set(
            [
                *itertools.chain(
                    *[service_to_alerts.get(p.id, []) for p in parent_services]
                ),
                *service_to_alerts[alert.service],
            ]
        )
        a.remove(alert)
        recent_alert: Alert = max(a, key=lambda x: x.startsAt, default=None)

        if recent_alert is None or recent_alert.id == alert.id:
            continue

        key = (recent_alert.id, alert.id)
        if is_temporally_valid(recent_alert, alert, delta):
            links[key][0] += 1
        else:
            links[key][1] += 1

        # for p_service in parent_services:
        #     parent_alerts = service_to_alerts.get(p_service.id, [])
        #     sorted_parents = sorted(
        #         parent_alerts, key=lambda x: x.startsAt, reverse=True
        #     )
        #     for parent_alert in sorted_parents:
        #         if parent_alert.id == alert.id:
        #             continue
        #
        #         key = (parent_alert.id, alert.id)
        #         if is_temporally_valid(parent_alert, alert, delta):
        #             links[key][0] += 1
        #         else:
        #             links[key][1] += 1

    return links


async def compute_alpha_beta_links(
    alerts: List[Alert],
    store: BaseAlertStore,
    graph,
) -> Dict[Tuple[str, str], List[int]]:
    batches = batch_alerts(alerts)
    normalized_batches = normalize_batches(batches)
    total_links = defaultdict(
        lambda: [cfg.detector.initial_alpha, cfg.detector.initial_beta]
    )

    print("***************  Preprocessing Info  **************")
    print("Total batches     : ", len(batches))
    print("Normalised batches: ", len(normalized_batches))
    print("***************************************************")

    for batch in normalized_batches:
        batch_links = process_batch(batch, graph)

        for al in batch:
            await store.put(al.id, al)

        for key, (a, b) in batch_links.items():
            total_links[key][0] += a - cfg.detector.initial_alpha
            total_links[key][1] += b - cfg.detector.initial_beta

    return total_links


# Dummy run for verification (replace with actual data and graph)
if __name__ == "__main__":
    map_dir = sys.argv[1]
    data_dir = sys.argv[2]
