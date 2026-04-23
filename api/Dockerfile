FROM python:3.11-alpine AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip==25.3.0  \
    && pip install --no-cache-dir --prefix=/install --requirement requirements.txt


FROM python:3.11-alpine AS final

# hadolint ignore=DL3018
RUN addgroup -S appgroup \
    && adduser -S -G appgroup appuser \
    && apk add --no-cache wget

WORKDIR /app

COPY --from=builder /install /usr/local
COPY main.py .

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
  CMD wget -qO- http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]