import argparse
import os
import subprocess
import time
from typing import Optional

from redis import Redis
from run_logger import Client


def execute_sweep(hasura_uri: str, hasura_secret: Optional[str]):
    redis = Redis(host="redis")
    rank = redis.decr("rank-counter")
    print("rank ==", rank)

    while (sweep_id := redis.get("sweep_id")) is None:
        time.sleep(0.1)
    print("sweep_id ==", sweep_id)

    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = str(rank)

    client = Client(hasura_uri=hasura_uri, hasura_secret=hasura_secret)

    def keep_running():
        data = client.execute(
            """
mutation incr_run_count($sweep_id: Int!) {
  update_sweep(where: {id: {_eq: $sweep_id}}, _inc: {run_count: 1}) {
    returning {
      run_count
    }
  }
}
        """,
            variable_values=dict(sweep_id=sweep_id),
        )
        run_count = data["update_sweep"]["returning"][0]["run_count"]
        max_runs = redis.get("max_runs")
        return max_runs is None or run_count < max_runs

    while keep_running():
        cmd = f"python {os.getenv('SCRIPT')} sweep {sweep_id.decode('utf-8')}"
        print(cmd)
        subprocess.run(cmd.split(), env=env)
        time.sleep(10)


if __name__ == "__main__":
    PARSER = argparse.ArgumentParser()
    PARSER.add_argument("--hasura-uri", required=True)
    PARSER.add_argument("--hasura-secret")
    execute_sweep(**vars(PARSER.parse_args()))
