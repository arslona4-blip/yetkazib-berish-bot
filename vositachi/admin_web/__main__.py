"""Ishga tushirish: python -m vositachi.admin_web"""

from __future__ import annotations

import os

import uvicorn


def main() -> None:
    host = os.getenv("VOSITACHI_ADMIN_HOST", "0.0.0.0")
    port = int(os.getenv("PORT") or os.getenv("VOSITACHI_ADMIN_PORT") or "8080")
    uvicorn.run(
        "vositachi.admin_web.app:app",
        host=host,
        port=port,
        reload=False,
    )


if __name__ == "__main__":
    main()
