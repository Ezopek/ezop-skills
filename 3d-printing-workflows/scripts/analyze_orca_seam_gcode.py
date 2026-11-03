#!/usr/bin/env python3
"""Quantify OrcaSlicer seam gaps and retracts from relative-E G-code.

Requires Orca role comments such as ``;TYPE:Outer wall``.

Supported input (anything else is refused with a message, never guessed):
  * absolute XY positioning (G90, which is also the default);
  * relative extrusion declared with M83 before the first E word;
  * commands are parsed after removing ';' comments, so words inside comments
    and mode words in comments have no effect.
Refused: any X/Y/Z motion while G91 is active, extrusion under M82 or before
M83, and non-extruding G2/G3 arcs (their length is not the straight chord).
Extruding G2/G3 arcs are accepted: only their exact end points are used.
Also refused, by line and field: an X/Y/Z/E/F/I/J/R word of a G0-G3 command whose
value is not a finite decimal number (malformed, NaN, infinite or overflowing; the
raw value is not echoed), and a full-circle G2/G3 arc, i.e. one with I/J/R whose end
point equals its start (it is neither a no-op nor a chord, and no arc geometry is
computed here). Only these words and arcs are checked: this is a narrow probe, not
a G-code interpreter, and other unsupported G-code is not detected.
Declared layer-Z metadata (``;Z:``) must also be a finite decimal number: a malformed,
NaN, infinite or overflowing value is refused by line (the raw value is not echoed)
instead of being skipped or printed.
This helper compares an arc's end point to its start exactly: there is no tolerance
here, so an end point that differs at all (however slightly) is an ordinary end-point-only
arc and only an identical one is the refused full circle. (The sparse helper, by
contrast, treats end points within 1e-9 mm per X and per Y as equal.)

Finite derived metrics: words that are individually finite can still overflow a derived
value, namely a coordinate difference or hypot (move length, direct travel, path gap),
an accumulated total (a path's extrusion, the non-extruding travel, the retraction and
de-retraction totals) or an even-length median that adds two large gaps. Every such
tracked or reported value is checked, and a nonfinite one is refused by line with a
clear message; because the whole report is buffered until every check has passed, no
output is printed on a refusal, and ordinary output is unchanged byte for byte. The
numeric command-line options feed the same report and must be finite numbers too.
There is no physical coordinate cap: large values that stay representable work.
"""

from __future__ import annotations

import argparse
import math
import re
import statistics
from collections import Counter

MOTION = ("G0", "G1", "G2", "G3")
DECIMAL = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?")


def parse_layer_z(payload: str, line_number: int) -> float:
    """The declared layer Z (`;Z:`): a finite decimal number, or the run is refused (the raw value is never echoed)."""
    text = payload.strip()
    value = float(text) if DECIMAL.fullmatch(text) else math.nan
    if not math.isfinite(value):
        raise SystemExit(f"line {line_number}: the ;Z: layer-Z metadata is not a finite decimal number; refusing (the value is not echoed)")
    return value


def motion_words(words: list[str], line_number: int, name: str) -> dict[str, float]:
    """Parse the admitted X/Y/Z/E/F/I/J/R words; refuse a malformed or nonfinite number by line and letter (never echoed)."""
    params: dict[str, float] = {}
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


def finite_option(text: str) -> float:
    """argparse type for the numeric options: they feed the report, so a NaN, an infinity or an overflowing value is refused."""
    try:
        value = float(text)
    except ValueError:
        raise argparse.ArgumentTypeError("must be a finite number") from None
    if not math.isfinite(value):
        raise argparse.ArgumentTypeError("must be a finite number")
    return value


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    return ordered[round((len(ordered) - 1) * fraction)]


def percent(part: int, whole: int) -> float:
    return 100.0 * part / whole if whole else 0.0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("gcode")
    parser.add_argument("--short-travel-mm", type=finite_option, default=2.0)
    parser.add_argument("--closed-loop-max-gap-mm", type=finite_option, default=0.2)
    parser.add_argument("--target-gap-mm", type=finite_option)
    parser.add_argument("--target-gap-tolerance-mm", type=finite_option, default=0.005)
    parser.add_argument("--expected-retraction-mm", type=finite_option)
    parser.add_argument("--retraction-tolerance-mm", type=finite_option, default=0.01)
    parser.add_argument("--examples", type=int, default=10)
    args = parser.parse_args()

    x = y = z = 0.0
    role: str | None = None
    layer = -1
    layer_z = 0.0
    relative_e: bool | None = None  # unknown until M83 / M82 is seen
    relative_xy = False  # G90 is the default
    current_path: dict | None = None
    paths: list[dict] = []
    last_extrusion_end: tuple[float, float] | None = None
    pending_deretract = 0.0
    pending_retract = 0.0
    actual_nonextrude_xy = 0.0
    current_line = 0
    lines: list[str] = []  # the whole report is buffered: a refusal at any point prints nothing at all

    def ensure_finite(value: float, what: str) -> float:
        """Individually finite words can still overflow a derived value (difference, hypot, total, even-length median)."""
        if not math.isfinite(value):
            raise SystemExit(
                f"line {current_line}: the derived {what} is not a finite number (finite inputs overflowed); refusing before any report is printed"
            )
        return value

    def finish_path(reason: str) -> None:
        nonlocal current_path, last_extrusion_end
        nonlocal pending_deretract, pending_retract, actual_nonextrude_xy
        if current_path is None:
            return
        sx, sy = current_path["start"]
        ex, ey = current_path["end"]
        current_path["gap_mm"] = ensure_finite(math.hypot(ex - sx, ey - sy), "path gap")
        current_path["end_reason"] = reason
        paths.append(current_path)
        last_extrusion_end = current_path["end"]
        current_path = None
        pending_deretract = 0.0
        pending_retract = 0.0
        actual_nonextrude_xy = 0.0

    with open(args.gcode, "r", errors="replace") as handle:
        for line_number, raw in enumerate(handle, 1):
            current_line = line_number
            line = raw.strip()
            if line.startswith(";Z:"):
                layer_z = parse_layer_z(line[3:], line_number)
                layer += 1
                continue
            if line.startswith(";TYPE:"):
                new_role = line[6:]
                if current_path is not None and new_role != role:
                    finish_path("role_change")
                role = new_role
                continue

            words = line.split(";", 1)[0].split()
            name = words[0].upper() if words else ""
            if name in ("M83", "M82"):
                relative_e = name == "M83"
                continue
            if name in ("G90", "G91"):
                relative_xy = name == "G91"
                continue
            if name not in MOTION:
                continue
            params = motion_words(words, line_number, name)
            if relative_xy and params.keys() & {"X", "Y", "Z"}:
                raise SystemExit("Unsupported G91 relative positioning for X/Y/Z motion; regenerate with G90")
            old_x, old_y = x, y
            new_x = params.get("X", x)
            new_y = params.get("Y", y)
            new_z = params.get("Z", z)
            e_delta = params.get("E")
            if e_delta is not None and relative_e is False:
                raise SystemExit(
                    "Unsupported active M82 absolute-E extrusion; regenerate normal Orca M83 G-code"
                )
            if e_delta is not None and relative_e is None:
                raise SystemExit(
                    "Extrusion before any M83 (relative extrusion not declared); regenerate normal Orca M83 G-code"
                )

            xy_move = ("X" in params or "Y" in params) and (
                new_x != x or new_y != y
            )
            xy_distance = ensure_finite(math.hypot(new_x - x, new_y - y), "XY move length") if xy_move else 0.0
            positive_extrusion_move = (
                xy_move and e_delta is not None and e_delta > 0
            )
            if name in ("G2", "G3") and not xy_move and params.keys() & {"I", "J", "R"}:
                raise SystemExit(
                    f"line {line_number}: {name} arc with I/J/R whose end point equals its start exactly (no tolerance; a full circle) is not supported; "
                    "it is neither a no-op nor a chord and no arc geometry is computed here"
                )
            if name in ("G2", "G3") and xy_move and not positive_extrusion_move:
                raise SystemExit("Unsupported non-extruding G2/G3 arc: its travel length is not the straight chord")

            if positive_extrusion_move:
                if current_path is None:
                    direct_travel = (
                        ensure_finite(
                            math.hypot(
                                old_x - last_extrusion_end[0],
                                old_y - last_extrusion_end[1],
                            ),
                            "direct travel distance",
                        )
                        if last_extrusion_end is not None
                        else None
                    )
                    current_path = {
                        "role": role,
                        "layer": layer,
                        "z": layer_z,
                        "start": (old_x, old_y),
                        "end": (new_x, new_y),
                        "moves": 1,
                        "positive_e": e_delta,
                        "prev_direct_travel_mm": direct_travel,
                        "actual_nonextrude_xy_mm": actual_nonextrude_xy,
                        "deretract_e_mm": pending_deretract,
                        "retract_e_mm": pending_retract,
                    }
                else:
                    current_path["end"] = (new_x, new_y)
                    current_path["moves"] += 1
                    current_path["positive_e"] = ensure_finite(current_path["positive_e"] + e_delta, "extrusion total of a path")
            else:
                if current_path is not None and (
                    xy_move or (e_delta is not None and e_delta < 0)
                ):
                    finish_path("nonextrude")
                if xy_move:
                    actual_nonextrude_xy = ensure_finite(actual_nonextrude_xy + xy_distance, "non-extruding travel total")
                if e_delta is not None:
                    if e_delta > 0:
                        pending_deretract = ensure_finite(pending_deretract + e_delta, "de-retraction total")
                    elif e_delta < 0:
                        pending_retract = ensure_finite(pending_retract + -e_delta, "retraction total")

            x, y, z = new_x, new_y, new_z

    finish_path("eof")
    emit = lines.append  # nothing reaches stdout until every derived value below has passed the finite check
    emit(f"gcode={args.gcode}")
    emit(f"all_paths={len(paths)} layers={layer + 1}")

    for role_name in ("Outer wall", "Inner wall"):
        selected = [item for item in paths if item["role"] == role_name]
        gaps = [item["gap_mm"] for item in selected]
        travels = [
            item["prev_direct_travel_mm"]
            for item in selected
            if item["prev_direct_travel_mm"] is not None
        ]
        closed = [
            item
            for item in selected
            if item["gap_mm"] <= args.closed_loop_max_gap_mm
        ]
        retracted = [item for item in selected if item["retract_e_mm"] > 0.05]
        emit(f"\n[{role_name}]")
        emit(
            f"paths={len(selected)} closed={len(closed)} "
            f"({percent(len(closed), len(selected)):.1f}%)"
        )
        if gaps:
            median_gap = ensure_finite(statistics.median(gaps), "median gap")  # an even-length median adds two finite gaps first
            emit(
                "gap_mm min/p10/median/p90/max="
                f"{min(gaps):.5f}/{percentile(gaps, .1):.5f}/"
                f"{median_gap:.5f}/{percentile(gaps, .9):.5f}/"
                f"{max(gaps):.5f}"
            )
            buckets = Counter(round(value, 3) for value in gaps).most_common(10)
            emit(f"common_gap_buckets={dict(buckets)}")
        if travels:
            short = sum(value < args.short_travel_mm for value in travels)
            emit(
                f"prev_direct_travel_below_{args.short_travel_mm:g}mm="
                f"{short}/{len(travels)} ({percent(short, len(travels)):.1f}%)"
            )
        emit(
            f"paths_with_retract={len(retracted)}/{len(selected)} "
            f"({percent(len(retracted), len(selected)):.1f}%)"
        )
        if args.expected_retraction_mm is not None:
            full = sum(
                abs(item["retract_e_mm"] - args.expected_retraction_mm)
                <= args.retraction_tolerance_mm
                and abs(item["deretract_e_mm"] - args.expected_retraction_mm)
                <= args.retraction_tolerance_mm
                for item in selected
            )
            emit(
                f"full_retract_deretract_near_{args.expected_retraction_mm:g}mm="
                f"{full}/{len(selected)} ({percent(full, len(selected)):.1f}%)"
            )
        if args.target_gap_mm is not None:
            target = sum(
                abs(item["gap_mm"] - args.target_gap_mm)
                <= args.target_gap_tolerance_mm
                for item in selected
            )
            emit(
                f"paths_near_target_gap_{args.target_gap_mm:g}mm="
                f"{target}/{len(selected)} ({percent(target, len(selected)):.1f}%)"
            )

    outer = [item for item in paths if item["role"] == "Outer wall"]
    examples = [
        item
        for item in outer
        if item["prev_direct_travel_mm"] is not None
        and item["prev_direct_travel_mm"] < args.short_travel_mm
        and item["retract_e_mm"] > 0.05
    ]
    examples.sort(key=lambda item: (item["prev_direct_travel_mm"], item["layer"]))
    emit("\n[Representative short-hop outer paths with retraction]")
    for item in examples[: args.examples]:
        emit(
            f"layer={item['layer']} z={item['z']:.2f} "
            f"gap={item['gap_mm']:.5f} "
            f"prev_direct={item['prev_direct_travel_mm']:.4f} "
            f"actual_nonextrude={item['actual_nonextrude_xy_mm']:.3f} "
            f"retract={item['retract_e_mm']:.3f} "
            f"deretract={item['deretract_e_mm']:.3f} "
            f"start={item['start']} end={item['end']}"
        )
    print("\n".join(lines))  # byte-for-byte what the separate print calls produced


if __name__ == "__main__":
    main()
