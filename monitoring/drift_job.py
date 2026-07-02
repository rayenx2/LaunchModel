import json, os, time
from collections import Counter

LIVE_LOG = os.getenv("LIVE_LOG", "ops/data/live_requests.jsonl")
BASELINE_PATH = os.getenv("BASELINE_PATH", "model/artifacts/baseline_feature_freq.json")
THRESHOLD = float(os.getenv("DRIFT_THRESHOLD", "0.2"))  # simple chi-like threshold

def load_live(n=1000):
    rows = []
    if not os.path.exists(LIVE_LOG):
        return rows
    with open(LIVE_LOG) as f:
        for line in f:
            try:
                rows.append(json.loads(line)["features"])
            except:
                pass
    return rows[-n:]

def categorical_freq(rows, keys):
    freqs = {}
    for k in keys:
        c = Counter([str(r.get(k)) for r in rows])
        total = sum(c.values()) or 1
        freqs[k] = {kv: v/total for kv, v in c.items()}
    return freqs

def compare_freq(a, b):
    # returns max absolute difference per key
    diffs = {}
    for k in a.keys():
        keys = set(a[k]).union(b.get(k, {}).keys())
        dmax = 0.0
        for val in keys:
            d = abs(a[k].get(val, 0.0) - b.get(k, {}).get(val, 0.0))
            dmax = max(dmax, d)
        diffs[k] = dmax
    return diffs

def main():
    # establish baseline from training-time if available
    if not os.path.exists(BASELINE_PATH):
        print("[drift] no baseline found; create one by running 'python monitoring/save_baseline.py'")
        return
    with open(BASELINE_PATH) as f:
        baseline = json.load(f)

    rows = load_live()
    if not rows:
        print("[drift] no live data to check")
        return

    keys = list(baseline.keys())
    live = categorical_freq(rows, keys)
    diffs = compare_freq(baseline, live)

    alerts = {k: v for k, v in diffs.items() if v >= THRESHOLD}
    if alerts:
        print(f"[ALERT][drift] categorical shift detected: {alerts}")
    else:
        print("[drift] no significant drift detected")

if __name__ == "__main__":
    main()
