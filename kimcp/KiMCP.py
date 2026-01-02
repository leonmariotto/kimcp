""" KiMCP server
"""

import click
import logging
import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from mcp.server.fastmcp import Context, FastMCP
from mcp.server.session import ServerSession

import kipy

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

@dataclass
class AppContext:
    """Application context with typed dependencies."""
    kicad: kipy.KiCad
    lock: asyncio.Lock  # serialize access to KiCad


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    # KiCad Python bindings connect synchronously on construction.
    kicad = await asyncio.to_thread(
        kipy.KiCad,
        timeout_ms=2000,
    )
    if kicad is None:
        raise RuntimeError("Failed to connect to KiCad")

    ## Optional sanity check (also sync -> run in thread)
    #ok = await asyncio.to_thread(kicad.check_version)
    #if not ok:
    #    # choose your policy: raise to fail startup, or log and continue
    #    logging.warning("KiCad instance and KiCad API version mismatch")
    # DO NOT check version as the project run with kicad 9.0.6 and KiPy IPC API is only compatible with 9.0.5 for now.
    # Just wait for it to be compatible with 9.0.6.

    logging.debug("Connected to kicad")

    try:
        yield AppContext(kicad=kicad, lock=asyncio.Lock())
    finally:
        # KiCad does not provide an explicit disconnect API.
        pass

mcp = FastMCP("KiMCP", lifespan=lifespan)

# Access type-safe lifespan context in tools
@mcp.tool()
def get_version(ctx: Context[ServerSession, AppContext]) -> str:
    """
    Get version of the running kicad instance.
    """
    kicad = ctx.request_context.lifespan_context.kicad
    return kicad.get_version().full_version

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
    mcp.run(transport="stdio")


