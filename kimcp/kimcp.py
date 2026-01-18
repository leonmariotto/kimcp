"""
KiMCP server
"""

import click
import logging
import asyncio
from typing import List, Tuple
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from mcp.server.fastmcp import Context, FastMCP
from mcp.server.session import ServerSession

import kipy
from .KiBoardWorker import KiBoardWorker

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)


@dataclass
class AppContext:
    """Application context with typed dependencies."""

    kiworker: KiBoardWorker
    lock: asyncio.Lock  # serialize access to KiCad


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    # KiCad Python bindings connect synchronously on construction.
    kiworker = await asyncio.to_thread(
        KiBoardWorker,
    )
    if kiworker is None:
        raise RuntimeError("Failed to connect to KiCad")

    try:
        _ = await asyncio.wait_for(
            asyncio.to_thread(kiworker.check_version),
            timeout=3.0,
        )
    except asyncio.TimeoutError as e:
        raise RuntimeError(
            "Timed out waiting for KiCad IPC response. Is KiCad running ?"
        ) from e
    except kipy.errors.FutureVersionError:
        logging.warning("KiCad instance and KiCad API version mismatch")
    except kipy.errors.ConnectionError as e:
        raise RuntimeError("Failed to connect to KiCad ! Is kicad running ?") from e
    # DO NOT check version as the project run with kicad 9.0.6 and KiPy IPC API is only compatible with 9.0.5 for now.
    # Just wait for it to be compatible with 9.0.6.

    logging.debug("Connected to kicad")

    try:
        yield AppContext(kiworker=kiworker, lock=asyncio.Lock())
    finally:
        # KiCad does not provide an explicit disconnect API.
        logging.debug("KiCad disconnect ...")
        pass


mcp = FastMCP("KiMCP", lifespan=lifespan)


@mcp.tool()
def get_version(ctx: Context[ServerSession, AppContext]) -> str:
    """
    Get version of the running kicad instance.
    """
    kiworker = ctx.request_context.lifespan_context.kiworker
    return kiworker.kicad.get_version().full_version


@mcp.tool()
def search_footprints_by_ref(
    ctx: Context[ServerSession, AppContext], ref_regex: str
) -> str:
    """
    Get a footprint list matching regex "ref_regex" in their references name.
    """
    kiworker = ctx.request_context.lifespan_context.kiworker
    return kiworker.search_footprints_by_ref(ref_regex)


@mcp.tool()
def get_board_outline(ctx: Context[ServerSession, AppContext]) -> str:
    """
    Get a list of board outlines. This can be used to delimit shape of the board.
    """
    kiworker = ctx.request_context.lifespan_context.kiworker
    return kiworker.get_board_outline()


@mcp.tool()
def move_rotate_footprint(
    ctx: Context[ServerSession, AppContext],
    ref: str,
    x_mm: float,
    y_mm: float,
    rotation: float,
) -> str:
    """
    Used to move a footprint on the board. Footprint is identified by its schematics reference.
    x_mm and y_mmc are given in milimeters. Rotation angle is in degree.
    """
    logging.debug(
        "ref:%s x_mm:%s y_mm:%s rotation:%s", ref, str(x_mm), str(y_mm), str(rotation)
    )
    kiworker = ctx.request_context.lifespan_context.kiworker
    kiworker.move_rotate_footprint(ref, x_mm, y_mm, rotation)
    return '{"status": "ok"}'


@mcp.tool()
def batch_place(
    ctx: Context[ServerSession, AppContext], batch: List[Tuple[str, float, float, int]]
) -> str:
    """
    Used to move a batch of components. Work the same way as move_rotate_footprint tool, but with a list of tuple
    containing (ref, x_mm, y_mm, rotation).
    """
    kiworker = ctx.request_context.lifespan_context.kiworker
    kiworker.batch_place(batch)
    return '{"status": "ok"}'


@click.command()
@click.option(
    "--debug",
    "-d",
    is_flag=True,
    default=False,
    show_default=True,
    help="Enable debug output.",
)
def run_server(debug: int):
    # Pass lifespan to server
    mcp.run(transport="streamable-http")
    # mcp.run(transport="http", host="127.0.0.1", port=8000, path="/mcp")
