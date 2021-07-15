#!/usr/bin/env python3
import argparse
import copy
import logging
from pathlib import Path
from typing import Optional

import yaml
from redis import Redis

from sweep_logger.params import ParamChoice, SweepMethod
from sweep_logger.reproducibility_info import get_reproducibility_info
from sweep_logger.logger import get_logger


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
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        "-c",
        help="path to sweep config yaml file",
        type=Path,
        default=Path("config.yml"),
    )
    parser.add_argument(
        "--name", "-n", help="name of sweep (logged in metadata)", default=None
    )
    parser.add_argument(
        "--project", "-p", help="name of project (logged in metadata)", default=None
    )
    parser.add_argument(
        "--logger",
        "-l",
        help="type of logger",
        choices=["hasura", "jsonlines"],
        default="hasura",
    )
    parser.add_argument("--log-level", "-ll", choices=log_levels, default="INFO")
    parser.add_argument(
        "--method",
        "-m",
        choices=["grid", "random"],
        default="random",
        help="whether to perform grid-search on parameters in config.yml or randomly sample",
    )
    parser.set_defaults(func=run)
    subparsers = parser.add_subparsers()
    redis_parser = subparsers.add_parser("redis")
    redis_parser.set_defaults(func=run_redis)
    redis_parser.add_argument("--host", default="redis")
    redis_parser.add_argument("--port", default=6379)
    args = parser.parse_args()
    _args = vars(copy.deepcopy(args))
    del _args["func"]
    args.func(**_args)


if __name__ == "__main__":
    main()
