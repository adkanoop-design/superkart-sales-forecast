#!/usr/bin/env bash
# Build and run the SuperKart backend + frontend containers on a shared Docker network
set -e

docker network create superkart-net 2>/dev/null || echo "Network superkart-net already exists"
docker rm -f superkart-backend superkart-frontend 2>/dev/null || true

docker build -t superkart-backend ./backend_files
docker build -t superkart-frontend ./frontend_files

docker run -d --name superkart-backend  --network superkart-net -p 7860:7860 superkart-backend
docker run -d --name superkart-frontend --network superkart-net -p 8501:8501 \
  -e BACKEND_URL=http://superkart-backend:7860 superkart-frontend

docker ps
echo "Backend API : port 7860  |  Streamlit UI : port 8501  (see the Ports tab)"
