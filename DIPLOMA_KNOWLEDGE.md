# DIPLOMA_KNOWLEDGE.md
# NT-Tech Trading Bot — Дипломный проект
# Автоматизация тестирования Python-приложений
# Последнее обновление: 2026-07-28

---

## СТАТУС ПРОЕКТА

**Фаза:** 4 — Диплом завершён, готов к сдаче
**Тесты:** 209/209 passed (локально Windows + Linux CI)
**Coverage:** 85% (общий, `--cov=src`, локально и Codecov совпадают)
**Файл:** Диплом_NT-Tech_Бердников_v32.docx — финальная версия

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
| Jira | dberdnikoff.atlassian.net, проект SCRUM, cloudId 61adc359-9f56-4b21-9ef6-2d61cf2d477e |

---

## ТЕКУЩИЕ МЕТРИКИ

| Метрика | Значение |
|---------|----------|
| Всего тестов | 209 |
| Unit-тестов | 194 |
| Integration-тестов | 15 |
| Passed | 209/209 (100%) |
| Coverage (`--cov=src`, локально) | 85% |
| Coverage (Codecov CI) | 85% |
| Время выполнения | ~0.3s (local) / ~29s (CI) |
| CI/CD | GitHub Actions passing ✅ + Codecov 85% |

### Реальное покрытие по компонентам (`--cov=bot_ai`, замер от 2026-07-28)

Компоненты, тестируемые через **стабы** (`src/stubs/`), покрытие видно через `--cov=src`:

| Компонент | Тестов | Coverage |
|---|---|---|
| exit_intelligence | 17 | 95% |
| stage1 | 23 | 98% |
| entry_engine | 15 | 96% |
| intrabar_stops | 13 | 63% |
| live_loop | 8 | 90% |

Компоненты, тестируемые напрямую на **реальных файлах NT** (`bot_ai.*`), покрытие видно только через `--cov=bot_ai`, а не через `--cov=src`:

| Компонент | Тестов | Coverage |
|---|---|---|
| risk_guard | 30 | 85% |
| trail_engine | 30 | 89% |
| indicators | 28 | 96% |
| meta_strategy | 15 | 77% |
| offline_runner | 23 | 41%* |

\* offline_runner: 23 теста покрывают три конкретные функции (`load_csv`, `check_intrabar_stops`, `build_trade_record`). Backtest-луп (`scripts/run_bt.py` и связанная логика прогона бэктеста) вне scope этой работы — этим объясняется разница между покрытием протестированных функций и покрытием всего файла. Пояснение об этом добавлено в текст диплома (после таблицы 4.3).

**Важно для будущих замеров:** `--cov=src` НЕ видит реальные файлы `bot_ai.*` — только стабы. Чтобы получить полную картину покрытия по всем 10 компонентам, нужно запускать:
```
pytest --cov=src --cov=bot_ai --cov-report=term-missing
```

---

## ОБЪЕКТ ИССЛЕДОВАНИЯ: LiveEngine 5.8

### Компоненты бота

| Файл | Назначение | NT/tests (130) | Diplom/tests |
|------|-----------|----------------|--------------|
| live_engine.py | Основной движок | Нет | Нет (не тестируется, оркестратор) |
| risk_guard.py | Риск-менеджмент, kill-switch | 23 теста | 30 тестов ✅ |
| live_loop.py | Event loop, WebSocket candles | Нет | 8 тестов (mock WS) |
| stage1.py | Entry gate (4H alignment) | Нет | 23 теста (параметризованные) |
| entry_engine.py | Логика входа | Нет | 15 тестов (BUG-3 cooldown) |
| intrabar_stops.py | Stop-loss логика | 21 тест | 13 тестов |
| exit_intelligence.py | Интеллектуальный выход | Нет | 17 тестов (ключевой вклад!) |
| trail_engine.py | Trailing stop | 27 тестов | 30 тестов ✅ |
| indicators.py | EMA, ATR, update_indicators | Нет | 28 тестов ✅ |
| meta_strategy.py | Основная стратегия | 13 тестов | 15 тестов ✅ |
| offline_runner.py | CSV loader, intrabar, trade record | 27 тестов | 23 теста ✅ |
| scripts/run_bt.py | Backtest | Нет | Нет |

**До начала работы без единого теста в Diplom-репозитории:** exit_intelligence, stage1, entry_engine, live_loop (4 компонента). Частично покрытые: risk_guard, intrabar_stops.

---

## РЕАЛЬНЫЕ БАГИ (ключевые кейсы диплома)

### БАГ-1: min_stop_pct floor — TRXUSDT (SCRUM-8)
- Компонент: risk_guard.py — compute_position_size()
- Обнаружен: в live-торговле, не тестами
- Исправление: min_distance = price * self.min_stop_pct (2%)
- Jira: https://dberdnikoff.atlassian.net/browse/SCRUM-8

### БАГ-2: pnl_pct — trigger вместо fill price, v5.7 (SCRUM-9)
- Компонент: exit_intelligence.py — _build_exit()
- Обнаружен: в live-торговле v5.7
- Исправление: "exit_price": float(meta_state["close"])
- Видео: https://youtu.be/PfMt1gRJlds
- Jira: https://dberdnikoff.atlassian.net/browse/SCRUM-9

### БАГ-3: ABS_STOP cooldown (SCRUM-10)
- Компонент: entry_engine.py — compute_entry_signal()
- Исправление: 8-барный cooldown после ABS_STOP
- Видео: https://youtu.be/L5QuDJ6lW2w
- Jira: https://dberdnikoff.atlassian.net/browse/SCRUM-10

### БАГ-4: off-by-one в _compute_phase (SCRUM-6, учебный кейс)
- Компонент: trail_engine.py
- `>` вместо `>=` на границе PROFIT_LOCK_RR_T2
- Видео: https://youtu.be/Tfvcmhu8Rbc
- Jira: https://dberdnikoff.atlassian.net/browse/SCRUM-6

### БАГ-5: инверсия коэффициентов ATR-режимов (SCRUM-7, учебный кейс)
- Компонент: trail_engine.py — _compute_atr_mult()
- extreme/low коэффициенты перепутаны местами
- Видео: https://youtu.be/i7xuB9HW43M
- Jira: https://dberdnikoff.atlassian.net/browse/SCRUM-7

Все 5 багов задокументированы в тексте диплома (раздел 4.1) со ссылками на Jira-тикеты.

---

## СТРУКТУРА ДИПЛОМА (по шаблону QA) — ВСЁ ЗАВЕРШЕНО

1. Введение ✅ (исправлена фактическая неточность: 4 непокрытых компонента, не 3; уточнено, какие 3 бага реальные — risk_guard/exit_intelligence/entry_engine)
2. Специфика проекта ✅
3. Планирование тестирования ✅ (добавлена пропущенная строка stage1 в таблицу "Что тестируется")
4. Тестовая документация ✅ (5 баг-репортов со ссылками на Jira; актуальные coverage-цифры)
5. Автоматизация тестирования ✅
6. Проблемы и решения ✅
7. Итоги работы ✅ (coverage-таблица "До/После" с реальными цифрами)
8. Заключение ✅ (исправлена структура списка: "Что эта работа дала лично мне" была ошибочно частью предыдущего bullet-списка — теперь отдельный блок)
9. Приложения ✅ — А (структура репо), Б (ссылки), В (видео), Г (10 скриншотов) — все теперь единообразные заголовки Heading2

---

## ВЁРСТКА / ФОРМАТИРОВАНИЕ (v28→v32)

Проведён полный аудит пагинации документа (25 страниц):
- Заголовки разделов не остаются одинокими внизу страницы (проверено программно: позиция каждого из 21 заголовка относительно конца страницы)
- Таблицы не разрываются так, что шапка отделяется от данных (было 2 случая: 4.3 Чек-лист, таблица "Инструменты" в разделе 3 — исправлено через pageBreakBefore)
- Подписи скриншотов (`Скриншот N:`) получили `keepNext`, чтобы не отрываться от своей картинки — было 10 таких абзацев без этой защиты
- Приложения В и Г переведены из обычных bullet-пунктов в полноценные заголовки Heading2 (были неконсистентны с А и Б)
- Раздел "3. Планирование тестирования" перенесён на отдельную страницу целиком (вместо разрыва таблицы "Инструменты" пополам)

**Метод проверки:** рендер в PDF → `pdftotext -layout` → программный анализ позиции каждого заголовка и последней строки каждой страницы на предмет "сиротских" шапок таблиц. Работает надёжнее ручного пролистывания.

---

## СТРУКТУРА РЕПОЗИТОРИЯ

```
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
    unit/          (194 теста)
    integration/   (15 тестов)
    mocks/
  docs/
  reports/htmlcov/          (HTML coverage отчёт, в .gitignore)
  .github/workflows/tests.yml
```

---

## ЗАДЕЛ ДЛЯ СЛЕДУЮЩЕЙ ИТЕРАЦИИ (второй диплом по этому боту)

Если по NT-Tech LiveEngine будет писаться ещё одна дипломная/курсовая работа, вот честный список того, что осталось непокрытым или недоделанным:

1. **offline_runner backtest-луп** — `scripts/run_bt.py` и связанная логика прогона бэктеста (строки 118–253 в `bot_ai/engine/offline_runner.py`) не покрыты тестами вообще. Сейчас покрыты только 3 вспомогательные функции.
2. **live_engine.py** — оркестратор, 0% покрытия, сознательно вне scope (требует полного окружения со всеми зависимостями для мокирования).
3. **stage2.py** — 5% покрытия (126 стр., 120 непокрыто) — совсем не в фокусе текущей работы.
4. **meta_signal_filter.py, breakout_engine.py** — 47-50% покрытия, частично затронуты косвенно через meta_strategy, но не имеют собственных прицельных тестов.
5. **live_loop.py** — 90% через стаб, но реальный файл `bot_ai/engine/live_loop.py` (209 строк) при прямом замере `--cov=bot_ai` показывает 0% — тестируется только через изолированный стаб, не напрямую.
6. **Методологический момент:** при любом будущем замере покрытия — всегда проверять и `--cov=src` (стабы), и `--cov=bot_ai` (реальные файлы) раздельно, иначе часть компонентов покажет ложные 0% или вообще не попадёт в отчёт.

---

## КАК ИСПОЛЬЗОВАТЬ ЭТОТ ФАЙЛ

При начале новой сессии с Claude — вставь содержимое этого файла в чат.
Обновляй статус написанных разделов после каждой сессии.

---

## БЫСТРЫЕ КОМАНДЫ

```
python -m pytest tests/ -v
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v
pytest --cov=src --cov-report=term-missing
pytest --cov=src --cov=bot_ai --cov-report=term-missing
pytest --cov=src --cov-report=html:reports/htmlcov
start reports\htmlcov\index.html
git add . && git commit -m "feat: ..." && git push
```