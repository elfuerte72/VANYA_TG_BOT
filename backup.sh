#!/bin/bash

# Backup script for Vanya Telegram Bot
# Создает резервные копии базы данных и логов

set -e

# Настройки
PROJECT_DIR="/opt/vanya_tg_bot"  # Измените на ваш путь
BACKUP_DIR="$PROJECT_DIR/backups"
DB_PATH="$PROJECT_DIR/data/users.db"
LOGS_DIR="$PROJECT_DIR/logs"
RETENTION_DAYS=30  # Количество дней хранения бэкапов

# Цвета для логирования
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Создание директории для бэкапов
mkdir -p "$BACKUP_DIR"

# Получение текущей даты
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

log "Начинаем создание резервной копии..."

# Бэкап базы данных
if [ -f "$DB_PATH" ]; then
    DB_BACKUP="$BACKUP_DIR/users_db_backup_$TIMESTAMP.db"
    cp "$DB_PATH" "$DB_BACKUP"
    log "База данных скопирована в: $DB_BACKUP"
    
    # Проверка целостности копии
    if [ -f "$DB_BACKUP" ]; then
        DB_SIZE=$(stat -c%s "$DB_PATH")
        BACKUP_SIZE=$(stat -c%s "$DB_BACKUP")
        
        if [ "$DB_SIZE" -eq "$BACKUP_SIZE" ]; then
            log "Проверка целостности бэкапа БД прошла успешно"
        else
            log_error "Размеры файлов не совпадают! Оригинал: $DB_SIZE, Бэкап: $BACKUP_SIZE"
            exit 1
        fi
    fi
else
    log_warning "База данных не найдена по пути: $DB_PATH"
fi

# Бэкап логов (если нужно)
if [ -d "$LOGS_DIR" ] && [ "$(ls -A $LOGS_DIR)" ]; then
    LOGS_BACKUP="$BACKUP_DIR/logs_backup_$TIMESTAMP.tar.gz"
    tar -czf "$LOGS_BACKUP" -C "$LOGS_DIR" .
    log "Логи заархивированы в: $LOGS_BACKUP"
else
    log_warning "Директория логов пуста или не найдена: $LOGS_DIR"
fi

# Бэкап конфигурации
if [ -f "$PROJECT_DIR/.env" ]; then
    ENV_BACKUP="$BACKUP_DIR/env_backup_$TIMESTAMP"
    # Копируем .env файл, но удаляем из него секретные данные для безопасности
    sed 's/=.*/=***HIDDEN***/' "$PROJECT_DIR/.env" > "$ENV_BACKUP"
    log "Конфигурация (без секретов) скопирована в: $ENV_BACKUP"
fi

# Удаление старых бэкапов
log "Удаляем бэкапы старше $RETENTION_DAYS дней..."
find "$BACKUP_DIR" -name "*backup*" -type f -mtime +$RETENTION_DAYS -exec rm -f {} \;

# Статистика
BACKUP_COUNT=$(ls -1 "$BACKUP_DIR" | wc -l)
BACKUP_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)

log "Бэкап завершен успешно!"
log "Всего файлов бэкапа: $BACKUP_COUNT"
log "Общий размер: $BACKUP_SIZE"
log "Местоположение: $BACKUP_DIR"

# Опционально: отправка уведомления
# Раскомментируйте для отправки уведомления в Telegram
# curl -s -X POST "https://api.telegram.org/bot$BOT_TOKEN/sendMessage" \
#     -d chat_id="$ADMIN_CHAT_ID" \
#     -d text="✅ Бэкап Vanya TG Bot выполнен успешно
# Файлов: $BACKUP_COUNT
# Размер: $BACKUP_SIZE"