# Lightweight Python base image
FROM python:3.12-slim

# OpenMP runtime used by XGBoost / scikit-learn
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies first so this layer is cached between code changes
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy the Flask app and the serialized model
COPY . .

EXPOSE 7860

# Serve the Flask app with gunicorn (production WSGI server): 2 workers on port 7860
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:7860", "--timeout", "120", "app:superkart_api"]
