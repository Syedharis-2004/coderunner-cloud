FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ .

EXPOSE 8000

# Use $PORT from Render if set, otherwise default to 8000
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
