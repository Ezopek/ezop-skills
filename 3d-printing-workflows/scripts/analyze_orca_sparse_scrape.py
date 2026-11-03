#!/usr/bin/env python3
"""Quantify sparse-infill self-crossings and no-lift travel crossings in Orca G-code.

Usage:
    python3 analyze_orca_sparse_scrape.py plate_1.gcode report.json

The probe is dependency-free and intentionally counts straight G1 sparse-infill
segments only. Arc crossings are omitted, so crossing totals are lower bounds.

Supported input (anything else is refused with a message, never guessed):
  * absolute XY positioning (G90, which is also the default);
  * relative extrusion declared with M83 before the first E word;
  * commands are parsed after removing ';' comments, so words inside comments
    and mode words in comments have no effect.
Refused: any X/Y/Z motion while G91 is active, extrusion under M82 or before
M83, and non-extruding G2/G3 arcs while the role is "Sparse infill" (their
crossings cannot be judged from the straight chord).
Also refused, by line and field: an X/Y/Z/E/F/I/J/R word of a G0-G3 command whose
value is not a finite decimal number (malformed, NaN, infinite or overflowing; the
raw value is not echoed), a full-circle G2/G3 arc in any role, i.e. one with I/J/R
whose end point equals its start (it would otherwise be miscounted as a
deretraction or a no-op; no arc geometry is computed here), and a report path that
is the same file as the source (same path, symlink, hardlink or normalised-path
alias), which is refused before anything is written. Only these words, arcs and
paths are checked: this is a narrow probe, not a G-code interpreter, and other
unsupported G-code is not detected.

Full-circle equivalence: an arc end point counts as equal to its start when it is within
1e-9 mm per X and per Y of it (a per-coordinate tolerance, not exact equality), so an
end point 5e-10 mm away is still refused as a full circle while one clearly outside
the tolerance is an ordinary end-point-only arc. The tolerance is part of the existing
design; no arc geometry is computed. (The seam helper compares exactly instead.)

Declared layer-Z metadata (``;Z:``) must be a finite decimal number: a malformed, NaN,
infinite or overflowing value is refused by line before any report (the raw value is
not echoed), and the report is serialised as strict JSON (no NaN or Infinity). When
the report path already exists but its identity cannot be determined relative to the
source (permission or I/O fault, dangling link), the helper refuses instead of writing.
The destination is probed with an explicit lstat: only FileNotFoundError is a
confirmed missing destination and skips the comparison; any other OSError from the
probe leaves the destination undetermined and the helper refuses before any write
(no exists/lexists Boolean is used). No locks or concurrency guarantee is given.

Resource guard: one fixed spatial work budget of 1,000,000 units per invocation,
never reset (not per layer either) and with no override or automatic raise. Units
are charged BEFORE the work they pay for: a segment's whole bounding-box cell count
before any cell is visited (a call is refused up front when it alone is too large),
each bucket's length before its entries are traversed (repeated entries count, not
just distinct candidates), the distinct candidate count before the intersection
checks, and the cell visits of every grid insertion. When the budget is exceeded the
run stops with an explicit message, writes no report and leaves the source untouched:
that input is NOT DONE by this probe, and the next step is a separately qualified
bounded backend, not a retry. A full real-plate G-code can exceed this budget. The
budget is an implementation guard of this narrow probe, not OS containment, a
benchmark, a memory or wall-clock limit, or a claim that accepted inputs are cheap.
"""
from __future__ import annotations

import collections
import json
import math
import os
import re
import statistics
import sys
from pathlib import Path

MOTION = ("G0", "G1", "G2", "G3")
WORK_LIMIT = 1_000_000  # fixed per-invocation spatial work budget (units); an implementation guard, not a printer limit or an override
DECIMAL = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?")


def motion_words(words, line_number, name):
    """Parse the admitted X/Y/Z/E/F/I/J/R words; refuse a malformed or nonfinite number by line and letter (never echoed)."""
    params = {}
    for word in words[1:]:
        letter = word[0].upper()
        if letter not in "XYZEFIJR":
            continue
        value = float(word[1:]) if DECIMAL.fullmatch(word[1:]) else math.nan
        if not math.isfinite(value):
            raise SystemExit(
                f"line {line_number}: the {letter} word on a {name} motion command is not a finite decimal number; refusing (the value is not echoed)"
            )
        params[letter] = value
    return params


def parse_layer_z(payload, line_number):
    """The declared layer Z (`;Z:`): a finite decimal number, or the run is refused (the raw value is never echoed)."""
    text = payload.strip()
    value = float(text) if DECIMAL.fullmatch(text) else math.nan
    if not math.isfinite(value):
        raise SystemExit(f"line {line_number}: the ;Z: layer-Z metadata is not a finite decimal number; refusing (the value is not echoed)")
    return value


def proper_intersection(a, b, c, d, eps=1e-8):
    def orient(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])

    o1, o2, o3, o4 = orient(a, b, c), orient(a, b, d), orient(c, d, a), orient(c, d, b)
    return (
        ((o1 > eps and o2 < -eps) or (o1 < -eps and o2 > eps))
        and ((o3 > eps and o4 < -eps) or (o3 < -eps and o4 > eps))
    )


def quantile(values, q):
    if not values:
        return None
    ordered = sorted(values)
    return ordered[round((len(ordered) - 1) * q)]


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: analyze_orca_sparse_scrape.py plate.gcode report.json")
    source, target = Path(sys.argv[1]), Path(sys.argv[2])
    # Probe the destination explicitly: only FileNotFoundError from lstat is a CONFIRMED missing destination. Any other OSError
    # (permission, I/O, a non-directory path component, ...) leaves the destination undetermined, so refuse before any write.
    # A Boolean such as lexists/exists would silently turn those errors into "missing".
    try:
        os.lstat(target)
        destination_exists = True
    except FileNotFoundError:
        destination_exists = False
    except OSError:
        raise SystemExit("The report path cannot be probed, so its identity cannot be determined relative to the source G-code; refusing to write it. Nothing was written.") from None
    if destination_exists:
        try:
            aliased = os.path.samefile(source, target)  # same path, normalised path, symlink or hardlink to the source
        except OSError:
            # Permission or I/O fault, dangling link, missing source: the comparison cannot be made, so fail closed.
            raise SystemExit("The report path exists but its identity cannot be determined relative to the source G-code; refusing to write it. Nothing was written.") from None
        if aliased:
            raise SystemExit("The report path is the same file as the source G-code (same path, symlink or hardlink alias); choose a distinct sibling report path. Nothing was written.")
    x = y = z = feed = 0.0
    nominal_z = None
    role = ""
    relative_e = None  # unknown until M83 / M82 is seen
    relative_xy = False  # G90 is the default
    layer = -1
    path_id = 0
    sparse_segments = []
    grid = collections.defaultdict(list)
    cell_size = 5.0
    stats = collections.Counter()
    layer_stats = collections.defaultdict(collections.Counter)
    travel_speeds = []
    extrusion_speeds = []
    crossing_examples = []

    work = 0  # spatial work units charged so far in this invocation; never reset (not per layer either)
    current_line = 0

    def charge(units):
        """Charge spatial work BEFORE the iteration it pays for; stop explicitly once the fixed budget is exceeded."""
        nonlocal work
        work += units
        if work > WORK_LIMIT:
            raise SystemExit(
                f"line {current_line}: the spatial work budget of {WORK_LIMIT:,} units for one invocation is exceeded; "
                "this input is beyond the admitted capacity of this narrow probe, NOT DONE for it "
                "(use a separately qualified bounded backend, do not retry unsafely). No report was written."
            )

    def cells_for(a, b):
        ix0 = math.floor(min(a[0], b[0]) / cell_size)
        ix1 = math.floor(max(a[0], b[0]) / cell_size)
        iy0 = math.floor(min(a[1], b[1]) / cell_size)
        iy1 = math.floor(max(a[1], b[1]) / cell_size)
        charge((ix1 - ix0 + 1) * (iy1 - iy0 + 1))  # the whole bounding box is admitted or refused before any cell is visited
        for ix in range(ix0, ix1 + 1):
            for iy in range(iy0, iy1 + 1):
                yield ix, iy

    def gather(a, b):
        """Distinct indexed segments in the cells of a-b; every bucket's length is charged before it is traversed."""
        found = set()
        for key in cells_for(a, b):
            bucket = grid.get(key, ())
            charge(len(bucket))
            found.update(bucket)
        return found

    def reset_layer():
        nonlocal sparse_segments, grid, path_id
        sparse_segments = []
        grid = collections.defaultdict(list)
        path_id = 0

    with source.open(errors="replace") as handle:
        for line_number, line in enumerate(handle, 1):
            current_line = line_number
            text = line.strip()
            if text == ";LAYER_CHANGE":
                layer += 1
                reset_layer()
                continue
            if text.startswith(";Z:"):
                nominal_z = parse_layer_z(text[3:], line_number)
                continue
            if text.startswith(";TYPE:"):
                role = text[6:]
                path_id += 1
                continue
            words = text.split(";", 1)[0].split()
            name = words[0].upper() if words else ""
            if name in ("M83", "M82"):
                relative_e = name == "M83"
                continue
            if name in ("G90", "G91"):
                relative_xy = name == "G91"
                continue
            if name not in MOTION:
                continue
            code = int(name[1])
            args = motion_words(words, line_number, name)
            if relative_xy and args.keys() & {"X", "Y", "Z"}:
                raise SystemExit(f"line {line_number}: X/Y/Z motion under G91 relative positioning is not supported; regenerate with G90")
            if "E" in args and relative_e is not True:
                raise SystemExit(
                    f"line {line_number}: "
                    + ("extrusion under M82 absolute-E mode is not supported" if relative_e is False else "extrusion before any M83 (relative extrusion not declared)")
                    + "; regenerate with M83 declared first"
                )
            if code in (2, 3) and args.keys() & {"I", "J", "R"} and abs(args.get("X", x) - x) <= 1e-9 and abs(args.get("Y", y) - y) <= 1e-9:
                raise SystemExit(
                    f"line {line_number}: {name} arc with I/J/R whose end point equals its start within 1e-9 mm per X and per Y (a full circle) is not supported; "
                    "it is neither a no-op nor a chord and no arc geometry is computed here"
                )
            if code in (2, 3) and role == "Sparse infill" and not args.get("E", 0) > 0 and args.keys() & {"X", "Y", "I", "J", "R"}:
                raise SystemExit(f"line {line_number}: non-extruding G2/G3 arc under Sparse infill is not supported (its crossings cannot be judged from the chord)")
            nx, ny, nz = args.get("X", x), args.get("Y", y), args.get("Z", z)
            next_feed = args.get("F", feed)
            moved_xy = abs(nx - x) > 1e-9 or abs(ny - y) > 1e-9
            e_value = args.get("E")
            is_extrusion = moved_xy and e_value is not None and e_value > 0
            is_travel = moved_xy and not is_extrusion
            start, end = (x, y), (nx, ny)
            distance = math.hypot(nx - x, ny - y)

            if e_value is not None and e_value < 0 and not moved_xy:
                stats["total_retractions"] += 1
                layer_stats[layer]["total_retractions"] += 1
                if role == "Sparse infill":
                    stats["sparse_retractions"] += 1
                    layer_stats[layer]["sparse_retractions"] += 1
            elif e_value is not None and e_value > 0 and not moved_xy:
                stats["total_deretractions"] += 1
                layer_stats[layer]["total_deretractions"] += 1
                if role == "Sparse infill":
                    stats["sparse_deretractions"] += 1
                    layer_stats[layer]["sparse_deretractions"] += 1

            hopped = nominal_z is not None and max(z, nz) > nominal_z + 0.05
            if role == "Sparse infill" and is_travel and distance > 1e-6:
                stats["sparse_xy_travels"] += 1
                layer_stats[layer]["sparse_xy_travels"] += 1
                travel_speeds.append(next_feed / 60.0)
                hop_key = "sparse_travels_hopped" if hopped else "sparse_travels_no_hop"
                stats[hop_key] += 1
                layer_stats[layer][hop_key] += 1

                candidates = gather(start, end)
                charge(len(candidates))  # one intersection check per candidate, charged before the checks run
                hits = [
                    index
                    for index in candidates
                    if proper_intersection(start, end, sparse_segments[index]["a"], sparse_segments[index]["b"])
                ]
                if hits:
                    stats["sparse_travels_cross_prior_sparse"] += 1
                    layer_stats[layer]["sparse_travels_cross_prior_sparse"] += 1
                    if not hopped:
                        stats["no_hop_travels_cross_prior_sparse"] += 1
                        layer_stats[layer]["no_hop_travels_cross_prior_sparse"] += 1
                    if len(crossing_examples) < 20:
                        crossing_examples.append(
                            {
                                "line": line_number,
                                "layer_index": layer,
                                "nominal_z": nominal_z,
                                "from": start,
                                "to": end,
                                "distance_mm": distance,
                                "speed_mm_s": next_feed / 60.0,
                                "hopped": hopped,
                                "prior_crossings": len(hits),
                            }
                        )
                path_id += 1
            elif is_travel:
                path_id += 1

            if role == "Sparse infill" and is_extrusion and code == 1 and distance > 1e-6:
                stats["sparse_straight_extrusions"] += 1
                layer_stats[layer]["sparse_straight_extrusions"] += 1
                extrusion_speeds.append(next_feed / 60.0)
                candidates = gather(start, end)
                charge(len(candidates))
                hits = 0
                for index in candidates:
                    segment = sparse_segments[index]
                    if segment["path_id"] == path_id and index == len(sparse_segments) - 1:
                        continue
                    if proper_intersection(start, end, segment["a"], segment["b"]):
                        hits += 1
                if hits:
                    stats["sparse_extrusions_cross_prior_sparse"] += 1
                    layer_stats[layer]["sparse_extrusions_cross_prior_sparse"] += 1
                index = len(sparse_segments)
                sparse_segments.append({"a": start, "b": end, "path_id": path_id})
                for key in cells_for(start, end):
                    grid[key].append(index)

            x, y, z, feed = nx, ny, nz, next_feed

    hottest_layers = sorted(
        (dict(values, layer_index=index) for index, values in layer_stats.items()),
        key=lambda row: (
            row.get("no_hop_travels_cross_prior_sparse", 0),
            row.get("sparse_extrusions_cross_prior_sparse", 0),
        ),
        reverse=True,
    )[:20]
    result = {
        "gcode": str(source),
        "counts": dict(stats),
        "travel_speed_mm_s": {
            "min": min(travel_speeds) if travel_speeds else None,
            "median": statistics.median(travel_speeds) if travel_speeds else None,
            "p95": quantile(travel_speeds, 0.95),
            "max": max(travel_speeds) if travel_speeds else None,
        },
        "sparse_extrusion_speed_mm_s": {
            "min": min(extrusion_speeds) if extrusion_speeds else None,
            "median": statistics.median(extrusion_speeds) if extrusion_speeds else None,
            "p95": quantile(extrusion_speeds, 0.95),
            "max": max(extrusion_speeds) if extrusion_speeds else None,
        },
        "hottest_layers": hottest_layers,
        "travel_crossing_examples": crossing_examples,
        "limitations": [
            "Only straight G1 sparse-extrusion segments are intersected; arc crossings are omitted, so counts are lower bounds.",
            "Travels are classified under the current Orca TYPE comment.",
            "Sloped Auto Lift may split one logical travel into several XY/Z moves; compare no-hop crossings, not raw travel totals alone.",
        ],
    }
    try:
        payload = json.dumps(result, indent=2, allow_nan=False)  # strict JSON: NaN/Infinity are never written
    except ValueError:
        raise SystemExit("The report contains a nonfinite number and was not written (strict JSON only). Nothing was written.") from None
    target.write_text(payload)
    print(payload)


if __name__ == "__main__":
    main()
