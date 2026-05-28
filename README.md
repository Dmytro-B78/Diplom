# NT-Tech Trading Bot — Дипломный проект
## Автоматизация тестирования Python-приложений

[![Tests](https://github.com/Dmytro-B78/Diplom/actions/workflows/tests.yml/badge.svg)](https://github.com/Dmytro-B78/Diplom/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/Dmytro-B78/Diplom/branch/master/graph/badge.svg)](https://codecov.io/gh/Dmytro-B78/Diplom)

**Объект исследования:** спотовый торговый бот NT-Tech (LiveEngine 5.8)  
**Биржа:** Binance Spot API  
**Стек тестирования:** pytest, pytest-mock, pytest-cov, GitHub Actions

## Структура проекта

```
Diplom/
├── src/
│   └── stubs/          ← заглушки/копии модулей из NT для тестов
├── tests/
│   ├── unit/           ← юнит-тесты отдельных компонентов
│   ├── integration/    ← интеграционные тесты
│   └── mocks/          ← моки Binance API
├── docs/               ← главы диплома (Markdown)
├── reports/            ← coverage HTML-отчёты
├── conftest.py         ← общие фикстуры pytest
├── pytest.ini          ← конфигурация pytest
├── requirements.txt    ← зависимости
└── .github/
    └── workflows/
        └── tests.yml   ← CI/CD GitHub Actions
```

## Запуск тестов

```bash
# Все тесты
pytest

# С coverage отчётом
pytest --cov=src --cov-report=html

# Только unit-тесты
pytest tests/unit/ -v

# Только интеграционные
pytest tests/integration/ -v
```

## Реальные баги, найденные в live (кейсы для диплома)

| Баг | Компонент | Где нашли | Новый тест |
|-----|-----------|-----------|------------|
| min_stop_pct floor (TRXUSDT ~71% notional) | risk_guard.py | Live trading | `tests/unit/test_risk_guard.py` |
| pnl_pct использовал trigger вместо fill price | exit_intelligence.py | Live trading v5.7 | `tests/unit/test_exit_intelligence.py` |
| ABS_STOP cooldown BUG-3 | entry_engine.py | Live trading | `tests/unit/test_entry_engine.py` |
```