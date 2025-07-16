#!/bin/bash

echo "🚀 Подготовка к деплою на Railway..."

# Проверяем наличие необходимых файлов
if [ ! -f "requirements.railway.txt" ]; then
    echo "❌ Файл requirements.railway.txt не найден"
    exit 1
fi

if [ ! -f "Dockerfile" ]; then
    echo "❌ Файл Dockerfile не найден"
    exit 1
fi

# Создаем временную копию основных файлов для Railway
echo "📦 Создаем резервную копию requirements.txt..."
if [ -f "requirements.txt" ]; then
    cp requirements.txt requirements.txt.backup
fi

# Заменяем requirements.txt на Railway-версию
cp requirements.railway.txt requirements.txt

echo "✅ Файлы подготовлены для Railway deployment"
echo ""
echo "📋 Следующие шаги:"
echo "1. Убедитесь, что все переменные окружения настроены в Railway:"
echo "   - BOT_TOKEN"
echo "   - OPENAI_API_KEY"
echo "   - TELEGRAM_CHANNEL_ID"
echo "   - DATABASE_SECRET_KEY (можно оставить пустым для Railway)"
echo "   - LOG_LEVEL=INFO"
echo ""
echo "2. Выполните деплой в Railway"
echo ""
echo "3. После деплоя запустите restore.railway.sh для восстановления локальных файлов"

# Создаем скрипт для восстановления
cat > restore.railway.sh << 'EOF'
#!/bin/bash
echo "🔄 Восстановление локальных файлов..."

if [ -f "requirements.txt.backup" ]; then
    mv requirements.txt.backup requirements.txt
    echo "✅ requirements.txt восстановлен"
else
    echo "⚠️  Резервная копия requirements.txt не найдена"
fi

echo "✅ Локальные файлы восстановлены"
EOF

chmod +x restore.railway.sh

echo "✅ Скрипт восстановления создан: restore.railway.sh"