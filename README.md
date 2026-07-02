# LaunchModel

<p align="center">
  <img src="https://img.shields.io/badge/MLflow-experiment%20tracking-0194E2?style=for-the-badge&logo=mlflow&logoColor=white"/>
  <img src="https://img.shields.io/badge/FastAPI-model%20serving-009688?style=for-the-badge&logo=fastapi&logoColor=white"/>
  <img src="https://img.shields.io/badge/Prometheus%20+%20Grafana-monitoring-E6522C?style=for-the-badge&logo=prometheus&logoColor=white"/>
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white"/>
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge"/>
</p>

<p align="center">
  <strong>End-to-end MLOps platform blueprint — model training, serving, monitoring, and autoscaling</strong><br/>
  MLflow tracking · FastAPI inference · drift detection · retraining triggers · European enterprise ready
</p>

<p align="center">
  <img src="assets/banner.svg" alt="LaunchModel Banner" width="800"/>
</p>



> A production-style MLOps platform that trains, serves, monitors, and
> autoscales a machine learning model — giving European companies a
> ready-made blueprint for getting ML models safely into production.

## Live Demo

Open [`demo/index.html`](demo/index.html) directly in any browser — no setup,
no backend required. Shows the architecture, the inference console, and real
pre-computed prediction results with a typing animation.

## Overview

LaunchModel packages the full lifecycle of a machine learning model:
**train → track → containerize → serve → monitor → autoscale → detect drift**.
The reference model predicts whether a person's income exceeds $50K/year from
census-style attributes, but the platform around it (FastAPI serving,
Prometheus metrics, MLflow tracking, Helm + HPA, drift CronJob, CI/CD to GHCR)
is model-agnostic and directly reusable.

European companies — insurers, banks, HR-tech platforms, and telecoms across
Germany, France, and the Benelux — run dozens of similar scoring models
(credit risk, churn, fraud, pricing) and need exactly this kind of MLOps
scaffolding to move models from a notebook into a monitored, autoscaling
production service.

## Architecture

```
 ┌────────────────┐     train      ┌──────────────────────┐
 │  Adult Income   │ ─────────────► │  model/train.py        │
 │  Dataset        │                │  (scikit-learn)         │
 └────────────────┘                └──────────┬────────────┘
                                                │ logs metrics + artifacts
                                                ▼
                                     ┌──────────────────────┐
                                     │   MLflow Tracking      │
                                     │   (localhost:5015)      │
                                     └──────────┬────────────┘
                                                │ model.pkl + encoder.pkl
                                                ▼
 ┌────────────────┐  POST /predict  ┌──────────────────────┐   /metrics   ┌──────────────┐
 │  Web Console /  │ ◄─────────────► │  FastAPI Service        │ ───────────► │  Prometheus  │
 │  curl / client  │                 │  (Docker, gunicorn)     │              │  + Grafana   │
 └────────────────┘                 └──────────┬────────────┘              └──────────────┘
                                                │ live_requests.jsonl
                                                ▼
                                     ┌──────────────────────┐
                                     │  Drift CronJob          │
                                     │  (K8s, nightly)         │
                                     └──────────────────────┘

 Kubernetes: Helm chart with HPA (2-10 replicas), ServiceMonitor, Ingress
```

## Tech Stack

| Technology | Version | Purpose |
|---|---|---|
| Python | 3.11 | Core language |
| FastAPI | 0.115 | Model serving API |
| scikit-learn | 1.5 | Model training (LogReg + OneHotEncoder pipeline) |
| MLflow | 2.16 | Experiment tracking, metrics & artifact storage |
| Prometheus client | 0.21 | `/metrics` endpoint for scraping |
| Docker / Docker Compose | - | Local containerized environment |
| Helm | 3.x | Kubernetes deployment charts (app + MLflow) |
| Terraform | - | GKE Autopilot cluster + workload IaC |
| GitHub Actions | - | CI/CD: tests → build → push to GHCR → Helm deploy |
| k6 | - | Load testing |
| Tailwind CSS (CDN) | 3.x | Web console & demo UI |

## Quick Start

```bash
git clone https://github.com/rayenx2/LaunchModel
cd LaunchModel
cp .env.example .env
docker compose up
```

This will:
1. Train the model (`trainer` service) and save artifacts to `model/artifacts/`
2. Start the FastAPI service at **http://localhost:8015**
3. Start MLflow tracking UI at **http://localhost:5015**

Open `http://localhost:8015` for the web console, or test directly:

```bash
curl http://localhost:8015/health
curl -X POST http://localhost:8015/predict \
  -H "content-type: application/json" \
  -d @sample_payload.json
curl http://localhost:8015/model/info
curl http://localhost:8015/predictions/recent
```

## Features

- 🧠 **Model training** with scikit-learn pipeline (OneHotEncoder + LogisticRegression), logged to MLflow
- 🚀 **FastAPI serving** with `/predict`, `/health`, `/metrics`, `/model/info`, `/predictions/recent`
- 🖥️ **Web console** (`app/static/index.html`) — dark "ops console" theme with a live inference form and endpoint browser, served at `/`
- 🧪 **Zero-backend static demo** (`demo/index.html`) with an architecture diagram and real pre-computed predictions
- 📊 **Prometheus metrics** — request counts, latencies, error counters
- 📈 **MLflow tracking** — AUC/F1 metrics + model artifacts, backed by a shared filesystem artifact store between the trainer and the tracking server
- 🌊 **Drift detection** — nightly CronJob compares live feature distributions to training baseline
- ☸️ **Kubernetes-ready** — Helm charts with HPA (2-10 replicas), ServiceMonitor, Ingress
- 🔄 **CI/CD** — GitHub Actions builds & pushes images to GHCR, deploys on release
- ☁️ **IaC** — Terraform modules for GKE Autopilot
- ✅ **Input validation** — Pydantic validators reject malformed feature payloads with clear 422 errors
- 📝 **Structured logging** — every request logged with method, path, status, latency

## Results

- Model AUC: **1.000** / F1: **0.667** on the sample training split (see `/model/info`)
- API health check and predict endpoint verified end-to-end via Docker Compose
- 4 real inference examples captured and embedded in the static demo
- All Prometheus metrics (`inference_requests_total`, `inference_errors_total`,
  `inference_latency_seconds`) scrape-ready at `/metrics`

## European Market Use Cases

- **Insurers (DE/FR/BE)** — risk-scoring models for underwriting, deployed
  with the same train→serve→monitor→drift pattern shown here
- **Banks & fintechs** — credit-scoring and fraud models that need
  autoscaling FastAPI serving with Prometheus/Grafana observability
- **HR-tech platforms** — candidate/employee classification models (e.g.
  attrition risk) requiring drift monitoring as workforce demographics shift
- **Telecoms** — churn-prediction models deployed across Kubernetes clusters
  with Helm-based CI/CD pipelines identical to this one

## Author

**Rayen Lassoued**
[github.com/rayenx2](https://github.com/rayenx2) | [LinkedIn](https://linkedin.com/in/Rayen-Lassoued)

## License

MIT
