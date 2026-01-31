import os

import httpx


def ping_heartbeat(heartbeat_key: str) -> None:
    print(f'Job completed, updating heartbeat {heartbeat_key}.')
    heartbeat_url = os.getenv(heartbeat_key)
    response = httpx.get(heartbeat_url)
    print(f'Heartbeat response: {response.status_code} - {response.text}')
