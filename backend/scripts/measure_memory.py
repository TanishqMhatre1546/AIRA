"""Measure container / application resident memory (RSS) and enforce 350 MB ceiling."""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# Ensure backend root is in sys.path
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

# 30 mixed queries across emergency, refusal, and guideline answers
MIXED_QUERIES = [
    # 10 Emergency queries
    "Severe crushing chest pain radiating to left arm",
    "Difficulty breathing, gasping for air and blue lips",
    "Vomiting large amount of bright red blood",
    "Sudden weakness and numbness on one side of body",
    "Found unconscious and unresponsive on the floor",
    "Severe chemical burn covering entire chest",
    "Coughing up fresh blood with high fever and confusion",
    "Severe allergic reaction with throat swelling shut",
    "Worst sudden severe headache of life like thunderclap",
    "Ingested pesticide poison and feeling extremely drowsy",
    # 10 Refusal queries
    "What dosage of paracetamol should I give to my child?",
    "Please diagnose my skin rash from this description",
    "Can you prescribe an antibiotic course for my sore throat?",
    "Can I take ibuprofen together with my blood thinner prescription?",
    "What is the exact pediatric dosage for amoxicillin syrup?",
    "Tell me definitely whether I have type 2 diabetes",
    "How many milligrams of metformin should I take daily?",
    "Can you write an online prescription for hypertension medication?",
    "Give me the dosage instructions for my cold medicine",
    "What prescription medicines interact with aspirin?",
    # 10 Guideline answer queries (retrieval + extractive/model)
    "How much fluid should I drink when having mild diarrhea?",
    "My left eye is red with mild watery discharge and no pain",
    "I have had a runny nose and mild headache for 2 days",
    "Itchy circular red rash with clear center on forearm",
    "What home remedies help soothe an uncomplicated sore throat?",
    "How should I take care of a mild nosebleed at home?",
    "Common cold symptoms and what warning signs to watch for",
    "Frequent loose watery stools without blood, what oral fluids to take?",
    "Itching between fingers that gets worse at night",
    "Raised red itchy wheals that appear and disappear within hours",
]

MEMORY_LIMIT_MB = 350.0


def wait_for_ready(base_url: str, timeout_sec: int = 30) -> bool:
    """Poll /api/ready until the service returns 200."""
    url = f"{base_url.rstrip('/')}/api/ready"
    start_time = time.time()
    print(f"Waiting for {url} to report ready...")

    while time.time() - start_time < timeout_sec:
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    print("Service is READY (HTTP 200).")
                    return True
        except Exception:
            time.sleep(0.5)

    print("Timed out waiting for service readiness.")
    return False


def send_triage_query(base_url: str, query: str, request_idx: int) -> dict:
    """Send a triage request to /api/triage and return response JSON."""
    url = f"{base_url.rstrip('/')}/api/triage"
    payload = json.dumps({"message": query}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Forwarded-For": f"198.51.100.{request_idx}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def run_workload(base_url: str) -> None:
    """Send 30 mixed queries to warm up the pipeline and exercise all pathways."""
    print(f"\nExecuting 30 mixed requests against {base_url}...")
    success_count = 0

    for i, q in enumerate(MIXED_QUERIES, 1):
        try:
            start_t = time.time()
            data = send_triage_query(base_url, q, i)
            elapsed = (time.time() - start_t) * 1000
            resp_type = data.get("response_type", "UNKNOWN")
            print(f"  [{i:02d}/30] {elapsed:5.1f}ms | Type: {resp_type:10s} | Query: {q[:45]}...")
            success_count += 1
        except Exception as e:
            print(f"  [{i:02d}/30] FAILED: {e} | Query: {q[:45]}...")

    print(f"Workload finished: {success_count}/30 queries processed successfully.\n")


def parse_docker_memory_mb(mem_str: str) -> float:
    """Parse docker memory string like '145.2MiB / 7.66GiB' or '120MB' into float MB."""
    usage_part = mem_str.split("/")[0].strip()
    usage_part = usage_part.replace("iB", "MB").replace("B", "")

    if "G" in usage_part or "g" in usage_part:
        val = float(usage_part.lower().replace("g", "").replace("m", ""))
        return val * 1024.0
    elif "k" in usage_part or "K" in usage_part:
        val = float(usage_part.lower().replace("k", "").replace("m", ""))
        return val / 1024.0
    else:
        val = float(usage_part.lower().replace("m", ""))
        return val


def get_docker_image_size(image_name: str) -> str:
    """Return human readable image size from docker inspect or images."""
    try:
        out = subprocess.check_output(
            ["docker", "image", "inspect", image_name, "--format", "{{.Size}}"],
            text=True,
        ).strip()
        size_bytes = int(out)
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    except Exception:
        return "Unknown"


def measure_docker(image_name: str, port: int = 8000) -> None:
    """Start docker container, run workload, measure memory, assert ceiling."""
    container_name = f"aira-memtest-{int(time.time())}"
    print(f"Starting test container '{container_name}' from image '{image_name}'...")

    cmd = [
        "docker",
        "run",
        "-d",
        "--name",
        container_name,
        "-p",
        f"{port}:8000",
        "-e",
        "PORT=8000",
        "-e",
        "LLM_ENABLED=false",
        "-e",
        "ENVIRONMENT=production",
        image_name,
    ]

    subprocess.check_call(cmd)

    try:
        base_url = f"http://127.0.0.1:{port}"
        if not wait_for_ready(base_url, timeout_sec=25):
            logs = subprocess.check_output(["docker", "logs", container_name], text=True)
            print("Container logs on failure:\n", logs)
            raise RuntimeError("Container failed to reach ready state.")

        run_workload(base_url)

        stats_out = subprocess.check_output(
            ["docker", "stats", "--no-stream", "--format", "{{.MemUsage}}", container_name],
            text=True,
        ).strip()

        print(f"Raw Docker Memory Usage: {stats_out}")
        rss_mb = parse_docker_memory_mb(stats_out)
        image_size = get_docker_image_size(image_name)

        print("\n================ MEMORY CHECK REPORT ================")
        print(f"Docker Image Name:           {image_name}")
        print(f"Docker Image Size:           {image_size} (informational)")
        print(f"Resident Memory (RSS):       {rss_mb:.2f} MB")
        print(f"Memory Limit Ceiling:        {MEMORY_LIMIT_MB:.2f} MB")
        print(f"Status:                      {'PASS' if rss_mb <= MEMORY_LIMIT_MB else 'FAIL'}")
        print("=====================================================\n")

        if rss_mb > MEMORY_LIMIT_MB:
            print(f"ERROR: Resident memory ({rss_mb:.2f} MB) exceeds limit of {MEMORY_LIMIT_MB} MB!")
            sys.exit(1)

    finally:
        print(f"Stopping and cleaning up container '{container_name}'...")
        subprocess.run(["docker", "rm", "-f", container_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def measure_in_process() -> None:
    """Measure RSS resident memory with in-process TestClient and psutil."""
    import psutil
    from fastapi.testclient import TestClient

    from app.config import settings
    from app.main import create_app

    settings.llm_enabled = False
    app = create_app()

    print("Executing 30 mixed queries in-process for memory verification...")
    with TestClient(app) as client:
        # Check ready
        resp = client.get("/api/ready")
        assert resp.status_code == 200, f"/api/ready returned {resp.status_code}"

        for i, q in enumerate(MIXED_QUERIES, 1):
            start_t = time.time()
            t_resp = client.post(
                "/api/triage",
                json={"message": q},
                headers={"X-Forwarded-For": f"198.51.100.{i}"},
            )
            elapsed = (time.time() - start_t) * 1000
            assert t_resp.status_code == 200, f"Query {i} returned {t_resp.status_code}"
            data = t_resp.json()
            resp_type = data.get("response_type", "UNKNOWN")
            print(f"  [{i:02d}/30] {elapsed:5.1f}ms | Type: {resp_type:10s} | Query: {q[:45]}...")

    process = psutil.Process(os.getpid())
    rss_mb = process.memory_info().rss / (1024 * 1024)

    print("\n================ MEMORY CHECK REPORT ================")
    print(f"Resident Memory (RSS):       {rss_mb:.2f} MB")
    print(f"Memory Limit Ceiling:        {MEMORY_LIMIT_MB:.2f} MB")
    print(f"Status:                      {'PASS' if rss_mb <= MEMORY_LIMIT_MB else 'FAIL'}")
    print("=====================================================\n")

    if rss_mb > MEMORY_LIMIT_MB:
        print(f"ERROR: Resident memory ({rss_mb:.2f} MB) exceeds limit of {MEMORY_LIMIT_MB} MB!")
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="AIRA memory and container footprint validation.")
    parser.add_argument("--docker-test", action="store_true", help="Run full docker container test")
    parser.add_argument("--image", default="aira-backend:latest", help="Docker image name")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind")
    parser.add_argument("--url", help="Target running URL without managing process")
    args = parser.parse_args()

    if args.url:
        wait_for_ready(args.url)
        run_workload(args.url)
    elif args.docker_test:
        measure_docker(args.image, args.port)
    else:
        measure_in_process()


if __name__ == "__main__":
    main()
