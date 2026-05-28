# DIPLOMA_KNOWLEDGE.md
# NT-Tech Trading Bot — Дипломный проект
# Автоматизация тестирования Python-приложений
# Последнее обновление: 2026-05-28

---

## СТАТУС ПРОЕКТА

**Фаза:** 3 — Расширение покрытия (в процессе)
**Тесты:** 74/74 passed (локально Windows + Linux CI)
**Coverage:** ~84% (Codecov)
**Следующий шаг:** Mock WebSocket, HTML отчёт, sys.path

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
| live_loop.py | Event loop, WebSocket candles | Нет | Нет |
| stage1.py | Entry gate (4H alignment) | Нет | 23 теста (параметризованные) |
| entry_engine.py | Логика входа | Нет | 15 тестов (BUG-3 cooldown) |
| intrabar_stops.py | Stop-loss логика | 21 тест | 10 тестов |
| exit_intelligence.py | Интеллектуальный выход | НОЛЬ | 17 тестов (ключевой вклад!) |
| trail_engine.py | Trailing stop | 27 тестов | Нет (покрыто в NT) |
| scripts/run_bt.py | Backtest | Нет | Нет |

---

## РЕАЛЬНЫЕ БАГИ (ключевые кейсы диплома)

### Баг 1: min_stop_pct floor — TRXUSDT
- Компонент: risk_guard.py — compute_position_size()
- Тест: tests/unit/test_risk_guard.py

### Баг 2: pnl_pct — trigger вместо fill price (v5.7)
- Компонент: exit_intelligence.py — _build_exit()
- Тест: tests/unit/test_exit_intelligence.py::TestExitPriceFix::test_exit_price_is_close_not_trigger

### Баг 3: ABS_STOP cooldown — BUG-3
- Компонент: entry_engine.py — compute_entry_signal()
- Тест: tests/unit/test_entry_engine.py::TestAbsStopCooldown

---

## СТРУКТУРА ДИПЛОМНОГО ПРОЕКТА

Diplom/
  conftest.py
  pytest.ini
  requirements.txt
  README.md
  DIPLOMA_KNOWLEDGE.md
  src/stubs/
    risk_guard_stub.py
    intrabar_stops_stub.py
    exit_intelligence_stub.py
    stage1_stub.py
    entry_engine_stub.py
  tests/
    unit/
      test_risk_guard.py          (6 тестов)
      test_intrabar_stops.py      (10 тестов)
      test_exit_intelligence.py   (17 тестов)
      test_stage1.py              (23 теста, параметризованные)
      test_entry_engine.py        (15 тестов, BUG-3)
    integration/
      test_mock_binance_api.py    (3 теста)
    mocks/
  docs/
  reports/
  .github/workflows/tests.yml

---

## ПЛАН РАБОТЫ ПО ФАЗАМ

### ФАЗА 1 — ЗАВЕРШЕНА
### ФАЗА 2 — ЗАВЕРШЕНА

### ФАЗА 3 — Расширение покрытия
- [x] Coverage badge в README
- [x] Параметризованные тесты (pytest.mark.parametrize) для stage1
- [x] Тесты entry_engine (BUG-3 cooldown, reentry, breakout)
- [ ] Mock WebSocket для live_loop.py
- [ ] Граничный случай: network timeout
- [ ] HTML coverage отчёт в reports/
- [ ] Добавить C:\TradingBots\NT\ в sys.path для прямого импорта

### ФАЗА 4 — Написание диплома
Глава 1 — Теоретические основы
Глава 2 — Объект исследования
Глава 3 — Практическая часть
Глава 4 — Результаты

---

## ТЕКУЩИЕ МЕТРИКИ

| Метрика | Значение |
|---------|----------|
| Всего тестов (Diplom) | 74 |
| Unit-тестов | 71 |
| Integration-тестов | 3 |
| Passed | 74/74 (100%) |
| Coverage (Codecov) | ~84% |
| Время выполнения | ~0.18s (local) / 29s (CI) |
| CI/CD | GitHub Actions passing + Codecov 84% |
| Репозиторий | https://github.com/Dmytro-B78/Diplom |
| Тестов в NT/tests | 130 |
| Реальных файлов NT подключено | 5 |

---

## КАК ИСПОЛЬЗОВАТЬ ЭТОТ ФАЙЛ

При начале новой сессии с Claude — вставь содержимое этого файла в чат.
Обновляй после каждой фазы: отмечай [x], обновляй метрики.

---

## БЫСТРЫЕ КОМАНДЫ

python -m pytest tests/ -v
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v
python -m pytest --cov=src --cov-report=term-missing
python -m pytest --cov=src --cov-report=html:reports/htmlcov
git add . && git commit -m "feat: ..." && git push