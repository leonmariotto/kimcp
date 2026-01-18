"""
Tis file implement extracting data out of protobuf structure.
It should export functions that takes a Footprint structure and output a
dictionnary with correct values extracted.
Protobuf structure bloat model, we need to filter out many things.
A _short and a _detailed version of extractions may exist.
"""

import hashlib
import json
import kipy
from google.protobuf.json_format import MessageToDict  # KiCad IPC is based on protobuf

PAD_TYPE = "type.googleapis.com/kiapi.board.types.Pad"


def nm_to_mm(v):
    # your JSON shows x_nm/y_nm as strings
    return round(int(v) / 1_000_000.0, 4)


def stable_hash_bytes(b: bytes, n=12):
    return hashlib.sha1(b).hexdigest()[:n]


def stable_hash_str(s: str, n=12):
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:n]


def proto_extract_footprint_short(fp: kipy.board_types.Footprint) -> dict:
    """
    Short version of protobuf extraction for Footprints.
    """
    # fp_proto: the protobuf object (for cheap bytes hash)
    # fp_json: proto->dict output (your current JSON)

    fp_proto = getattr(fp, "proto", None)
    if fp_proto is None:
        raise TypeError(
            "This FootprintInstance does not expose .proto in this KiPy build."
        )

    fp_json = MessageToDict(
        fp_proto,
        preserving_proto_field_name=True,
        # Often helpful so enums show as ints (stable for downstream code):
        use_integers_for_enums=True,
        # Keep default fields if you want a consistent schema:
        always_print_fields_with_no_presence=True,
    )
    fid = fp_json["id"]["value"]

    # placement
    x = nm_to_mm(fp_json["position"]["x_nm"])
    y = nm_to_mm(fp_json["position"]["y_nm"])
    rot = float(fp_json.get("orientation", {}).get("value_degrees", 0.0))

    # identity
    defid = fp_json["definition"]["id"]
    fpname = f"{defid['library_nickname']}:{defid['entry_name']}"

    ref = (
        fp_json.get("reference_field", {})
        .get("text", {})
        .get("text", {})
        .get("text", "")
    )
    val = fp_json.get("value_field", {}).get("text", {}).get("text", {}).get("text", "")

    # flags
    attr = fp_json.get("attributes", {})
    flags = {
        "dnp": bool(attr.get("do_not_populate", False)),
        "npos": bool(attr.get("exclude_from_position_files", False)),
        "nbom": bool(attr.get("exclude_from_bill_of_materials", False)),
        "nis": bool(attr.get("not_in_schematic", False)),
    }

    # summarize pads
    nets_set = set()
    pad_count = 0
    for it in fp_json["definition"].get("items", []):
        if it.get("@type") == PAD_TYPE:
            pad_count += 1
            net = it.get("net", {}).get("name")
            if net:
                nets_set.add(net)

    nets_sorted = sorted(nets_set)
    nets_capped = nets_sorted[:4]
    nsig = stable_hash_str("\n".join(nets_sorted))  # stable even if capped

    # change tracking: hash full proto bytes (best), else canonical JSON
    try:
        h = stable_hash_bytes(fp_proto.SerializeToString(deterministic=True))
    except Exception:
        h = stable_hash_str(json.dumps(fp_json, sort_keys=True, separators=(",", ":")))

    rec = {
        "id": fid,
        "fp": fpname,
        "ref": ref,
        "val": val,
        "at": [x, y, rot],
        "ly": int(fp_json.get("layer", 0)),
        "lock": bool(fp_json.get("locked", 0)),
        "pc": pad_count,
        "nets": nets_capped,
        "nsig": nsig,
        "h": h,
        **flags,
    }
    return rec


def proto_extract_footprint_long(fp: kipy.board_types.Footprint) -> dict:
    """
    Long version of protobuf extraction.
    Return all for now.
    """
    # fp_proto: the protobuf object (for cheap bytes hash)
    # fp_json: proto->dict output (your current JSON)

    fp_proto = getattr(fp, "proto", None)
    if fp_proto is None:
        raise TypeError(
            "This FootprintInstance does not expose .proto in this KiPy build."
        )

    fp_json = MessageToDict(
        fp_proto,
        preserving_proto_field_name=True,
        # Often helpful so enums show as ints (stable for downstream code):
        use_integers_for_enums=True,
        # Keep default fields if you want a consistent schema:
        always_print_fields_with_no_presence=True,
    )
    return fp_json
