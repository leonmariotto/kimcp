import logging
import click
import kipy

from kipy.board_types import BoardLayer, Zone
from kipy.common_types import PolygonWithHoles
from kipy.geometry import PolyLine, PolyLineNode
from kipy.util import from_mm

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)


class KiPyWrap:
    def __init__(self):
        self.kicad = kipy.KiCad()

    def draw_zone(self):
        board = self.kicad.get_board()
        outline = PolyLine()
        outline.append(PolyLineNode.from_xy(from_mm(100), from_mm(100)))
        outline.append(PolyLineNode.from_xy(from_mm(110), from_mm(100)))
        outline.append(PolyLineNode.from_xy(from_mm(110), from_mm(110)))
        outline.append(PolyLineNode.from_xy(from_mm(100), from_mm(110)))
        outline.append(PolyLineNode.from_xy(from_mm(100), from_mm(100)))
        polygon = PolygonWithHoles()
        polygon.outline = outline
        zone = Zone()
        zone.layers = [BoardLayer.BL_F_Cu, BoardLayer.BL_B_Cu]
        zone.outline = polygon
        board.create_items(zone)

    def check_version(self):
        ok = self.kicad.check_version()
        if not ok:
            raise ValueError()


@click.command()
def test_kicad():
    # Pass lifespan to server
    kiwrap = KiPyWrap()
    kiwrap.check_version()
