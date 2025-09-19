import logging
import logging.config
import logging.handlers
import queue
import atexit
import yaml


class Constants:
    pass


def setup_async_logging(config_path="log_config.yaml", logger_name="src"):
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    fmt_str = config["formatters"]["default"]["format"]
    datefmt_str = config["formatters"]["default"]["datefmt"]

    console_cfg = config["handlers"]["console"]
    file_cfg = config["handlers"]["file"]

    formatter = logging.Formatter(fmt=fmt_str, datefmt=datefmt_str)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, console_cfg["level"]))
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(
        filename=file_cfg["filename"], mode=file_cfg.get("mode", "a")
    )
    file_handler.setLevel(getattr(logging, file_cfg["level"]))
    file_handler.setFormatter(formatter)

    log_queue = queue.Queue(-1)
    queue_handler = logging.handlers.QueueHandler(log_queue)

    logging.config.dictConfig(config)

    logger = logging.getLogger(logger_name)
    logger.handlers = []
    logger.addHandler(queue_handler)
    logger.setLevel(getattr(logging, config["loggers"][logger_name]["level"]))
    logger.propagate = config["loggers"][logger_name].get("propagate", False)

    listener = logging.handlers.QueueListener(log_queue, console_handler, file_handler)
    listener.start()

    atexit.register(listener.stop)

    return logger


log = setup_async_logging()
