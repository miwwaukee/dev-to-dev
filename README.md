
```markdown
# DevHelper MCP Server 🛠️

MCP-сервер с инструментами для ежедневной работы разработчика.

## 🎯 Что решает
| Проблема | Решение |
|----------|---------|
| Технический долг | Поиск TODO/FIXME с приоритизацией |
| Уязвимые зависимости | Локальная проверка без внешних API |

**Инструменты:** `find_tech_debt`, `check_dependencies`

## 🚀 Быстрый старт

```
### 1. Сборка образа
```bash
docker build -t devhelper-mcp .
```

### 2. Запуск сервера
```bash
docker run -p 8000:8000 devhelper-mcp serve
```

### 3. Проверка здоровья
```bash
curl http://localhost:8000/health
```
**Ответ:** `{"status":"ok","service":"devhelper-mcp","version":"1.0.0"}`

### 4. Smoke-тест
```bash
docker run devhelper-mcp smoke
```
**Ответ:** `✅ Smoke test passed!`

### 5. Подключение
MCP Inspector URL: `http://localhost:8000/mcp`

## 🧰 Инструменты

### `find_tech_debt`
**Параметры:** `path` (обяз), `extensions`, `min_priority`
**Пример:**
```bash
curl -X POST http://localhost:8000/mcp -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"find_tech_debt","arguments":{"path":"./demo_project","min_priority":"medium"}}}'
```

### `check_dependencies`
**Параметры:** `manifest_path` (обяз), `license_policy`, `check_vulnerabilities`
**Пример:**
```bash
curl -X POST http://localhost:8000/mcp -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"check_dependencies","arguments":{"manifest_path":"./demo_project/requirements.txt"}}}'
```

## ⚠️ Ограничения
- Поддержка: Python (requirements.txt), JS (package.json)
- Без внешних API (локальная база уязвимостей)

## 🆘 Troubleshooting
- Порт занят: `docker run -p 8001:8000 devhelper-mcp serve`
- Ошибка сборки: Проверьте запуск Docker Desktop
```
