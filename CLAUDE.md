# Confessio - Claude Code Guide

## Commands

### Run server
```bash
python manage.py runserver
```

### Run background tasks worker
```bash
python manage.py process_tasks --sleep 1
```

### Lint
```bash
flake8 .
```

### Test
```bash
python -m unittest discover -s scheduling/tests -s crawling/tests
```

### Translations (front app only)
```bash
# Extract strings
python manage.py makemessages -l fr
# Compile
python manage.py compilemessages
```

## Architecture

Modular Django monorepo with 7 apps. Each app has its own models, views, services, and management commands.

### Apps

| App | Role |
|-----|------|
| `core` | Base models, settings, utilities, OTEL middleware |
| `registry` | Ecclesial entities: Diocese, Parish, Church, Website |
| `crawling` | Web crawling: Scraping, Crawling logs, moderation |
| `fetching` | External data sources (OClocher API integration) |
| `scheduling` | Confession schedule pipeline: pruning, parsing, matching, indexing |
| `attaching` | Image uploads and LLM-based image parsing |
| `front` | Public-facing views + django-ninja REST API |


### Key models

- `registry.Diocese` - Catholic diocese
- `registry.Parish` - Parish (belongs to Diocese, optionally has Website)
- `registry.Church` - Physical church with PostGIS PointField location (SRID 4326)
- `registry.Website` - Parish website to crawl
- `crawling.Scraping` - Crawled page (URL + website)
- `crawling.Crawling` - Crawl session metadata
- `scheduling.Scheduling` - Full pipeline state for a website (built -> pruned -> parsed -> matched -> indexed)
- `scheduling.Pruning` - Pruned HTML snippet containing schedule data
- `attaching.Image` - Uploaded image with LLM-extracted HTML

### Scheduling pipeline

`Scheduling.Status` progression:
1. `built` - resources collected (scrapings, images, OClocher data)
2. `pruned` - HTML pruned to confession-relevant snippets
3. `parsed` - LLM parses time/day schedules from snippets
4. `matched` - schedules matched to churches
5. `indexed` - final schedules indexed for search

### REST API

django-ninja API defined in `front/api.py`, mounted in `front/urls.py`. Namespace: `main_api`.

## Tech stack

- **Django 5.2** with Python 3.13
- **PostgreSQL** with **PostGIS** (spatial queries) and **pgvector** (embeddings)
- **django-ninja** for REST API (Pydantic schemas)
- **django-simple-history** for model versioning (all key models have `HistoricalRecords`)
- **django-background-tasks** for async workers
- **fructose** / **openai** for LLM calls
- **sentence-transformers** + **keras** for ML models (pruning, action classification)
- **uv** for dependency management (`pyproject.toml`)

## Code style

- Max line length: 100 characters (enforced by flake8)

## Project structure conventions

- Models use `TimeStampMixin` (from `core.models.base_models`) for `created_at`/`updated_at`
- Moderation models inherit `ModerationMixin` (from `registry.models`)
- Business logic lives in `*/services/` subdirectories
- Pipeline workflows live in `*/workflows/` subdirectories
- Management commands in `*/management/commands/` — one-shot migrations prefixed with `one_shot__`
- Tests in `*/tests/` — run with standard `manage.py test`
- Translation strings only in `front` app (`front/locale/fr/`)
