# Event Bot - Управление мероприятиями в Discord

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![Discord.py](https://img.shields.io/badge/discord.py-2.0%2B-orange)
![License](https://img.shields.io/badge/license-MIT-green)

**Event Bot** - профессиональный инструмент для организации и управления мероприятиями на вашем Discord-сервере.

## 🌟 Основные возможности

### 📅 Управление ивентами
- Создание мероприятий с гибкими настройками
- Автоматические напоминания участникам
- Система регистрации и подтверждения участия

### ⚙️ Технологии
- Python 3.8+ с использованием discord.py
- Модульная система команд (cogs)
- Легкая настройка через конфигурационный файл

## 🚀 Быстрый старт

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Настройте бота:
```python
# В config.py
TOKEN = "ваш_токен_бота"
PREFIX = "!"
EVENT_CHANNEL = 123456789  # ID канала для ивентов
```

3. Запустите:
```bash
python event.py
```

## 📂 Структура проекта
```
├── cogs/
│   └── event.py - Основной модуль управления ивентами
├── event.py - Главный файл бота
└── requirements.txt - Зависимости
```

Разработано с ❤️ для Discord-сообществ. Лицензия MIT.
