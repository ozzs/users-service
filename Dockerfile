FROM python:3.10-slim
WORKDIR /app

RUN pip3 install poetry

COPY poetry.lock pyproject.toml ./

RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi --only main --no-root

COPY . .

WORKDIR /app/src
