FROM python:3.11-slim

RUN pip install poetry
WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi
COPY . .

EXPOSE 5000

CMD ["poetry", "run", "gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "ygg_rss_proxy.proxy:app"]
