"""Measure site-packages disk footprint and process resident memory (RSS)."""

import contextlib
import os
import site
import sys
from pathlib import Path

# Ensure backend root is in sys.path
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))


def get_dir_size_bytes(path: str) -> int:
    """Calculate recursive directory size in bytes."""
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            fp = os.path.join(root, f)
            with contextlib.suppress(OSError):
                total += os.path.getsize(fp)
    return total


def find_site_packages_dirs() -> list[str]:
    """Find pure site-packages directories, excluding virtualenv roots."""
    dirs: list[str] = []
    for s_dir in site.getsitepackages():
        if os.path.basename(s_dir).lower() == "site-packages" and os.path.exists(s_dir):
            dirs.append(s_dir)
    if not dirs:
        # Fallback to sys.path entries named site-packages
        for p in sys.path:
            if os.path.basename(p).lower() == "site-packages" and os.path.exists(p):
                dirs.append(p)
    return dirs


def measure_site_packages() -> tuple[float, list[tuple[str, float]]]:
    """Measure total site-packages size and identify largest packages."""
    site_dirs = find_site_packages_dirs()
    total_bytes = 0
    package_sizes: dict[str, int] = {}

    for s_dir in site_dirs:
        total_bytes += get_dir_size_bytes(s_dir)
        for entry in os.listdir(s_dir):
            entry_path = os.path.join(s_dir, entry)
            if os.path.isdir(entry_path) and not entry.endswith(".dist-info"):
                with contextlib.suppress(OSError):
                    package_sizes[entry] = get_dir_size_bytes(entry_path)

    total_mb = total_bytes / (1024 * 1024)
    sorted_pkgs = sorted(package_sizes.items(), key=lambda x: x[1], reverse=True)[:5]
    top_5_mb = [(name, size / (1024 * 1024)) for name, size in sorted_pkgs]
    return total_mb, top_5_mb


def measure_import_rss() -> float:
    """Measure RSS memory after importing app.main."""
    import psutil

    import app.main  # noqa: F401

    process = psutil.Process(os.getpid())
    rss_mb = process.memory_info().rss / (1024 * 1024)
    return float(rss_mb)


def main() -> None:
    """Measure and print memory metrics."""
    total_mb, top_5 = measure_site_packages()
    print(f"Total site-packages size: {total_mb:.2f} MB")

    if top_5:
        print("Top 5 largest packages in site-packages:")
        for name, size in top_5:
            print(f"  - {name}: {size:.2f} MB")

    rss_mb = measure_import_rss()
    print(f"Resident memory (RSS) after importing app.main: {rss_mb:.2f} MB")


if __name__ == "__main__":
    main()
