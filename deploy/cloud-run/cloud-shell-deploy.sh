#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-project-0fb33b45-8118-49ed-b8c}"
REGION="${REGION:-asia-east1}"
REPOSITORY="${REPOSITORY:-wearedge}"
SERVICE="${SERVICE:-wearedge-agent-service}"
IMAGE_TAG="${IMAGE_TAG:-$(date -u +%Y%m%d%H%M%S)}"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${SERVICE}:${IMAGE_TAG}"

gcloud config set project "${PROJECT_ID}"

gcloud services enable \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  run.googleapis.com

if ! gcloud artifacts repositories describe "${REPOSITORY}" --location "${REGION}" >/dev/null 2>&1; then
  gcloud artifacts repositories create "${REPOSITORY}" \
    --repository-format docker \
    --location "${REGION}" \
    --description "Wearedge Industrial AI Agent PoC images"
fi

gcloud builds submit . \
  --config deploy/cloud-run/cloudbuild.yaml \
  --substitutions "_REGION=${REGION},_REPOSITORY=${REPOSITORY},_SERVICE=${SERVICE},_IMAGE_TAG=${IMAGE_TAG}"

gcloud run deploy "${SERVICE}" \
  --image "${IMAGE}" \
  --region "${REGION}" \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --cpu 1 \
  --memory 512Mi \
  --max-instances 3 \
  --timeout 30 \
  --set-env-vars "WEAREDGE_AUTH_DISABLED=true,WEAREDGE_DEPLOYMENT_MODE=cloud_proxy,WEAREDGE_EDGE_NODE_ID=wearedge-cloud-run-poc,LLAMA_MODEL=wearedge-competition-decision-runtime,WEAREDGE_MODEL_VARIANT=deterministic-competition-runtime"

SERVICE_URL="$(gcloud run services describe "${SERVICE}" --region "${REGION}" --format 'value(status.url)')"
echo "WEAREDGE_CLOUD_RUN_URL=${SERVICE_URL}"
