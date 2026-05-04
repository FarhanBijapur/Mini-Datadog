import argparse
import json
import random
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone


SERVICES = [
    "checkout-api",
    "payment-worker",
    "auth-service",
    "inventory-api",
    "notification-worker",
    "gateway-edge",
]

MESSAGES = {
    "INFO": [
        "request completed",
        "cache refresh completed",
        "worker batch processed",
        "health check passed",
    ],
    "WARN": [
        "latency above service baseline",
        "retry scheduled for downstream call",
        "queue depth approaching threshold",
    ],
    "ERROR": [
        "downstream timeout while processing request",
        "payment authorization failed",
        "database write retry exhausted",
        "5xx response from upstream dependency",
    ],
    "DEBUG": [
        "trace sampled for request path",
        "dedupe cache lookup completed",
        "worker heartbeat recorded",
    ],
}


def choose_level(spike: bool) -> str:
    if spike:
        return random.choices(["INFO", "WARN", "ERROR", "DEBUG"], weights=[35, 15, 45, 5], k=1)[0]
    return random.choices(["INFO", "WARN", "ERROR", "DEBUG"], weights=[70, 15, 10, 5], k=1)[0]


def post_log(base_url: str, payload: dict) -> None:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/logs",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=3) as response:
        response.read()


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate demo logs for Mini Datadog.")
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="Backend base URL")
    parser.add_argument("--count", type=int, default=120, help="Number of logs to send")
    parser.add_argument("--delay", type=float, default=0.08, help="Delay between logs in seconds")
    parser.add_argument("--spike", action="store_true", help="Generate an error-heavy traffic spike")
    args = parser.parse_args()

    for index in range(args.count):
        level = choose_level(args.spike)
        service = random.choice(SERVICES)
        payload = {
            "source": "demo-generator",
            "service": service,
            "level": level,
            "message": f"{random.choice(MESSAGES[level])} #{index + 1}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "attributes": {
                "demo": True,
                "sequence": index + 1,
                "region": random.choice(["ap-south-1", "us-east-1", "eu-west-1"]),
                "latency_ms": random.randint(12, 900 if level == "ERROR" else 240),
            },
            "tags": ["demo", "local"],
        }

        try:
            post_log(args.url, payload)
            print(f"{index + 1:03d}/{args.count} {level:<5} {service} - {payload['message']}", flush=True)
        except urllib.error.URLError as error:
            raise SystemExit(f"Could not reach {args.url}: {error}") from error

        time.sleep(args.delay)


if __name__ == "__main__":
    main()
