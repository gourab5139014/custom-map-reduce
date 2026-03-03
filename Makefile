KUBECTL    := /opt/homebrew/bin/kubectl
DOCKER     := $(HOME)/.rd/bin/docker
NAMESPACE  := mapreduce
NODE_IP    := 127.0.0.1
NODE_PORT  := 30080
IMAGE      := mapreduce:latest
K8S_DIR    := k8s

.PHONY: all build test deploy wait-job wait-mappers wait-reducer query status clean redeploy

all: build test deploy

# --------------------------------------------------------------------------
# Build Docker image (directly into k8s-visible docker daemon)
# --------------------------------------------------------------------------
build:
	@echo "==> Building $(IMAGE)..."
	$(DOCKER) build -t $(IMAGE) .
	@echo "==> Build complete."

# --------------------------------------------------------------------------
# Run tests locally
# --------------------------------------------------------------------------
test:
	@echo "==> Running tests..."
	pytest tests/ -v

# --------------------------------------------------------------------------
# Deploy all manifests in dependency order
# --------------------------------------------------------------------------
deploy:
	@echo "==> Deploying to namespace $(NAMESPACE)..."
	$(KUBECTL) apply -f $(K8S_DIR)/namespace.yaml
	$(KUBECTL) apply -f $(K8S_DIR)/data-job.yaml
	$(KUBECTL) apply -f $(K8S_DIR)/mapper-headless-svc.yaml
	$(KUBECTL) apply -f $(K8S_DIR)/mapper-statefulset.yaml
	$(KUBECTL) apply -f $(K8S_DIR)/reducer-deploy.yaml
	$(KUBECTL) apply -f $(K8S_DIR)/reducer-svc.yaml
	@echo "==> Deploy complete."

# --------------------------------------------------------------------------
# Wait targets
# --------------------------------------------------------------------------
wait-job:
	@echo "==> Waiting for data-generator Job..."
	$(KUBECTL) wait job/data-generator -n $(NAMESPACE) --for=condition=complete --timeout=300s

wait-mappers:
	@echo "==> Waiting for mapper StatefulSet (3/3 ready)..."
	$(KUBECTL) rollout status statefulset/mapper -n $(NAMESPACE) --timeout=600s

wait-reducer:
	@echo "==> Waiting for reducer Deployment..."
	$(KUBECTL) rollout status deployment/reducer -n $(NAMESPACE) --timeout=120s

# --------------------------------------------------------------------------
# Query the reducer endpoint
# --------------------------------------------------------------------------
query:
	@echo "==> Querying reducer at $(NODE_IP):$(NODE_PORT)/results ..."
	curl -s http://$(NODE_IP):$(NODE_PORT)/results | python3 -m json.tool

# --------------------------------------------------------------------------
# Status overview
# --------------------------------------------------------------------------
status:
	@echo "==> Pods:"
	$(KUBECTL) get pods -n $(NAMESPACE) -o wide
	@echo ""
	@echo "==> Services:"
	$(KUBECTL) get svc -n $(NAMESPACE)
	@echo ""
	@echo "==> Jobs:"
	$(KUBECTL) get jobs -n $(NAMESPACE)

# --------------------------------------------------------------------------
# Logs
# --------------------------------------------------------------------------
logs-job:
	$(KUBECTL) logs job/data-generator -n $(NAMESPACE) --tail=50

logs-mappers:
	$(KUBECTL) logs -l app=mapper -n $(NAMESPACE) --prefix=true --tail=20

logs-reducer:
	$(KUBECTL) logs -l app=reducer -n $(NAMESPACE) --tail=50

# --------------------------------------------------------------------------
# Clean everything
# --------------------------------------------------------------------------
clean:
	@echo "==> Deleting namespace $(NAMESPACE)..."
	$(KUBECTL) delete namespace $(NAMESPACE) --ignore-not-found=true
	@echo "==> Done. Note: /tmp/mapreduce on the node is NOT removed automatically."

# --------------------------------------------------------------------------
# Full rebuild + redeploy cycle
# --------------------------------------------------------------------------
redeploy: build clean deploy
