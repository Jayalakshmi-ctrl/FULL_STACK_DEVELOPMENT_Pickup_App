from __future__ import annotations

from typing import Iterable

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from .settings import settings

app = FastAPI(title="api-gateway", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _filter_headers(headers: Iterable[tuple[str, str]]) -> dict[str, str]:
    out: dict[str, str] = {}
    for k, v in headers:
        lk = k.lower()
        if lk in ("host", "content-length", "connection"):
            continue
        out[k] = v
    return out


async def _proxy(request: Request, upstream_base: str, prefix: str) -> Response:
    # e.g. /auth/login -> upstream_base + /auth/login
    upstream_url = f"{upstream_base}{request.url.path}"
    if request.url.query:
        upstream_url += f"?{request.url.query}"

    body = await request.body()
    headers = _filter_headers(request.headers.items())

    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.request(
            request.method,
            upstream_url,
            content=body if body else None,
            headers=headers,
        )

    resp_headers = _filter_headers(r.headers.items())
    return Response(content=r.content, status_code=r.status_code, headers=resp_headers, media_type=r.headers.get("content-type"))


@app.api_route("/auth/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def auth_proxy(request: Request, path: str):
    return await _proxy(request, settings.auth_service_base_url, "/auth")


@app.api_route("/pickups{rest:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def pickups_proxy(request: Request, rest: str):
    return await _proxy(request, settings.pickups_service_base_url, "/pickups")


@app.api_route("/rewards{rest:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def rewards_proxy(request: Request, rest: str):
    return await _proxy(request, settings.pickups_service_base_url, "/rewards")


@app.api_route("/eco{rest:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def eco_proxy(request: Request, rest: str):
    return await _proxy(request, settings.pickups_service_base_url, "/eco")


@app.api_route("/catalog{rest:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def catalog_proxy(request: Request, rest: str):
    return await _proxy(request, settings.pickups_service_base_url, "/catalog")


@app.api_route("/admin{rest:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def admin_proxy(request: Request, rest: str):
    return await _proxy(request, settings.pickups_service_base_url, "/admin")


@app.get("/health")
def health():
    return {"status": "ok"}

