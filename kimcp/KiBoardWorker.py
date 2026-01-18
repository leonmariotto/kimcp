import logging
import click
import kipy
import json

from typing import Optional, List, Tuple

from kipy.geometry import Vector2, Angle
from kipy.proto.common.types import KiCadObjectType
from kipy.util.board_layer import layer_from_canonical_name
from google.protobuf.json_format import MessageToDict  # KiCad IPC is based on protobuf

from .protobuf_extract import (
    proto_extract_footprint_short,
    proto_extract_footprint_long,
)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)


class KiWorkerError(Exception):
    pass


class KiBoardWorker:
    """
    Should implement the core functions for the following tools :
    pcb_load(board_path)
      - Args: board_path: string (path to .kicad_pcb)
      - Output: success boolean
      - Purpose: open the board to work on.
      - __init__ of KiBoardWorker.
    pcb_list_footprints()
      - Output: list of footprints with refs, current pos/rot,
            footprint name, and assigned nets per pad
      - Purpose: inventory what needs placement.
    pcb_get_nets()
      - Output: list of nets with connected pads/footprints
      - Purpose: understand connectivity to minimize crossings.
    pcb_move_rotate_footprint(ref, x, y, rotation)
      - Args: ref: string, x/y: float (mm), rotation: float (deg)
      - Output: success boolean (or updated footprint info)
      - Purpose: place a specific footprint precisely.
    pcb_batch_place(placements)
      - Args: placements: array of {ref, x, y, rotation}
      - Output: per-ref success/errors
      - Purpose: apply multiple placements efficiently.
    pcb_get_board_outline()
      - Output: polygon/segments of edge cuts
      - Purpose: keep placements inside the outline.
    pcb_save()
      - Output: success boolean
      - Purpose: persist changes.
    """

    def __init__(self):
        self.kicad = kipy.KiCad()
        self.logger = logging.getLogger(__name__)
        self.board = self.kicad.get_board()

    def get_footprints(self, detailed: bool = False, indent=2) -> str:
        """ """
        footprints = self.board.get_footprints()
        dicts = []
        for fp in footprints:
            if not detailed:
                dicts += [proto_extract_footprint_short(fp)]
            else:
                dicts += [proto_extract_footprint_long(fp)]
        out = json.dumps(dicts, indent=indent)
        self.logger.debug("Got %d footprints js_repr=[%s]", len(footprints), out)
        return out

    def _get_footprint_by_ref(self, ref: str) -> Optional[kipy.board_types.Footprint]:
        """
        Return footprint if reference found in board's footprint list.
        Otherwise return None.
        """
        for fp in self.board.get_footprints():
            fp_ref = (
                fp.reference_field.text.value
            )  # reference is stored in the reference field text
            if fp_ref == ref:
                self.logger.debug("Found footprints ref %s", ref)
                return fp
        raise KiWorkerError("Footprint ref %s not found" % ref)

    def move_rotate_footprint(
        self, ref: str, x_mm: float, y_mm: float, rotation_angle: float
    ):
        """
        Move + rotate a footprint identified by its reference designator.

        Coordinates here are interpreted as millimeters (x_mm, y_mm).
        """

        # Find the footprint instance by its reference field text (e.g., "R12", "U3")
        target = self._get_footprint_by_ref(ref)
        if target is None:
            raise KeyError(f'No footprint with reference "{ref}" found on this board')

        self.logger.debug(
            "Move footprints ref %s to %f - %f (rot=%f)",
            ref,
            x_mm,
            y_mm,
            rotation_angle,
        )
        # If the footprint is locked, you typically need to unlock it before moving.
        # (If your workflow relies on locking, you can remove this and handle failure instead.)
        if getattr(target, "locked", False):
            target.locked = False

        # Set absolute position + absolute orientation
        target.position = Vector2.from_xy_mm(x_mm, y_mm)
        target.orientation = Angle.from_degrees(rotation_angle)

        # Apply to the open board (use a commit so it's one undo step in the GUI)
        commit = self.board.begin_commit()
        try:
            self.board.update_items(target)
            self.board.push_commit(commit, message=f"Move+rotate {ref}")
            return
        except Exception as e:
            self.board.drop_commit(commit)
            raise KiWorkerError("Failed to commit the move.") from e

    def batch_place(self, batch: List[Tuple[str, float, float, int]]):
        for ref, x, y, rot in batch:
            self.move_rotate_footprint(ref, x, y, rot)

    @staticmethod
    def boardshapes_to_json(
        shapes, *, preserving_proto_field_name=True, indent=2
    ) -> str:
        """
        Convert a list[BoardShape] to a JSON string by serializing each shape's .proto.
        """
        dicts = []
        for s in shapes:
            # Most KiPy wrappers expose the underlying protobuf as .proto
            msg = getattr(s, "proto", None) or s
            dicts.append(
                MessageToDict(
                    msg,
                    preserving_proto_field_name=preserving_proto_field_name,
                    # Often helpful so enums show as ints (stable for downstream code):
                    use_integers_for_enums=True,
                    # Keep default fields if you want a consistent schema:
                    always_print_fields_with_no_presence=True,
                )
            )
        return json.dumps(dicts, indent=indent)

    def get_board_outline(self) -> str:
        """
        Returns a list of KiPy board shape objects that are on Edge.Cuts.
        Each element is usually a concrete type (BoardSegment, BoardArc, ...),
        otherwise the original BoardShape.
        """
        edge_cuts = layer_from_canonical_name("Edge.Cuts")

        edge_cuts_shapes = [s for s in self.board.get_shapes() if s.layer == edge_cuts]
        out = KiBoardWorker.boardshapes_to_json(edge_cuts_shapes)
        self.logger.debug("Board edges cuts json = %s", out)
        return out

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
        logging.debug(
            "Trace list={%s}",
            str(board.get_items(types=[KiCadObjectType.KOT_PCB_TRACE])),
        )
        # logging.debug("Items list={%s}", str(board.get_items()))
        # logging.debug("Dimensions={%s}", str(board.get_dimensions()))
        # kipy.errors.ApiError: KiCad returned error: none of the requested types are valid for a Board object

    def check_version(self):
        return self.kicad.check_version()


@click.command()
def test_kicad():
    # Pass lifespan to server
    kiwork = KiBoardWorker()
    logging.debug("KiBoardWorker init !")
    kiwork.get_footprints()
    # kiwork.get_board_outline()
    # kiwork.move_rotate_footprint("U1", 145.75, 88.25, 270)
