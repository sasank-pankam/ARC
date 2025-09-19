import random
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path
import datetime as dt

import uuid

# === CONFIG ===
NUM_DAYS = 500
MIN_SCENARIOS_PER_DAY = 1
MAX_SCENARIOS_PER_DAY = 3
SCENARIO_GAP_RANGE_MINUTES = (20, 30)
ALERT_GAP_RANGE_SECONDS = (30, 50)
ALERT_DURATION_MINUTES = 3
OUTPUT_DIR = "./test_data/data/"
TYPE1_NOISE_DIR = "./test_data/type1_noise"
NOISE_DAY_PERCENT = 0.4

# === FIXED SCENARIOS ===
SCENARIOS = [
    ["1.1", "2.1", "3.1", "4.1", "5.1"],
]

# === ALERT METADATA ===
alert_metadata = {
    "1.1": {
        "service": "auth-service",
        "desc": "Login spike",
        "summary": "Sudden surge in login attempts",
    },
    "2.1": {
        "service": "catalog-service",
        "desc": "Catalog sync issue",
        "summary": "Product catalog synchronization delay",
    },
    "3.1": {
        "service": "inventory-service",
        "desc": "Inventory mismatch",
        "summary": "Inventory records inconsistent across nodes",
    },
    "4.1": {
        "service": "order-service",
        "desc": "Order queue delay",
        "summary": "Order processing backlog increasing",
    },
    "5.1": {
        "service": "payment-service",
        "desc": "Payment timeout",
        "summary": "Payment gateway timeouts exceeding threshold",
    },
    "6.1": {
        "service": "analytics-service",
        "desc": "High report generation latency",
        "summary": "Analytics reports taking too long to generate",
    },
    "7.1": {
        "service": "email-service",
        "desc": "Email delivery drop",
        "summary": "Decrease in successful outbound email delivery",
    },
    "8.1": {
        "service": "chatbot-service",
        "desc": "Response mismatch detected",
        "summary": "Chatbot returning inconsistent or incorrect responses",
    },
    "9.1": {
        "service": "logging-service",
        "desc": "Log ingestion failure",
        "summary": "System logs failing to reach ingestion pipeline",
    },
    "10.1": {
        "service": "monitoring-service",
        "desc": "Anomaly detector crash",
        "summary": "Anomaly detection module crashed unexpectedly",
    },
}

# === SERVICE GRAPH ===
service_graph = {
    "1": {"parents": [], "children": ["2"]},
    "2": {"parents": ["1"], "children": ["3"]},
    "3": {"parents": ["2"], "children": ["4"]},
    "4": {"parents": ["3"], "children": ["5"]},
    "5": {"parents": ["4"], "children": []},
    "6": {"parents": [], "children": []},
    "7": {"parents": [], "children": []},
    "8": {"parents": [], "children": []},
    "9": {"parents": [], "children": []},
    "10": {"parents": [], "children": []},
}


def create_alert(alert_id, start_time):
    meta = alert_metadata[alert_id]
    service_id = alert_id.split(".")[1]
    end_time = start_time + timedelta(minutes=ALERT_DURATION_MINUTES)
    fmt = "%b %d, %Y, %I:%M:%S %p"
    return {
        "Id": str(uuid.uuid4()),
        "Current State": "critical",
        "Resource Name": meta["service"],
        "Created Time": start_time.strftime(fmt),
        "End Date": "09-10-2025",
        "Metric": meta["desc"],
        "Subject": meta["summary"],
    }


def generate_day_alerts(day_index, base_date):
    alerts = []
    involved_services = set()
    scenario_count = random.randint(MIN_SCENARIOS_PER_DAY, MAX_SCENARIOS_PER_DAY)
    scenario_pool = random.choices(SCENARIOS, k=scenario_count)
    current_time = base_date.replace(hour=0, minute=0, second=0) + timedelta(
        minutes=random.randint(0, 60)
    )

    for scenario in scenario_pool:
        for alert_id in scenario:
            alert = create_alert(alert_id, current_time)
            alerts.append(alert)
            involved_services.add(alert_id.split(".")[0])
            current_time += timedelta(seconds=random.randint(*ALERT_GAP_RANGE_SECONDS))
        current_time += timedelta(minutes=random.randint(*SCENARIO_GAP_RANGE_MINUTES))

    return alerts, involved_services


def choose_linked_alerts(existing_services, count):
    valid = []
    for aid, meta in alert_metadata.items():
        sid = aid.split(".")[0]
        if sid in existing_services:
            continue
        if any(p in existing_services for p in service_graph[sid]["parents"]):
            valid.append(aid)
    return random.choices(valid, k=count) if valid else []


# === MAIN ===
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    Path(TYPE1_NOISE_DIR).mkdir(exist_ok=True)
    base_date = datetime.now(dt.UTC) - timedelta(days=NUM_DAYS)

    alerts_by_day = {}
    involved_services_by_day = {}
    all_alerts_flat = []
    type1_noise_by_day_pattern = defaultdict(lambda: defaultdict(list))

    # Days allowed to have any noise
    allowed_noise_days = set(
        random.sample(range(NUM_DAYS), int(NUM_DAYS * NOISE_DAY_PERCENT))
    )
    used_noise_days = set()

    # === Step 1a: Force include all scenarios once
    for day, scenario in enumerate(SCENARIOS):
        day_time = base_date + timedelta(days=day)
        alerts = []
        involved_services = set()
        current_time = day_time.replace(hour=0, minute=0, second=0) + timedelta(
            minutes=random.randint(0, 60)
        )
        for alert_id in scenario:
            alert = create_alert(alert_id, current_time)
            alerts.append(alert)
            involved_services.add(alert_id.split(".")[0])
            current_time += timedelta(seconds=random.randint(*ALERT_GAP_RANGE_SECONDS))
        alerts_by_day[day] = alerts
        involved_services_by_day[day] = involved_services
        all_alerts_flat.extend(alerts)

    # === Step 1b: Generate remaining days
    for day in range(len(SCENARIOS), NUM_DAYS):
        day_time = base_date + timedelta(days=day)
        alerts, services = generate_day_alerts(day, day_time)
        alerts_by_day[day] = alerts
        involved_services_by_day[day] = services
        all_alerts_flat.extend(alerts)

    # === Step 2: Determine total noise
    total_scenario_alerts = len(all_alerts_flat)
    total_noise_alerts = int(total_scenario_alerts * 0.2)
    half = total_noise_alerts // 2

    # === Step 3: Type 1 noise (correlated)
    correlated_inserted = 0
    attempts = 0
    while correlated_inserted < half and attempts < half * 10:
        unused = allowed_noise_days - used_noise_days
        if not unused:
            break
        day = random.choice(list(unused))
        service_set = involved_services_by_day[day]
        new_alert_ids = choose_linked_alerts(service_set, 1)
        if not new_alert_ids:
            attempts += 1
            continue
        ts = datetime.fromisoformat(alerts_by_day[day][-1]["startsAt"]) + timedelta(
            minutes=random.randint(1, 5)
        )
        for aid in new_alert_ids:
            alert = create_alert(aid, ts)
            alerts_by_day[day].append(alert)
            for pattern_idx, pattern in enumerate(SCENARIOS):
                pattern_services = {pid.split(".")[0] for pid in pattern}
                if any(p in service_set for p in pattern_services):
                    day_key = f"day_{day + 1:04d}"
                    pattern_key = f"pattern_{pattern_idx}"
                    type1_noise_by_day_pattern[day_key][pattern_key].append(alert)
                    break
            correlated_inserted += 1
        used_noise_days.add(day)
        attempts += 1

    # === Step 4: Type 2 noise (independent scenarios)
    independent_inserted = 0
    fake_scenarios = [
        ["2.1", "4.1"],
        ["3.1", "5.1"],
        ["1.1", "3.1"],
    ]
    while independent_inserted < (total_noise_alerts - half):
        unused = allowed_noise_days - used_noise_days
        if not unused:
            break
        day = random.choice(list(unused))
        scenario = random.choice(fake_scenarios)
        ts = datetime.now(dt.UTC).replace(hour=3, minute=0, second=0) + timedelta(
            days=day
        )
        for aid in scenario:
            alert = create_alert(aid, ts)
            alerts_by_day[day].append(alert)
            ts += timedelta(seconds=random.randint(30, 50))
            independent_inserted += 1
        used_noise_days.add(day)

    # === Step 5: Save alerts by day
    for day, alerts in alerts_by_day.items():
        filename = os.path.join(OUTPUT_DIR, f"alerts_day_{day + 1:04d}.json")
        with open(filename, "w") as f:
            json.dump(alerts, f, indent=2)

    # === Step 6: Save Type 1 noise by day & pattern
    for day_key, patterns in type1_noise_by_day_pattern.items():
        day_dir = Path(TYPE1_NOISE_DIR) / day_key
        day_dir.mkdir(parents=True, exist_ok=True)
        for pattern_key, alerts in patterns.items():
            with open(day_dir / f"{pattern_key}.json", "w") as f:
                json.dump(alerts, f, indent=2)

    # === Summary
    print(f"Generated {NUM_DAYS} days.")
    print(f"Scenario alerts: {len(all_alerts_flat)}")
    print(f"Type 1 noise alerts: {correlated_inserted}")
    print(f"Type 2 noise alerts: {independent_inserted}")
    print(f"Output in '{OUTPUT_DIR}/' and '{TYPE1_NOISE_DIR}/'")


if __name__ == "__main__":
    main()
