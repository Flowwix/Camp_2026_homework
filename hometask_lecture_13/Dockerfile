FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN useradd --create-home --shell /usr/sbin/nologin appuser

COPY requirements.txt .
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

COPY --chown=appuser:appuser etl_pipeline.ipynb .
COPY --chown=appuser:appuser tests ./tests
COPY --chown=appuser:appuser data/raw ./data/raw

RUN mkdir -p /app/data \
    && chown -R appuser:appuser /app

USER appuser

CMD ["jupyter", "nbconvert", "--to", "notebook", "--execute", "etl_pipeline.ipynb", "--output", "executed_etl_pipeline.ipynb"]
