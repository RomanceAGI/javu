# ---------- base ----------
FROM python:3.11-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git && rm -rf /var/lib/apt/lists/*
WORKDIR /app

# ---------- deps ----------
FROM base AS deps
# pilih salah satu manajer dependency:
# 1) Poetry (pakai pyproject.toml) — REKOMENDASI
COPY pyproject.toml ./
RUN pip install -U pip poetry && poetry config virtualenvs.create false
COPY . .
RUN poetry install --no-root --no-interaction --no-ansi

# Jika ingin pakai requirements.txt (alternatif):
# COPY requirements.txt ./
# RUN pip install -U pip && pip install -r requirements.txt

# ---------- runtime ----------
FROM base AS runtime
RUN useradd -m -u 10001 app
WORKDIR /app
COPY --from=deps /usr/local /usr/local
COPY . .
RUN mkdir -p /data/logs /data/runtime /data/db && chown -R app:app /data
USER app
ENV PYTHONPATH=/app
HEALTHCHECK --interval=30s --timeout=5s --retries=5 CMD python -m javu_agi.core health || exit 1
ENTRYPOINT ["python","-m","javu_agi.core","run","loop"]
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONUNBUFFERED=1
CMD ["python","api.py"]
