#!/usr/bin/env python3
import argparse
import copy
import logging
from pathlib import Path
from typing import Optional

import yaml
from redis import Redis
# from run_logger import ParamChoice, SweepMethod, get_logger

from sweep_logger.reproducibility_info import get_reproducibility_info


def load_config(config: Path) -> dict:
    with config.open() as f:
        return yaml.load(f, Loader=yaml.FullLoader)


def run(
    config: Path,
    log_level: str,
    name: Optional[str],
    project: Optional[str],
    logger: str,
    method: str,
) -> int:
    breakpoint()
    config = load_config(config)
    logging.getLogger().setLevel(log_level)
    metadata = dict(
        config=config,
        **get_reproducibility_info(),
    )
    if name is not None:
        metadata.update(name=name)
    if project is not None:
        metadata.update(project=project)
    with get_logger(logger) as logger:
        if isinstance(config, list):
            config = {"": config}
        choices = [ParamChoice(k, v) for k, v in config.items()]

        sweep_id = logger.create_sweep(
            method=SweepMethod[method],
            metadata=metadata,
            choices=choices,
        )
    logging.info(f"Sweep ID: {sweep_id}")
    return sweep_id


def run_redis(host, port, **kwargs):
    sweep_id = run(**kwargs)
    redis = Redis(host=host, port=port)
    redis.set("sweep_id", sweep_id)


log_levels = [
    "CRITICAL",
    "FATAL",
    "ERROR",
    "WARN",
    "WARNING",
    "INFO",
    "DEBUG",
    "NOTSET",
]

def main():
    print("main from main")

if __name__ == "__main__":
    PARSER = argparse.ArgumentParser()
    PARSER.add_argument(
        "--config",
        "-c",
        help="path to sweep config yaml file",
        type=Path,
        default=Path("config.yml"),
    )
    PARSER.add_argument(
        "--name", "-n", help="name of sweep (logged in metadata)", default=None
    )
    PARSER.add_argument(
        "--project", "-p", help="name of project (logged in metadata)", default=None
    )
    PARSER.add_argument(
        "--logger",
        "-l",
        help="type of logger",
        choices=["hasura", "jsonlines"],
        default="hasura",
    )
    PARSER.add_argument("--log-level", "-ll", choices=log_levels, default="info")
    PARSER.add_argument(
        "--method",
        "-m",
        choices=["grid", "random"],
        default="random",
        help="whether to perform grid-search on parameters in config.yml or randomly sample",
    )
    PARSER.set_defaults(func=run)
    SUBPARSERS = PARSER.add_subparsers()
    REDIS_PARSER = SUBPARSERS.add_parser("redis")
    REDIS_PARSER.set_defaults(func=run_redis)
    REDIS_PARSER.add_argument("--host", default="redis")
    REDIS_PARSER.add_argument("--port", default=6379)
    ARGS = PARSER.parse_args()
    _ARGS = vars(copy.deepcopy(ARGS))
    del _ARGS["func"]
    ARGS.func(**_ARGS)
