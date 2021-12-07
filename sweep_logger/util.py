from dataclasses import astuple, dataclass
from pathlib import Path
from typing import List, Optional, Tuple, Union

import yaml
from gql import gql

from sweep_logger import HasuraLogger


@dataclass
class NewParams:
    load_params: dict
    sweep_params: dict
    config_params: dict


def get_config_params(config: Union[str, Path]) -> dict:
    if isinstance(config, str):
        config = Path(config)
    with Path(config).open() as f:
        config = yaml.load(f, yaml.FullLoader)
    return config


def get_load_params(load_id: int, logger: HasuraLogger) -> dict:
    return logger.execute(
        gql(
            """
query GetParameters($id: Int!) {
run_by_pk(id: $id) {
metadata(path: "parameters")
}
}"""
        ),
        variable_values=dict(id=load_id),
    )["run_by_pk"]["metadata"]


def get_new_params(
    create_run: bool,
    logger: HasuraLogger,
    charts: List[dict] = None,
    config: Union[Path, str] = None,
    load_id: int = None,
    sweep_id: int = None,
) -> NewParams:

    config_params = None
    sweep_params = None
    load_params = None

    if config is not None:
        config_params = get_config_params(config)

    if create_run:
        if charts is None:
            charts = []
        sweep_params = logger.create_run(
            metadata={},
            sweep_id=sweep_id,
            charts=charts,
        )

    if load_id is not None:
        load_params = get_load_params(load_id=load_id, logger=logger)

    return NewParams(
        config_params=config_params,
        sweep_params=sweep_params,
        load_params=load_params,
    )


def update_params(
    logger: HasuraLogger,
    new_params: NewParams,
    name: str,
    **params,
) -> dict:

    for p in astuple(new_params):
        if p is not None:
            params.update(p)

    if logger.run_id is not None:
        logger.update_metadata(dict(parameters=params, run_id=logger.run_id, name=name))
    return params


def initialize(
    graphql_endpoint: str = None,
    config: Union[Path, str] = None,
    charts: List[dict] = None,
    sweep_id: int = None,
    load_id: int = None,
    create_run: bool = False,
    metadata=None,
    params=None,
) -> Tuple[dict, HasuraLogger]:
    if metadata is None:
        metadata = {}
    if params is None:
        params = {}
    logger = HasuraLogger(graphql_endpoint)
    new_params = get_new_params(
        charts=charts,
        config=config,
        create_run=create_run,
        load_id=load_id,
        logger=logger,
        sweep_id=sweep_id,
    )
    params.update(name=params.get("name"))
    params = update_params(
        logger=logger,
        new_params=new_params,
        **params,
    )
    if logger is not None:
        logger.update_metadata(metadata)
    return params, logger
