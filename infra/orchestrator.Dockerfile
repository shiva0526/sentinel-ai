FROM python:3.10-slim
WORKDIR /app

# Install dependencies
COPY orchestrator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY sentinel_core/ /app/sentinel_core/
COPY shared/ /app/shared/
COPY orchestrator/ /app/orchestrator/

EXPOSE 8000
CMD ["python", "-m", "orchestrator.app.main"]
