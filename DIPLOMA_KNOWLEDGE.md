# DIPLOMA_KNOWLEDGE.md
# NT-Tech Trading Bot — Дипломный проект
# Автоматизация тестирования Python-приложений
# Последнее обновление: 2026-06-02

---

## СТАТУС ПРОЕКТА

**Фаза:** 4 — Написание диплома
**Тесты:** 206/206 passed (локально Windows + Linux CI)
**Coverage:** 89% (локально) / 85% (Codecov)
**Написано:** Введение ✅ | Диплом v16 финальная версия ✅

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
| Python (тесты) | pytest 8.3.5, pytest-mock 3.14.0, pytest-cov 6.1.0, pytest-asyncio 0.25.0 |

---

## ОБЪЕКТ ИССЛЕДОВАНИЯ: LiveEngine 5.8

### Компоненты бота и покрытие тестами

| Файл | Назначение | NT/tests (130) | Diplom/tests |
|------|-----------|----------------|--------------|
| live_engine.py | Основной движок | Нет | Нет |
| risk_guard.py | Риск-менеджмент, kill-switch | 23 теста | 30 тестов ✅ |
| live_loop.py | Event loop, WebSocket candles | Нет | 8 тестов (mock WS) |
| stage1.py | Entry gate (4H alignment) | Нет | 23 теста (параметризованные) |
| entry_engine.py | Логика входа | Нет | 15 тестов (BUG-3 cooldown) |
| intrabar_stops.py | Stop-loss логика | 21 тест | 13 тестов |
| exit_intelligence.py | Интеллектуальный выход | НОЛЬ | 17 тестов (ключевой вклад!) |
| trail_engine.py | Trailing stop | 27 тестов | 30 тестов ✅ (новый) |
| indicators.py | EMA, ATR, update_indicators | Нет | 28 тестов ✅ (новый) |
| meta_strategy.py | Основная стратегия | 13 тестов | 15 тестов ✅ (новый) |
| offline_runner.py | CSV loader, intrabar, trade record | 27 тестов | 23 теста ✅ (новый) |
| scripts/run_bt.py | Backtest | Нет | Нет |

---

## РЕАЛЬНЫЕ БАГИ (ключевые кейсы диплома)

### Баг 1: min_stop_pct floor — TRXUSDT
- Компонент: risk_guard.py — compute_position_size()
- Суть: при низком ATR позиция становилась огромной (без floor)
- Обнаружен: в live-торговле, не тестами
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
### 2. Специфика проекта ✅
### 3. Планирование тестирования ✅
### 4. Тестовая документация ✅
### 5. Автоматизация тестирования ✅
### 6. Проблемы и решения ✅
### 7. Итоги работы ✅
### 8. Заключение ✅
### 9. Приложения ✅
**Файл:** Диплом_NT-Tech_Бердников_v18.docx — финальная версия

---

## СТРУКТУРА РЕПОЗИТОРИЯ

Diplom/
  conftest.py               (sys.path NT подключен)
  pytest.ini
  requirements.txt
  README.md                 (badges: CI passing + Codecov 85%)
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
      test_risk_guard.py          (30 тестов — расширен)
      test_intrabar_stops.py      (13 тестов)
      test_exit_intelligence.py   (17 тестов — ключевой вклад)
      test_stage1.py              (23 теста — параметризованные)
      test_entry_engine.py        (15 тестов — BUG-3)
      test_trail_engine.py        (30 тестов — новый)
      test_indicators.py          (28 тестов — новый)
      test_meta_strategy.py       (15 тестов — новый)
      test_offline_runner.py      (23 теста — новый)
    integration/
      test_mock_binance_api.py    (7 тестов — network timeout)
      test_websocket.py           (8 тестов — mock WS)
    mocks/
  docs/
  reports/htmlcov/              (HTML coverage отчёт, в .gitignore)
  .github/workflows/tests.yml   (CI/CD GitHub Actions + Codecov + NT deploy key)

---

## ТЕКУЩИЕ МЕТРИКИ

| Метрика | Значение |
|---------|----------|
| Всего тестов (Diplom) | 206 |
| Unit-тестов | 183 |
| Integration-тестов | 15 |
| Passed | 206/206 (100%) |
| Coverage (локально) | 89% |
| Coverage (Codecov) | 85% |
| Время выполнения | ~0.50s (local) / ~29s (CI) |
| CI/CD | GitHub Actions passing ✅ + Codecov 85% |
| Репозиторий | https://github.com/Dmytro-B78/Diplom |
| Тестов в NT/tests | 130 |
| Новых файлов тестов добавлено | 4 (trail_engine, indicators, meta_strategy, offline_runner) |
| Расширенных файлов | 1 (risk_guard: 6 → 30) |
| HTML coverage отчёт | reports/htmlcov/index.html |

---

## CI/CD ИНФРАСТРУКТУРА

- GitHub Actions: ubuntu-latest, Python 3.11
- NT репо клонируется в CI через SSH deploy key (secret: NT_DEPLOY_KEY)
- PYTHONPATH установлен на /NT для доступа к bot_ai.*
- Codecov: автоматический upload coverage.xml

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
