# custom-map-reduce

A from-scratch MapReduce implementation for finding the **Top-X most frequent URLs** in a large dataset, deployed on Kubernetes using a StatefulSet for mappers and a Deployment for the reducer.

---

## Concept

The system follows the classic MapReduce pattern:

1. **Data Generation** — a one-shot Job writes a large CSV of URLs with Zipf-distributed frequencies to a shared volume.
2. **Map phase** — each mapper pod owns a disjoint byte-range partition of the CSV. It counts URL occurrences in its slice and serves the result over HTTP.
3. **Reduce phase** — the single reducer pod fans out to all mapper `/results` endpoints, merges the partial counters, and returns the global Top-X list.

External clients query the reducer via a NodePort service.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                      Kubernetes Namespace: mapreduce                      │
│                                                                           │
│  ┌─────────────────────┐                                                  │
│  │   Job: data-generator│                                                 │
│  │   (generate_data.py) │                                                 │
│  │                      │  Generates 10M URL rows with Zipf distribution  │
│  │  --rows 10000000     │  Writes /data/input.csv + /data/metadata.json   │
│  └──────────┬───────────┘                                                 │
│             │ hostPath volume (/tmp/mapreduce on node)                    │
│             ▼                                                             │
│  ┌──────────────────────────────────────────────────────────────────┐     │
│  │                  StatefulSet: mapper  (3 replicas)                │     │
│  │                                                                   │     │
│  │   init container: waits for /data/metadata.json before starting  │     │
│  │                                                                   │     │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │     │
│  │  │  mapper-0    │  │  mapper-1    │  │  mapper-2    │            │     │
│  │  │              │  │              │  │              │            │     │
│  │  │ bytes [0,N/3)│  │bytes[N/3,2N/3│  │bytes[2N/3,N] │            │     │
│  │  │              │  │              │  │              │            │     │
│  │  │  GET /results│  │  GET /results│  │  GET /results│            │     │
│  │  │  → {counts}  │  │  → {counts}  │  │  → {counts}  │            │     │
│  │  └──────────────┘  └──────────────┘  └──────────────┘            │     │
│  └──────────────────────────────────────────────────────────────────┘     │
│             │                │                │                           │
│   ┌─────────┴────────────────┴────────────────┘                          │
│   │  Service: mapper-headless (clusterIP: None)                           │
│   │  DNS: mapper-{0,1,2}.mapper-headless.mapreduce.svc.cluster.local      │
│   └──────────────────────────┬───────────────────────────────────────    │
│                              │  HTTP fan-out (GET /results per pod)       │
│                              ▼                                            │
│  ┌───────────────────────────────────────┐                                │
│  │      Deployment: reducer  (1 replica) │                                │
│  │      (topx.py --mode reducer)         │                                │
│  │                                       │                                │
│  │  1. fan-out → fetch each mapper's     │                                │
│  │     partial URL counts                │                                │
│  │  2. merge_counters()                  │                                │
│  │  3. top_x(merged, TOP_X=10)           │                                │
│  │                                       │                                │
│  │  GET /results → JSON top-X response   │                                │
│  └──────────────────┬────────────────────┘                                │
│                     │                                                      │
│  ┌──────────────────▼────────────────────┐                                │
│  │  Service: reducer-svc  (NodePort)     │                                │
│  │  port 8080 → nodePort 30080           │                                │
│  └──────────────────┬────────────────────┘                                │
└─────────────────────│──────────────────────────────────────────────────── ┘
                      │
                      ▼
          curl http://127.0.0.1:30080/results
```

---

## Project Structure

```
custom-map-reduce/
├── topx.py              # Mapper + Reducer Flask app (--mode mapper|reducer)
├── generate_data.py     # URL dataset generator (Zipf distribution)
├── requirements.txt     # Python dependencies (flask, requests, pytest)
├── Dockerfile           # Single image used by all pods
├── Makefile             # Build / deploy / query helpers
├── k8s/
│   ├── namespace.yaml          # Namespace: mapreduce
│   ├── data-job.yaml           # Job: data-generator
│   ├── mapper-headless-svc.yaml# Headless service for mapper DNS
│   ├── mapper-statefulset.yaml # StatefulSet: mapper (3 replicas)
│   ├── reducer-deploy.yaml     # Deployment: reducer (1 replica)
│   └── reducer-svc.yaml        # NodePort service: :30080
└── tests/
    ├── test_generate.py    # Unit tests for data generator
    ├── test_topx.py        # Unit tests for mapper/reducer logic
    └── test_integration.py # Integration tests against live cluster
```

---

## Key Design Decisions

| Decision | Detail |
|---|---|
| **StatefulSet for mappers** | Gives each pod a stable ordinal hostname (`mapper-0`, `mapper-1`, …) needed for byte-partition assignment |
| **Headless service** | Enables DNS lookup of individual pod addresses — reducer calls `mapper-{i}.mapper-headless` directly |
| **Byte partitioning** | The input CSV is split by byte offset (not line count), so each mapper seeks to its start/end without reading the whole file |
| **Single Docker image** | One image, two modes — the entrypoint arg (`--mode mapper` / `--mode reducer`) switches behaviour |
| **hostPath volume** | Simplest shared storage for a single-node (Rancher Desktop / minikube) setup |
| **Init container** | Mappers wait for `metadata.json` sentinel before starting, ensuring the data-generator Job finishes first |

---

## Prerequisites

- [Rancher Desktop](https://rancherdesktop.io/) (or minikube / Docker Desktop with Kubernetes enabled)
- `kubectl` configured for the local cluster
- Python 3.12+ (for running tests locally)

---

## Quick Start

### 1. Install Python dependencies (for local tests)

```bash
pip install -r requirements.txt
```

### 2. Build the Docker image

```bash
make build
```

> The image is built directly into the local Docker daemon that Kubernetes uses (`imagePullPolicy: Never`).

### 3. Run unit tests

```bash
make test
```

### 4. Deploy to Kubernetes

```bash
make deploy
```

This applies all manifests in order:
1. `namespace.yaml`
2. `data-job.yaml` → generates the dataset
3. `mapper-headless-svc.yaml` + `mapper-statefulset.yaml` → start mappers
4. `reducer-deploy.yaml` + `reducer-svc.yaml` → start reducer

### 5. Wait for everything to be ready

```bash
make wait-job       # waits for data-generator Job to complete
make wait-mappers   # waits for all 3 mapper pods to be Running
make wait-reducer   # waits for reducer Deployment rollout
```

### 6. Query the results

```bash
make query
```

Example response:
```json
{
  "top_x": 10,
  "total_unique_urls": 200,
  "total_url_hits": 10000000,
  "query_time_seconds": 0.42,
  "results": [
    {"url": "https://example.com/popular", "count": 1234567},
    ...
  ]
}
```

### 7. Check cluster status

```bash
make status
```

### 8. View logs

```bash
make logs-job       # data generator logs
make logs-mappers   # all mapper pods (prefixed by pod name)
make logs-reducer   # reducer logs
```

---

## Useful Make Targets

| Target | Description |
|---|---|
| `make build` | Build Docker image |
| `make test` | Run unit tests locally |
| `make deploy` | Apply all k8s manifests |
| `make wait-job` | Block until data-generator completes |
| `make wait-mappers` | Block until all 3 mappers are ready |
| `make wait-reducer` | Block until reducer is ready |
| `make query` | Fetch and pretty-print top-X results |
| `make status` | Show pods, services, and jobs |
| `make logs-job` | Tail data-generator logs |
| `make logs-mappers` | Tail all mapper logs |
| `make logs-reducer` | Tail reducer logs |
| `make clean` | Delete the entire `mapreduce` namespace |
| `make redeploy` | `build` → `clean` → `deploy` |

---

## HTTP API

Both mappers and the reducer expose the same Flask app on port **8080**.

| Method | Path | Mode | Description |
|---|---|---|---|
| GET | `/health` | both | Liveness probe — returns `{"status": "ok"}` |
| GET | `/status` | both | Readiness info (mapper includes pod name + rows processed) |
| GET | `/results` | mapper | Returns this pod's partial URL counts |
| GET | `/results` | reducer | Returns merged top-X URL list |

---

## Running Integration Tests

Integration tests require the live cluster to be running and the reducer NodePort to be reachable at `http://127.0.0.1:30080`.

```bash
pytest tests/test_integration.py -v
```

> Some tests are expected to fail until the MapReduce logic is implemented (the core counting/merging functions are stubs marked `TODO`).

---

## Environment Variables

| Variable | Used by | Default | Description |
|---|---|---|---|
| `PORT` | mapper, reducer | `8080` | Flask listen port |
| `NUM_PODS` | mapper | `3` | Total number of mapper pods |
| `DATA_FILE` | mapper | `/data/input.csv` | Path to the input CSV |
| `TOP_X` | mapper, reducer | `10` | Number of top URLs to return |
| `NUM_MAPPERS` | reducer | `3` | How many mappers to fan out to |
| `MAPPER_SVC` | reducer | `mapper-headless` | Headless service name for mapper DNS |
| `NAMESPACE` | reducer | `mapreduce` | Kubernetes namespace (for DNS construction) |
