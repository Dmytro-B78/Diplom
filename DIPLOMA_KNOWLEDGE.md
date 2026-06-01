# DIPLOMA_KNOWLEDGE.md
# NT-Tech Trading Bot — Дипломный проект
# Автоматизация тестирования Python-приложений
# Последнее обновление: 2026-05-31

---

## СТАТУС ПРОЕКТА

**Фаза:** 4 — Написание диплома
**Тесты:** 86/86 passed (локально Windows + Linux CI)
**Coverage:** 89% (локально) / ~84% (Codecov)
**Написано:** Введение ✅ | п.2 Специфика — в работе

---

## ОКРУЖЕНИЕ

| Параметр | Значение |
|----------|----------|
| OS | Windows, Python 3.13.1 |
| Дипломный проект | C:\TradingBots\Diplom\ |
| Бот (локально) | C:\TradingBots\NT\ |
| Бот (production) | VPS Contabo /home/ubuntu/NT/ |
| Сервис | systemd nttech.service |
| Репозиторий бота | https://github.com/Dmytro-B78/NT (private) |
| Репозиторий диплома | https://github.com/Dmytro-B78/Diplom (public) |
| Python (тесты) | pytest 8.3.5, pytest-mock 3.14.0, pytest-cov 6.1.0 |

---

## ОБЪЕКТ ИССЛЕДОВАНИЯ: LiveEngine 5.8

### Компоненты бота и покрытие тестами

| Файл | Назначение | NT/tests (130) | Diplom/tests |
|------|-----------|----------------|--------------|
| live_engine.py | Основной движок | Нет | Нет |
| risk_guard.py | Риск-менеджмент, kill-switch | 23 теста | 6 тестов |
| live_loop.py | Event loop, WebSocket candles | Нет | 8 тестов (mock WS) |
| stage1.py | Entry gate (4H alignment) | Нет | 23 теста (параметризованные) |
| entry_engine.py | Логика входа | Нет | 15 тестов (BUG-3 cooldown) |
| intrabar_stops.py | Stop-loss логика | 21 тест | 13 тестов |
| exit_intelligence.py | Интеллектуальный выход | НОЛЬ | 17 тестов (ключевой вклад!) |
| trail_engine.py | Trailing stop | 27 тестов | Нет (покрыто в NT) |
| scripts/run_bt.py | Backtest | Нет | Нет |

---

## РЕАЛЬНЫЕ БАГИ (ключевые кейсы диплома)

### Баг 1: min_stop_pct floor — TRXUSDT
- Компонент: risk_guard.py — compute_position_size()
- Суть: при низком ATR позиция становилась огромной (без floor)
- Обнаружен: в live-торговле, не в тестами
- Исправление: min_distance = price * self.min_stop_pct (2%)
- Тест: tests/unit/test_risk_guard.py

### Баг 2: pnl_pct — trigger вместо fill price (v5.7)
- Компонент: exit_intelligence.py — _build_exit()
- Суть: exit_price брался из trigger_price вместо meta_state["close"]
- Обнаружен: в live-торговле v5.7
- Исправление: "exit_price": float(meta_state["close"])
- Тест: tests/unit/test_exit_intelligence.py::TestExitPriceFix::test_exit_price_is_close_not_trigger

### Баг 3: ABS_STOP cooldown — BUG-3
- Компонент: entry_engine.py — compute_entry_signal()
- Суть: после ABS_STOP бот сразу открывал новую позицию против движения
- Исправление: 8-барный cooldown после ABS_STOP
- Тест: tests/unit/test_entry_engine.py::TestAbsStopCooldown

---

## СТРУКТУРА ДИПЛОМА (по шаблону QA)

### 1. Введение ✅ НАПИСАНО
- Описание проекта: NT-Tech LiveEngine 5.8, торговый бот на Python
- Цель: покрыть 3 компонента без тестов, поймать реальные баги
- Задачи: анализ покрытия → stubs → тесты → CI/CD → документация

### 2. Специфика проекта — В РАБОТЕ
- Что за проект: алготрейдинг-бот, Binance, WebSocket, production VPS
- Основной функционал: 8 компонентов, поток данных
- Что тестируется: exit_intelligence, stage1, entry_engine + интеграция
- Что НЕ тестируется: live_engine (оркестратор), trail_engine (покрыт в NT)

### 3. Планирование тестирования
- Тест-план: цель, scope, виды тестов, инструменты, риски
- Виды: unit (71), integration (15)
- Инструменты: pytest, pytest-mock, pytest-cov, GitHub Actions, Codecov
- Риски: нет тестового окружения → решение: stubs

### 4. Тестовая документация
- 3 баг-репорта (реальные баги из production)
- Примеры тест-кейсов (позитивные/негативные)
- Чек-лист покрытия по компонентам

### 5. Автоматизация тестирования
- Теория: unit vs integration, pytest (фикстуры, параметризация, моки)
- Инфраструктура: stubs, conftest.py, pytest.ini
- Ключевые тест-кейсы с кодом по каждому компоненту
- CI/CD: GitHub Actions + Codecov

### 6. Проблемы и решения
- Нет тестового окружения → stubs вместо реального бота
- WebSocket нельзя поднять в CI → pytest-mock + asyncio
- Реальные файлы NT подключены через sys.path в conftest.py

### 7. Итоги работы
- 86 тестов, 89% coverage, CI passing, ~0.15s local / ~29s CI
- Таблица: метрики до/после
- Какие баги поймали бы раньше

### 8. Заключение
- Что дала работа, рекомендации (live_engine, trail_engine)

### 9. Приложения
- Код тестов (ключевые фрагменты)
- HTML coverage отчёт
- Ссылка: https://github.com/Dmytro-B78/Diplom

---

## СТРУКТУРА РЕПОЗИТОРИЯ

Diplom/
  conftest.py               (sys.path NT подключен)
  pytest.ini
  requirements.txt
  README.md                 (badges: CI passing + Codecov 84%)
  DIPLOMA_KNOWLEDGE.md
  src/stubs/
    risk_guard_stub.py
    intrabar_stops_stub.py
    exit_intelligence_stub.py
    stage1_stub.py
    entry_engine_stub.py
    live_loop_stub.py
  tests/
    unit/
      test_risk_guard.py          (6 тестов)
      test_intrabar_stops.py      (13 тестов)
      test_exit_intelligence.py   (17 тестов — ключевой вклад)
      test_stage1.py              (23 теста — параметризованные)
      test_entry_engine.py        (15 тестов — BUG-3)
    integration/
      test_mock_binance_api.py    (7 тестов — network timeout)
      test_websocket.py           (8 тестов — mock WS)
    mocks/
  docs/
  reports/htmlcov/              (HTML coverage отчёт, в .gitignore)
  .github/workflows/tests.yml   (CI/CD GitHub Actions + Codecov)

---

## ТЕКУЩИЕ МЕТРИКИ

| Метрика | Значение |
|---------|----------|
| Всего тестов (Diplom) | 86 |
| Unit-тестов | 71 |
| Integration-тестов | 15 |
| Passed | 86/86 (100%) |
| Coverage (локально) | 89% |
| Coverage (Codecov) | ~84% |
| Время выполнения | ~0.15s (local) / ~29s (CI) |
| CI/CD | GitHub Actions passing + Codecov 84% |
| Репозиторий | https://github.com/Dmytro-B78/Diplom |
| Тестов в NT/tests | 130 |
| Компонентов без тестов в NT | 3 (exit_intelligence, stage1, entry_engine) |
| Реальных файлов NT подключено | 6 |
| HTML coverage отчёт | reports/htmlcov/index.html |

---

## КАК ИСПОЛЬЗОВАТЬ ЭТОТ ФАЙЛ

При начале новой сессии с Claude — вставь содержимое этого файла в чат.
Обновляй статус написанных разделов после каждой сессии.

---

## БЫСТРЫЕ КОМАНДЫ

python -m pytest tests/ -v
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v
python -m pytest --cov=src --cov-report=term-missing
python -m pytest --cov=src --cov-report=html:reports/htmlcov
start reports\htmlcov\index.html
git add . && git commit -m "feat: ..." && git push