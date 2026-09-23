# Deployment

## Local / VS Code

```bash
bash run.sh
```

Open `http://127.0.0.1:5012`.

For a temporary public preview in VS Code: open **Ports**, forward `5012`, set Visibility to **Public**, and share the generated devtunnels link.

## Render

The repository contains `render.yaml` and a `Procfile`.

1. Push this folder to a GitHub repository.
2. In Render, create a Web Service from the repository (or use the Blueprint from `render.yaml`).
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 180`
5. Health check: `/api/health`

The bundled SQLite database is fine for review/demo. For a public multi-user launch, migrate to PostgreSQL because ephemeral hosting and concurrent writes are not appropriate for long-term SQLite persistence.
