import os, json, joblib, mlflow, argparse
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.metrics import roc_auc_score, f1_score
from sklearn.linear_model import LogisticRegression

ARTIFACT_DIR = os.getenv("ARTIFACT_DIR", "model/artifacts")
os.makedirs(ARTIFACT_DIR, exist_ok=True)

SAMPLE_DATA = [
    [39,"State-gov",77516,"Bachelors",13,"Never-married","Adm-clerical","Not-in-family","White","Male",2174,0,40,"United-States","<=50K"],
    [50,"Self-emp-not-inc",83311,"Bachelors",13,"Married-civ-spouse","Exec-managerial","Husband","White","Male",0,0,13,"United-States","<=50K"],
    [38,"Private",215646,"HS-grad",9,"Divorced","Handlers-cleaners","Not-in-family","White","Male",0,0,40,"United-States","<=50K"],
    [53,"Private",234721,"11th",7,"Married-civ-spouse","Handlers-cleaners","Husband","Black","Male",0,0,40,"United-States","<=50K"],
    [28,"Private",338409,"Bachelors",13,"Married-civ-spouse","Prof-specialty","Wife","Black","Female",0,0,40,"Cuba",">50K"],
    [37,"Private",284582,"Masters",14,"Married-civ-spouse","Exec-managerial","Wife","White","Female",0,0,40,"United-States",">50K"],
    [49,"Private",160187,"9th",5,"Married-spouse-absent","Other-service","Not-in-family","Black","Female",0,0,16,"Jamaica","<=50K"],
    [52,"Self-emp-not-inc",209642,"HS-grad",9,"Married-civ-spouse","Exec-managerial","Husband","White","Male",0,0,45,"United-States",">50K"],
    [31,"Private",45781,"Masters",14,"Never-married","Prof-specialty","Not-in-family","White","Female",14084,0,50,"United-States",">50K"],
    [42,"Private",159449,"Bachelors",13,"Married-civ-spouse","Exec-managerial","Husband","White","Male",5178,0,40,"United-States",">50K"]
]
COLS = ["age","workclass","fnlwgt","education","education_num","marital_status","occupation","relationship","race","sex","capital_gain","capital_loss","hours_per_week","native_country","income"]

def load_data(mode: str):
    if mode == "full":
        try:
            import openml
            d = openml.datasets.get_dataset(1590)  # Adult
            df, *_ = d.get_data(dataset_format="dataframe")
            # Ensure column names match expectations
            df = df.rename(columns={
                "education-num":"education_num",
                "marital-status":"marital_status",
                "native-country":"native_country",
                "hours-per-week":"hours_per_week",
                "capital-gain":"capital_gain",
                "capital-loss":"capital_loss"
            })
            return df
        except Exception as e:
            print(f"[WARN] Failed to load OpenML dataset, falling back to sample: {e}")
    return pd.DataFrame(SAMPLE_DATA, columns=COLS)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", choices=["sample","full"], default="sample")
    args = parser.parse_args()

    mlflow.set_experiment("launchmodel")
    with mlflow.start_run():
        df = load_data(args.dataset)

        # Some datasets label target differently; normalize
        target = "income"
        if target not in df.columns:
            # OpenML uses 'class'
            target = "class"
        y = (df[target].astype(str).str.contains(">50K")).astype(int)
        X = df.drop(columns=[target])

        cat = ["workclass","education","marital_status","occupation","relationship","race","sex","native_country"]
        cat = [c for c in cat if c in X.columns]
        num = [c for c in X.columns if c not in cat]

        pre = ColumnTransformer([
            ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
            ("num", "passthrough", num)
        ])

        clf = Pipeline([
            ("pre", pre),
            ("lr", LogisticRegression(max_iter=1000))
        ])

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y if y.nunique()==2 else None)
        clf.fit(X_train, y_train)

        proba = clf.predict_proba(X_test)[:,1]
        import numpy as np
        preds = (proba >= 0.5).astype(int)
        auc = float(roc_auc_score(y_test, proba)) if y.nunique()==2 else float("nan")
        f1 = float(f1_score(y_test, preds)) if y.nunique()==2 else float("nan")

        mlflow.log_metric("auc", auc)
        mlflow.log_metric("f1", f1)
        mlflow.log_param("model", "log_reg")
        mlflow.log_param("cat_features", ",".join(cat))
        mlflow.log_param("num_features", ",".join(num))

        encoder = clf.named_steps["pre"]
        model = clf.named_steps["lr"]

        os.makedirs(ARTIFACT_DIR, exist_ok=True)
        joblib.dump(model, os.path.join(ARTIFACT_DIR, "model.pkl"))
        joblib.dump(encoder, os.path.join(ARTIFACT_DIR, "encoder.pkl"))
        with open(os.path.join(ARTIFACT_DIR, "metrics.json"), "w") as f:
            json.dump({"auc": auc, "f1": f1}, f, indent=2)

        mlflow.log_artifact(os.path.join(ARTIFACT_DIR, "model.pkl"), artifact_path="artifacts")
        mlflow.log_artifact(os.path.join(ARTIFACT_DIR, "encoder.pkl"), artifact_path="artifacts")
        mlflow.log_artifact(os.path.join(ARTIFACT_DIR, "metrics.json"), artifact_path="artifacts")

        print(f"Saved artifacts to {ARTIFACT_DIR}. AUC={auc:.3f} F1={f1:.3f}")

if __name__ == "__main__":
    main()
