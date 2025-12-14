"""
Basic latency benchmark for /twin/chat.
Run backend first, then:
    python scripts/bench_chat.py --n 50 --url http://127.0.0.1:8000
Reports p50/p95 latency in ms.
"""
import argparse
import statistics
import time
import requests


SAMPLE_PAYLOADS = [
    {
        "question": "How is my fasting glucose doing?",
        "health_state": {"fasting_glucose": 118, "history": {"fasting_glucose": [132, 125]}},
    },
    {
        "question": "How did I sleep?",
        "health_state": {"sleep_hours": 6},
    },
    {
        "question": "What should I do next?",
        "health_state": {"bp_systolic": 130, "bp_diastolic": 85},
    },
]


def run_once(url: str, payload: dict) -> float:
    start = time.time()
    r = requests.post(f"{url}/twin/chat", json=payload, timeout=15)
    r.raise_for_status()
    _ = r.json()
    return (time.time() - start) * 1000


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="Backend base URL")
    parser.add_argument("--n", type=int, default=20, help="Number of requests")
    args = parser.parse_args()

    latencies = []
    for i in range(args.n):
        payload = SAMPLE_PAYLOADS[i % len(SAMPLE_PAYLOADS)]
        try:
            lat = run_once(args.url, payload)
            latencies.append(lat)
        except Exception as e:
            print(f"Request {i} failed: {e}")

    if not latencies:
        print("No successful requests.")
        return
    p50 = statistics.median(latencies)
    p95 = statistics.quantiles(latencies, n=20)[18]  # approximate p95
    print(f"Completed {len(latencies)} requests")
    print(f"p50: {p50:.1f} ms | p95: {p95:.1f} ms")


if __name__ == "__main__":
    main()
