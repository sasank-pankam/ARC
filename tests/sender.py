# all the alerts should relate to the same service is not working.
import csv
import itertools
from pathlib import Path
import requests


false = False
true = True

curr_path = Path(__file__).parent
input_file = curr_path / "input.csv"

batch_size = 100

with open(input_file, newline="") as f:
    r = csv.DictReader(f)

    while True:
        batch = list(itertools.islice(r, batch_size))
        if not batch:
            break
        res = requests.post(
            "http://localhost:9090/webhook/alerts", json={"alerts": batch}
        )
        print(res.json(), res.status_code)
