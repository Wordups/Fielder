# Fielder onboarding/intake backend — deploys on any Docker host (Render, Railway, Fly.io).
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Hosts inject $PORT at runtime; default to 8000 for local `docker run`.
ENV PORT=8000
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT}"]
