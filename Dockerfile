# Dockerfile для Railway deployment
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости (минимальные для Railway)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Копируем файлы зависимостей для Railway
COPY requirements.railway.txt requirements.txt

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY src/ ./src/
COPY run.py .

# Создаем директории для данных и логов
RUN mkdir -p /app/data /app/logs

# Устанавливаем переменные окружения
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Railway автоматически назначает порт, но мы можем указать дефолтный
EXPOSE 8000

# Команда запуска
CMD ["python", "run.py"]