import os
import subprocess
import time

from redis import Redis


def execute_sweep():
    redis = Redis(host="redis")
    while (rank := redis.rpop("rank-queue")) is None:
        time.sleep(0.1)

    while (sweep_id := redis.get("sweep_id")) is None:
        time.sleep(0.1)

    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = rank.decode("utf-8")
    while os.getenv("NUM_RUNS") is None or redis.rpop("runs-queue") is not None:
        cmd = f"python {os.getenv('SCRIPT')} sweep {sweep_id.decode('utf-8')}"
        print(cmd)
        subprocess.run(cmd.split(), env=env)
        time.sleep(10)


if __name__ == "__main__":
    execute_sweep()
