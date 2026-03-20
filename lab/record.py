"""
record.py — Display evaluation results for TSP autoresearch.
Called by prepare.py to print results to stdout.
"""


def training_results(results: dict):
    """Print training evaluation results."""
    print("\n=== Training (random instances) ===\n")
    for name, data in results.items():
        if not isinstance(data, dict):
            continue
        if data.get("valid"):
            print(
                f"  {name:12s}  {data['tour_length']:>10.2f} / {data['baseline']:>10.2f}"
                f"  {data['improvement']:>+8.2%}  {data['time']:.3f}s"
            )
        else:
            print(f"  {name:12s}  FAILED: {data.get('error', 'unknown')}")
    print(f"\n  avg_improvement: {results['avg_improvement']:.2%}  |  total_time: {results['total_time']}s")


def benchmark_results(results: dict):
    """Print benchmark evaluation results."""
    print("\n=== Benchmark (TSPLIB known optima) ===\n")
    for name, data in results.items():
        if not isinstance(data, dict):
            continue
        if data.get("valid"):
            print(
                f"  {name:12s}  {data['tour_length']:>10.2f} / {data['optimal']:>10.2f} opt"
                f"  {data['loss']:>+8.2%} loss  {data['time']:.3f}s"
            )
        else:
            print(f"  {name:12s}  FAILED: {data.get('error', 'unknown')}")
    print(f"\n  avg_loss: {results['avg_loss']:.2%}  |  total_time: {results['total_time']}s")
