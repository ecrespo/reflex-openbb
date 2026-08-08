# T-007 — Fix runtime data binding + carga inicial

> **Estado**: PENDIENTE
> **Creado**: 2026-08-08
> **Bloqueado por**: T-006 (data layer arreglado ✅, UI binding roto ❌)
> **Bloquea**: T-009 (CI), v0.2.0, PyPI publish, GitHub release

---

## Contexto

T-006 demostró que:
- El **data layer funciona** contra OpenBB v4 real (7 integration tests verde).
- El **UI no muestra datos** por 2 bugs de binding entre state y componentes.
- Las páginas cargan vacías (no hay `on_load` que cargue datos iniciales).

---

## Tareas

### T-007-1: Fix `news_feed` binding en equity page
- **Archivo**: `src/reflex_openbb/pages/equity.py` línea ~121
- **Bug**: pasa `EquityState.news` (list[NewsItem] Pydantic con HttpUrl/datetime)
- **Fix**: cambiar a `EquityState.news_display` (list[str] HTML pre-renderado)
- **Tiempo**: 5 min
- **Verificación**: `reflex run` → /equity → MSFT → news feed renderiza sin crash

### T-007-2: Fix `test_equity_state.py::test_set_ticker_rejects_invalid_ticker`
- **Archivo**: `tests/test_equity_state.py` línea ~336
- **Bug**: el test pasa `{"ticker": "AA!PL"}` y espera `InvalidTickerError`
  pero el mock del data layer no está configurado para levantarlo
- **Fix**: configurar `mock_data_layer["quote"].side_effect = InvalidTickerError(...)`
- **Tiempo**: 5 min
- **Verificación**: `uv run pytest tests/test_equity_state.py -q -W ignore`

### T-007-3: Agregar `on_load` handlers a las 3 páginas
- **Archivos**:
  - `src/reflex_openbb/state/equity_state.py` — `async def load_initial(self)`
  - `src/reflex_openbb/state/crypto_state.py` — `async def load_initial(self)`
  - `src/reflex_openbb/state/economy_state.py` — `async def load_initial(self)`
- **Bug**: las páginas cargan con `price_bars=[]`, `quote=None`, `series=[]`
  — no hay carga automática al montar la página
- **Fix**: cada state expone `load_initial()` que carga datos por defecto
  (MSFT para equity, BTC para crypto, GDP/US para economy)
- **Registración**: en `app.py`, pasar `on_load=State.load_initial` a `add_page()`
- **Tiempo**: 15 min
- **Verificación**: `reflex run` → abrir /equity → datos de MSFT cargan solos

### T-007-4: Verificar que el handler `set_ticker` completa sin crash en runtime
- **Archivo**: `src/reflex_openbb/state/equity_state.py`
- **Bug**: el handler llama 4 data functions secuenciales; si news_feed
  explota en el render, el backend crashea y el state nunca se actualiza
- **Fix**: después de T-007-1 (news_feed binding), verificar que el handler
  completa las 4 llamadas y el state se propaga al cliente
- **Verificación**: `reflex run` → /equity → MSFT → KPIs, chart, fundamentals,
  news se renderizan

### T-007-5: Verificar crypto page end-to-end
- **Archivo**: `src/reflex_openbb/pages/crypto.py`
- **Verificación**: `reflex run` → /crypto → BTC → chart con 366 bars
- **Tiempo**: 5 min

### T-007-6: Verificar economy page end-to-end
- **Archivo**: `src/reflex_openbb/pages/economy.py`
- **Verificación**: `reflex run` → /economy → GDP/US → chart con 43 points
- **Tiempo**: 5 min

### T-007-7: Commit + PR #7
- **Branch**: `fix/reflex-runtime-typing` → `develop`
- **Scope**: 31 archivos modificados (data layer OpenBB v4 fix + componentes
  dual-compatibility + state handlers form_data + tests integration)
- **Tiempo**: 10 min
- **Verificación**: CI verde (si T-009 está listo) o merge directo

---

## Tareas post-T-007 (no bloqueadas por T-007)

### T-008: Carga inicial con skeleton/loading state
- Mientras `on_load` carga datos, mostrar skeleton/spinner en vez de
  "No price data"
- **Tiempo**: 15 min

### T-009: GitHub Actions CI
- Workflow: ruff + pytest + build wheel
- **Tiempo**: 30 min

### T-010: v0.2.0
- Features: multi-ticker comparison, export CSV funcional, dark mode
- **Tiempo**: TBD

### T-011: PyPI publish
- `uv publish` + verificar `pip install reflex-openbb-ui`
- **Tiempo**: 10 min

### T-012: GitHub release
- Release notes v0.2.0 + tag
- **Tiempo**: 5 min

---

## Resumen de estado

| Tarea | Descripción | Estado | Tiempo |
|---|---|---|---|
| T-007-1 | Fix news_feed binding | ⏭ Pendiente | 5 min |
| T-007-2 | Fix test_set_ticker_rejects | ⏭ Pendiente | 5 min |
| T-007-3 | on_load handlers | ⏭ Pendiente | 15 min |
| T-007-4 | Verificar equity runtime | ⏭ Pendiente | 5 min |
| T-007-7 | Commit + PR #7 | ⏭ Pendiente | 10 min |
| T-008 | Skeleton loading | ⏭ Pendiente | 15 min |
| T-009 | CI GitHub Actions | ⏭ Pendiente | 30 min |
| T-010 | v0.2.0 features | ⏭ Pendiente | TBD |
| T-011 | PyPI publish | ⏭ Pendiente | 10 min |
| T-012 | GitHub release | ⏭ Pendiente | 5 min |
| **Total T-007** | | | **~45 min** |
