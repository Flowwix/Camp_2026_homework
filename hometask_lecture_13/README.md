# ETL Pipeline

Run the notebook pipeline with SQLite + PostgreSQL:

```bash
docker compose up --build
```

Run tests against notebook code:

```bash
docker compose run --build --rm etl pytest -v
```

Stop containers:

```bash
docker compose down
```

Stop and remove PostgreSQL data volume:

```bash
docker compose down -v
```

SQLite result: `data/pipeline.db`. PostgreSQL is available on `localhost:5432` (`etl` / `etl`). No virtual environment is needed for Docker.
