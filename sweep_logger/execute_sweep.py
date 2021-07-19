import os
import subprocess
import time

from redis import Redis


def execute_sweep():
    redis = Redis(host="redis")
    rank = redis.decr("rank-counter")
    print("rank ==", rank)

    while (sweep_id := redis.get("sweep_id")) is None:
        time.sleep(0.1)
    print("sweep_id ==", sweep_id)

    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = str(rank)

    while (
        redis.object("encoding", "runs-counter") != b"int"
        or redis.decr("runs-counter") >= 0
    ):
        cmd = f"python {os.getenv('SCRIPT')} sweep {sweep_id.decode('utf-8')}"
        print(cmd)
        subprocess.run(cmd.split(), env=env)
        time.sleep(10)


if __name__ == "__main__":
    execute_sweep()
