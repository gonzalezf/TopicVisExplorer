"""Programmatic launcher used by ``tve.show()`` / ``tve.demo()``.

Wraps uvicorn so callers don't have to know about the ASGI machinery.
The function blocks until the server is interrupted (Ctrl+C); use a
thread or ``asyncio.create_task`` for non-blocking variants.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..logging import configure_logging, get_logger

if TYPE_CHECKING:
    from fastapi import FastAPI

logger = get_logger(__name__)


def serve(
    app: FastAPI,
    *,
    host: str = "127.0.0.1",
    port: int = 8000,
    open_browser: bool = False,
    browser_path: str = "/singlecorpus",
    log_level: str = "info",
) -> None:
    """Run the given FastAPI app under uvicorn (blocking).

    Parameters
    ----------
    app:
        The :class:`fastapi.FastAPI` returned by
        :func:`topicvisexplorer.server.build_app`.
    host:
        Interface to bind. Defaults to localhost; pass ``"0.0.0.0"`` to
        allow LAN access.
    port:
        TCP port. If already in use, increments up to 50 times before
        raising.
    open_browser:
        If True, open the user's default browser to ``/singlecorpus``.
    log_level:
        Forwarded to uvicorn (``"debug"``, ``"info"``, ``"warning"``...).

    Notes
    -----
    Multi-worker deployment is intentionally not supported here; the
    in-memory :class:`SessionStore` would not be shared across workers.
    For production use put TVE behind a single-worker uvicorn process,
    or wait for v1.1 which adds Redis-backed sessions.
    """
    import socket
    import webbrowser

    import uvicorn

    chosen_port = port
    for _ in range(50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((host, chosen_port))
                break
            except OSError:
                chosen_port += 1
    else:
        raise OSError(f"Could not find a free port near {port} on {host} after 50 attempts.")

    # So ``logger.info`` from :mod:`topicvisexplorer` modules is visible in the
    # terminal (the library does not configure handlers by default).
    configure_logging()

    if open_browser:
        path = browser_path if browser_path.startswith("/") else f"/{browser_path}"
        url = f"http://{host}:{chosen_port}{path}"
        logger.info("Opening browser to %s", url)
        webbrowser.open(url)

    uvicorn.run(app, host=host, port=chosen_port, log_level=log_level)
