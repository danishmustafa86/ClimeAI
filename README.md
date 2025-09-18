---
title: ClimeAI
emoji: 🎭
colorFrom: indigo
colorTo: pink
sdk: docker
pinned: false
license: mit
short_description: testing
python_version: 3.13
---

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference

# ClimeAI

## Getting Started

1. Install dependencies

```bash
uv sync
```

2. Set environment variables

```bash
cp .env .env.example
# Edit .env with your keys (e.g., OPENWEATHERMAP_API_KEY, OPENCAGE_API_KEY, DB connection)
```

3. Run the API server (FastAPI with Uvicorn)

```bash
uv run uvicorn main:app --reload
```

Server will start on http://127.0.0.1:8000

Open docs at:
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc
