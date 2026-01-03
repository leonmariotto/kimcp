import logging
import click
import kipy

from kipy.board_types import BoardLayer, Zone
from kipy.common_types import PolygonWithHoles
from kipy.geometry import PolyLine, PolyLineNode
from kipy.util import from_mm
from kipy.proto.common.types import KiCadObjectType
from kipy.proto.common.types import DocumentType

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)


class KiPyWrap:
    """
    """
    def __init__(self):
        self.kicad = kipy.KiCad()
        self.board = self.kicad.get_board()

    def get_board_info(self):
        """
        The main API here is get_items, it take a list of id in parameters to filter which item
        it return.
        Here's the list of types :
            - KiCadObjectType.KOT_UNKNOWN
		    - KiCadObjectType.KOT_PCB_FOOTPRINT
		    - KiCadObjectType.KOT_PCB_PAD
		    - KiCadObjectType.KOT_PCB_SHAPE
		    - KiCadObjectType.KOT_PCB_REFERENCE_IMAGE
		    - KiCadObjectType.KOT_PCB_FIELD
		    - KiCadObjectType.KOT_PCB_GENERATOR
		    - KiCadObjectType.KOT_PCB_TEXT
		    - KiCadObjectType.KOT_PCB_TEXTBOX
		    - KiCadObjectType.KOT_PCB_TABLE
		    - KiCadObjectType.KOT_PCB_TABLECELL
		    - KiCadObjectType.KOT_PCB_TRACE
		    - KiCadObjectType.KOT_PCB_VIA
		    - KiCadObjectType.KOT_PCB_ARC
		    - KiCadObjectType.KOT_PCB_MARKER
		    - KiCadObjectType.KOT_PCB_DIMENSION
		    - KiCadObjectType.KOT_PCB_ZONE
		    - KiCadObjectType.KOT_PCB_GROUP
        Obtain the full list by running :
        print([name for name in KiCadObjectType.keys()])
        """
        board = self.kicad.get_board()
        logging.debug("Board={%s}", str(board))
        logging.debug("Copper layers={%s}", str(board.get_copper_layer_count()))
        logging.debug("Footprint list={%s}", str(board.get_footprints()))
        logging.debug("Trace list={%s}", str(board.get_items(types=[KiCadObjectType.KOT_PCB_TRACE])))
        #logging.debug("Items list={%s}", str(board.get_items()))
        # logging.debug("Dimensions={%s}", str(board.get_dimensions()))
        # kipy.errors.ApiError: KiCad returned error: none of the requested types are valid for a Board object

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
    kiwrap.get_board_info()
