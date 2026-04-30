from __future__ import annotations

import asyncio

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .routers import account, admin, billing, market, pages
from .security import add_security_headers
from .services.accounts import init_account_db
from .services.quotes import _fmp_ws_tasks, fetch_quote_cards, start_fmp_quote_websockets


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

app.middleware("http")(add_security_headers)


@app.on_event("startup")
async def startup_event() -> None:
    init_account_db()
    await fetch_quote_cards()
    start_fmp_quote_websockets()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    for task in _fmp_ws_tasks:
        task.cancel()
    if _fmp_ws_tasks:
        await asyncio.gather(*_fmp_ws_tasks, return_exceptions=True)


app.include_router(account.router)
app.include_router(billing.router)
app.include_router(admin.router)
app.include_router(market.router)
app.include_router(pages.router)
