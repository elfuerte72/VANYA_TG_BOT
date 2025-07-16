# Makefile для удобного управления Docker контейнерами

.PHONY: help build up down logs dev prod clean restart status

# Переменные
COMPOSE_FILE_DEV = docker-compose.yml
COMPOSE_FILE_PROD = docker-compose.prod.yml
PROJECT_NAME = vanya_tg_bot

help: ## Показать справку
	@echo "Доступные команды:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Собрать Docker образ
	docker-compose -f $(COMPOSE_FILE_DEV) build

up: ## Запустить в development режиме
	docker-compose -f $(COMPOSE_FILE_DEV) up -d

down: ## Остановить контейнеры
	docker-compose -f $(COMPOSE_FILE_DEV) down
	docker-compose -f $(COMPOSE_FILE_PROD) down 2>/dev/null || true

logs: ## Показать логи
	docker-compose -f $(COMPOSE_FILE_DEV) logs -f

dev: ## Запустить в development режиме с логами
	docker-compose -f $(COMPOSE_FILE_DEV) up --build

prod: ## Запустить в production режиме
	docker-compose -f $(COMPOSE_FILE_PROD) up --build -d

restart: ## Перезапустить контейнеры
	$(MAKE) down
	$(MAKE) up

status: ## Показать статус контейнеров
	docker-compose -f $(COMPOSE_FILE_DEV) ps
	docker-compose -f $(COMPOSE_FILE_PROD) ps 2>/dev/null || true

clean: ## Очистить неиспользуемые ресурсы Docker
	docker system prune -f
	docker image prune -f

setup: ## Первоначальная настройка (создание .env из примера)
	@if [ ! -f .env ]; then \
		cp .env.docker.example .env; \
		echo "Создан .env файл из .env.docker.example"; \
		echo "Отредактируйте .env файл с вашими настройками!"; \
	else \
		echo ".env файл уже существует"; \
	fi

update-req: ## Обновить requirements.txt из pyproject.toml
	./update_requirements.sh

# Алиасы для удобства
start: up ## Алиас для up
stop: down ## Алиас для down