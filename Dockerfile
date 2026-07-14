FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ backend/
COPY frontend/ frontend/

# 영구 디스크가 마운트되지 않은 환경(로컬 docker run 등)에서도 최소한 컨테이너 안에서는 동작하도록 기본값 유지.
ENV DATA_DIR=/app/output

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
