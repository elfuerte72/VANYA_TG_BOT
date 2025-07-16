#!/bin/bash

# Deploy script for Vanya Telegram Bot
# Использование: ./deploy.sh [development|production]

set -e  # Остановка при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция логирования
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка аргументов
ENVIRONMENT=${1:-development}

if [[ "$ENVIRONMENT" != "development" && "$ENVIRONMENT" != "production" ]]; then
    log_error "Неверное окружение. Используйте: development или production"
    exit 1
fi

log "Начинаем деплой в режиме: $ENVIRONMENT"

# Проверка наличия Docker
if ! command -v docker &> /dev/null; then
    log_error "Docker не установлен!"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    log_error "Docker Compose не установлен!"
    exit 1
fi

# Проверка .env файла
if [ ! -f ".env" ]; then
    log_warning ".env файл не найден"
    if [ -f ".env.docker.example" ]; then
        log "Копируем .env.docker.example в .env"
        cp .env.docker.example .env
        log_warning "Отредактируйте .env файл с вашими настройками!"
        exit 1
    else
        log_error "Нет ни .env, ни .env.docker.example файла!"
        exit 1
    fi
fi

# Создание необходимых директорий
log "Создаем директории для данных и логов..."
mkdir -p data logs

# Выбор docker-compose файла
if [ "$ENVIRONMENT" = "production" ]; then
    COMPOSE_FILE="docker-compose.prod.yml"
    log "Используем продакшн конфигурацию: $COMPOSE_FILE"
else
    COMPOSE_FILE="docker-compose.yml"
    log "Используем dev конфигурацию: $COMPOSE_FILE"
fi

# Проверка наличия compose файла
if [ ! -f "$COMPOSE_FILE" ]; then
    log_error "Файл $COMPOSE_FILE не найден!"
    exit 1
fi

# Остановка существующих контейнеров
log "Останавливаем существующие контейнеры..."
docker-compose -f "$COMPOSE_FILE" down 2>/dev/null || true

# Очистка старых образов (опционально)
if [ "$ENVIRONMENT" = "production" ]; then
    log "Очищаем неиспользуемые Docker образы..."
    docker image prune -f
fi

# Сборка и запуск
log "Собираем и запускаем контейнеры..."
docker-compose -f "$COMPOSE_FILE" up --build -d

# Проверка статуса
sleep 5
log "Проверяем статус контейнеров..."
docker-compose -f "$COMPOSE_FILE" ps

# Проверка логов
log "Последние логи контейнера:"
docker-compose -f "$COMPOSE_FILE" logs --tail=20 vanya_tg_bot

# Проверка здоровья
log "Ждем запуска сервиса..."
sleep 10

if docker-compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
    log_success "Деплой завершен успешно!"
    log "Для просмотра логов: docker-compose -f $COMPOSE_FILE logs -f"
    log "Для остановки: docker-compose -f $COMPOSE_FILE down"
else
    log_error "Контейнер не запустился. Проверьте логи:"
    docker-compose -f "$COMPOSE_FILE" logs
    exit 1
fi