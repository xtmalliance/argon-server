FROM --platform=linux/amd64 python:3.10-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -U pip && pip install -r requirements.txt

RUN addgroup --gid 10000 django  && adduser --shell /bin/bash --disabled-password --gecos "" --uid 10000 --ingroup django django
RUN chown -R django:django /app
USER django:django

COPY --chown=django:django . .

EXPOSE 8000
