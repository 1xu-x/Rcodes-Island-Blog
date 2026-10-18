"""Vercel serverless entrypoint.

Re-exports the existing FastAPI app unchanged. The app's `normalize_api_prefix`
middleware already strips the `/api` prefix that Vercel forwards to this
function, so the frontend's `/api/*` calls keep working on the same origin.
"""

from backend.app.main import app

__all__ = ["app"]
