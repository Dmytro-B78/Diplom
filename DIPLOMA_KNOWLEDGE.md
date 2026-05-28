# DIPLOMA_KNOWLEDGE.md
# NT-Tech Trading Bot — Дипломный проект
# Автоматизация тестирования Python-приложений
# Последнее обновление: 2026-05-28

---

## СТАТУС ПРОЕКТА

**Фаза:** 2 — GitHub CI запущен, реальный код подключён
**Тесты:** 93/93 passed (локально Windows + Linux CI)
**Coverage:** 93% (src/stubs)
**Следующий шаг:** Фаза 3 — расширение покрытия, coverage badge, параметризация

---

## ОКРУЖЕНИЕ

| Параметр | Значение |
|----------|----------|
| OS | Windows, Python 3.13.1 |
| Дипломный проект | `C:\TradingBots\Diplom\` |
| Бот (локально) | `C:\TradingBots\NT\` |
| Бот (production) | VPS Contabo `/home/ubuntu/NT/` |
| Сервис | `systemd nttech.service` |
| Репозиторий бота | https://github.com/Dmytro-B78/NT (private) |
| Репозиторий диплома | https://github.com/Dmytro-B78/Diplom (public) |
| Python (тесты) | pytest 8.3.5, pytest-mock 3.14.0, pytest-cov 6.1.0 |

---

## ОБЪЕКТ ИССЛЕДОВАНИЯ: LiveEngine 5.8

### Компоненты бота и покрытие тестами

| Файл | Назначение | NT/tests (130) | Diplom/tests |
|------|-----------|----------------|--------------|
| `live_engine.py` | Основной движок, управление позициями | Нет | Нет |
| `risk_guard.py` | Риск-менеджмент, kill-switch | 23 теста | 25 тестов (реальный интерфейс) |
| `live_loop.py` | Event loop, WebSocket candles | Нет | Нет |
| `stage1.py` | Entry gate (4H alignment) | **Нет** | **23 теста (новое!)** |
| `entry_engine.py` | Логика входа | **Нет** | **15 тестов (новое!)** |
| `intrabar_stops.py` | Stop-loss логика | 21 тест | 10 тестов (реальный интерфейс) |
| `exit_intelligence.py` | Интеллектуальный выход | **НОЛЬ** | **17 тестов (ключевой вклад!)** |
| `trail_engine.py` | Trailing stop | 27 тестов | Нет (покрыто в NT) |
| `scripts/run_bt.py` | Backtest | Нет | Нет |

### Существующее тестирование в NT (130 тестов)

| Файл тестов | Тестов | Покрывает |
|-------------|--------|-----------|
| `test_indicators.py` | 24 | EMA, ATR, momentum, slope, HWM |
| `test_intrabar_stops.py` | 21 | abs_stop, hwm_stop, atr_trail, ema_stop |
| `test_meta_strategy.py` | 14 | smoke-тесты движка |
| `test_offline_runner.py` | 21 | CSV, stop triggers, trade records |
| `test_risk_guard.py` | 23 | kill-switch, positions, sizing |
| `test_trail_engine.py` | 27 | RR, фазы 1-3, trail state |

### Пробелы в NT/tests (вклад диплома)

- `exit_intelligence.py` — **НОЛЬ тестов**, баг pnl_pct v5.7 найден в live
- `stage1.py` — **НОЛЬ тестов**, 6 порогов фильтрации входов
- `entry_engine.py` — **НОЛЬ тестов**, BUG-3 cooldown, re-entry логика

---

## РЕАЛЬНЫЕ БАГИ (ключевые кейсы диплома)

### Баг 1: min_stop_pct floor — TRXUSDT
- **Компонент:** `risk_guard.py` — `compute_position_size()`
- **Суть:** при низком ATR символа (TRXUSDT) расстояние до стопа было ~0.0003,
  позиция становилась огромной (без floor в `min_distance = price * min_stop_pct`)
- **Обнаружен:** в live-торговле, не в тестах
- **Исправление:** `min_distance = price * self.min_stop_pct` (2%)
- **Тест:** `tests/unit/test_risk_guard.py::TestPositionSizing::test_min_stop_pct_floor_prevents_oversizing`

### Баг 2: pnl_pct — trigger вместо fill price (v5.7)
- **Компонент:** `exit_intelligence.py` — `_build_exit()`
- **Суть:** `exit_price` брался из `trigger_price`, а не `meta_state["close"]` (реальный fill)
- **Обнаружен:** в live-торговле, не в тестах
- **Исправление:** `"exit_price": float(meta_state["close"])`
- **Тест:** `tests/unit/test_exit_intelligence.py::TestExitPriceFix::test_exit_price_is_close_not_trigger`

### Баг 3: ABS_STOP cooldown — BUG-3
- **Компонент:** `entry_engine.py` — `compute_entry_signal()`
- **Суть:** после ABS_STOP бот сразу открывал новую позицию против движения
- **Исправление:** 8-барный cooldown после ABS_STOP
- **Тест:** `tests/unit/test_entry_engine.py::TestAbsStopCooldown`

---

## СТРУКТУРА ДИПЛОМНОГО ПРОЕКТА

```
C:\TradingBots\Diplom\
├── conftest.py
├── pytest.ini
├── requirements.txt
├── README.md
├── DIPLOMA_KNOWLEDGE.md
│
├── src/stubs/
│   ├── risk_guard_stub.py          ← RiskGuard 4.1 (класс, реальный интерфейс)
│   ├── intrabar_stops_stub.py      ← abs/hwm/atr/ema stops (реальный интерфейс)
│   ├── exit_intelligence_stub.py   ← evaluate_exits + state (реальный интерфейс)
│   ├── stage1_stub.py              ← stage1_check (pure fn, реальный интерфейс)
│   └── entry_engine_stub.py        ← compute_entry_signal (реальный интерфейс)
│
├── tests/
│   ├── unit/
│   │   ├── test_risk_guard.py          ← 25 тестов
│   │   ├── test_intrabar_stops.py      ← 10 тестов
│   │   ├── test_exit_intelligence.py   ← 17 тестов (ключевой!)
│   │   ├── test_stage1.py              ← 23 теста
│   │   └── test_entry_engine.py        ← 15 тестов
│   ├── integration/
│   │   └── test_mock_binance_api.py    ← 3 теста
│   └── mocks/
│
├── docs/
├── reports/
└── .github/workflows/tests.yml         ← CI/CD GitHub Actions ✅
```

---

## ПЛАН РАБОТЫ ПО ФАЗАМ

### ФАЗА 1 — Фундамент ✅ ЗАВЕРШЕНА (2026-05-28)
- [x] Структура проекта создана
- [x] conftest.py с фикстурами
- [x] pytest.ini, requirements.txt
- [x] Stubs для 5 компонентов бота
- [x] 90 unit-тестов (risk_guard, intrabar_stops, exit_intelligence, stage1, entry_engine)
- [x] 3 integration-теста с mock Binance API
- [x] CI/CD pipeline (GitHub Actions)
- [x] 93/93 тестов прошло локально
- [x] Coverage 93%
- [x] Анализ пробелов: exit_intelligence / stage1 / entry_engine не покрыты в NT/tests

---

### ФАЗА 2 — GitHub CI + реальный код ✅ ЗАВЕРШЕНА (2026-05-28)
- [x] Создать репозиторий Diplom на GitHub
- [x] Сделать первый push и проверить GitHub Actions
- [x] CI/CD: Status Success, 22s, ubuntu-latest
- [x] Изучить реальные файлы NT (risk_guard, intrabar_stops, exit_intelligence, stage1, entry_engine)
- [x] Адаптировать stubs и тесты под реальные интерфейсы
- [x] 93/93 тестов прошло на GitHub Actions

---

### ФАЗА 3 — Расширение покрытия
- [x] Coverage badge в README
- [ ] Параметризованные тесты (pytest.mark.parametrize) для stage1
- [ ] Mock WebSocket для live_loop.py
- [ ] Граничный случай: network timeout
- [ ] HTML coverage отчёт в reports/
- [ ] Добавить `C:\TradingBots\NT\` в sys.path для прямого импорта

---

### ФАЗА 4 — Написание диплома
**Глава 1 — Теоретические основы**
- Виды тестирования, pytest, CI/CD, особенности финансовых систем

**Глава 2 — Объект исследования**
- Архитектура NT-Tech Bot (8 компонентов)
- Анализ 130 существующих тестов: что покрыто, что нет
- Кейс 1: баг min_stop_pct (TRXUSDT) — не покрыт тестами
- Кейс 2: баг pnl_pct v5.7 — exit_intelligence без тестов
- Кейс 3: BUG-3 cooldown — entry_engine без тестов

**Глава 3 — Практическая часть**
- Инфраструктура: stubs, fixtures, pytest.ini, CI/CD
- Тесты exit_intelligence (главный вклад — было 0)
- Тесты stage1 (чистая функция, 6 порогов)
- Тесты entry_engine (cooldown, re-entry, breakout path)
- Mock Binance API
- Coverage до/после

**Глава 4 — Результаты**
- Метрики, какие баги поймали бы раньше, рекомендации

---

## ТЕКУЩИЕ МЕТРИКИ

| Метрика | Значение |
|---------|----------|
| Всего тестов (Diplom) | 93 |
| Unit-тестов | 90 |
| Integration-тестов | 3 |
| Passed | 93/93 (100%) |
| Coverage (stubs) | 93% |
| Время выполнения | ~0.07s (local) / 22s (CI) |
| | CI/CD | GitHub Actions ✅ passing + Codecov 84% |
| Репозиторий | https://github.com/Dmytro-B78/Diplom |
| Тестов в NT/tests | 130 |
| Компонентов без тестов в NT | 3 (exit_intelligence, stage1, entry_engine) |
| Реальных файлов NT подключено | 5 |

---

## КАК ИСПОЛЬЗОВАТЬ ЭТОТ ФАЙЛ

При начале новой сессии с Claude — вставь содержимое этого файла в чат.
Обновляй после каждой фазы: отмечай [x], обновляй метрики.

---

## БЫСТРЫЕ КОМАНДЫ

```bash
# Из C:\TradingBots\Diplom\

python -m pytest tests/ -v
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v
python -m pytest --cov=src --cov-report=term-missing
python -m pytest --cov=src --cov-report=html:reports/htmlcov

# Один тест
python -m pytest tests/unit/test_exit_intelligence.py::TestExitPriceFix::test_exit_price_is_close_not_trigger -v

# Git
git add . && git commit -m "feat: ..." && git push
```