
FROM python:3.11-alpine AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip==25.3.0  \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt


FROM python:3.11-alpine AS final

RUN addgroup -S appgroup \
    && adduser -S -G appgroup appuser

WORKDIR /app

COPY --from=builder /install /usr/local
COPY worker.py .

USER appuser

HEALTHCHECK --interval=20s --timeout=5s --start-period=15s --retries=3 \
  CMD python3 -c "import redis, os; r=redis.Redis(host=os.environ.get('REDIS_HOST','redis'),password=os.environ.get('REDIS_PASSWORD',None)); r.ping()"

CMD ["python", "worker.py"]