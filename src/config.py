from pathlib import Path
import argparse
from dataclasses import dataclass, field
from omegaconf import OmegaConf


@dataclass
class Polling:
    token: str = ""
    url: str = ""
    interval: int = 60  # 1 minute.
    max_failures = 10


@dataclass
class Detector:
    batch_gap_threshold: int = 15
    time_delta: int = 5
    confidence_threshold: float = 0.2

    initial_alpha: int = 1
    initial_beta: int = 1

    delay: int = 5


@dataclass
class Server:
    host: str = "0.0.0.0"
    port: int = 8080


@dataclass
class Store:
    path: str = "test/alerts"


@dataclass
class ServiceGraph:
    path: Path = Path("service_dependancy_map.yaml")


@dataclass
class HistoricData:
    path: Path = Path()


@dataclass
class Output:
    emit_links: bool = False


@dataclass
class AppConfig:
    polling: Polling = field(default_factory=Polling)
    detector: Detector = field(default_factory=Detector)
    server: Server = field(default_factory=Server)
    store: Store = field(default_factory=Store)
    historic_data: HistoricData = field(default_factory=HistoricData)
    service_graph: ServiceGraph = field(default_factory=ServiceGraph)
    output: Output = field(default_factory=Output)


def load_config(path: str) -> AppConfig:
    conf_path = Path(path)

    cfg = OmegaConf.structured(AppConfig)

    if conf_path.exists() and conf_path.is_file():
        yaml_cfg = OmegaConf.load(args.cfg)
        cfg = OmegaConf.merge(cfg, yaml_cfg)

    cli_cfg = OmegaConf.from_cli(remaining)
    cfg = OmegaConf.merge(cfg, cli_cfg)
    return OmegaConf.to_object(cfg)


parser = argparse.ArgumentParser()
parser.add_argument(
    "--cfg", default="config.yaml", type=str, help="Path to YAML config file"
)
args, remaining = parser.parse_known_args()

cfg = load_config(args.cfg)
