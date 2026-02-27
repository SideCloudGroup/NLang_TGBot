FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY nlang_bot.py ./
COPY pyproject.toml ./
RUN pip install --no-cache-dir .

CMD ["python", "nlang_bot.py"]
