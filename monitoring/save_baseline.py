# Save baseline categorical frequencies from training data for drift comparison
import json, os, joblib, pandas as pd
from model.train import load_data, COLS

OUT = os.getenv("BASELINE_PATH", "model/artifacts/baseline_feature_freq.json")
def main():
    df = load_data("sample")
    # choose a few categorical keys
    keys = ["workclass","education","marital_status","sex","native_country"]
    keys = [k for k in keys if k in df.columns]
    freqs = {}
    for k in keys:
        c = df[k].astype(str).value_counts(normalize=True)
        freqs[k] = {str(i): float(v) for i, v in c.items()}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(freqs, f, indent=2)
    print(f"Saved baseline to {OUT}")

if __name__ == "__main__":
    main()
