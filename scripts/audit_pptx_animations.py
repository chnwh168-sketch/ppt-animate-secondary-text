#!/usr/bin/env python3
"""Read-only structural audit for click-reveal animations in PPTX files."""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
}

SLIDE_RE = re.compile(r"^ppt/slides/slide(\d+)\.xml$")
STATIC_TOKENS = {"•", "●", "○", "↓", "→", "+", "AI"}
TITLE_PLACEHOLDERS = {"title", "ctrTitle"}


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def normalize_text(value: str) -> str:
    value = value.replace("\u00a0", " ").replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(" ".join(line.split()) for line in value.split("\n")).strip()


def slide_number(name: str) -> int:
    match = SLIDE_RE.match(name)
    if not match:
        raise ValueError(f"Not a slide path: {name}")
    return int(match.group(1))


def read_deck(path: Path) -> tuple[zipfile.ZipFile, list[str]]:
    try:
        archive = zipfile.ZipFile(path)
    except (OSError, zipfile.BadZipFile) as exc:
        raise ValueError(f"Cannot open PPTX archive {path}: {exc}") from exc
    bad_member = archive.testzip()
    if bad_member:
        archive.close()
        raise ValueError(f"Corrupt PPTX member in {path}: {bad_member}")
    slides = sorted(
        (name for name in archive.namelist() if SLIDE_RE.match(name)),
        key=slide_number,
    )
    if not slides:
        archive.close()
        raise ValueError(f"No slide XML found in {path}")
    return archive, slides


def element_text(element: ET.Element) -> str:
    paragraphs: list[str] = []
    for paragraph in element.findall(".//a:p", NS):
        text = "".join(node.text or "" for node in paragraph.findall(".//a:t", NS))
        if text:
            paragraphs.append(text)
    return normalize_text("\n".join(paragraphs))


def placeholder_type(element: ET.Element) -> str | None:
    placeholder = element.find(".//p:nvPr/p:ph", NS)
    return placeholder.get("type") if placeholder is not None else None


def shape_records(root: ET.Element) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for element in root.iter():
        if local_name(element.tag) not in {"sp", "grpSp", "graphicFrame", "pic", "cxnSp"}:
            continue
        properties = element.find("./p:nvSpPr/p:cNvPr", NS)
        if properties is None:
            properties = element.find("./p:nvGrpSpPr/p:cNvPr", NS)
        if properties is None:
            properties = element.find("./p:nvGraphicFramePr/p:cNvPr", NS)
        if properties is None:
            properties = element.find("./p:nvPicPr/p:cNvPr", NS)
        if properties is None:
            properties = element.find("./p:nvCxnSpPr/p:cNvPr", NS)
        if properties is None or properties.get("id") is None:
            continue
        shape_id = properties.get("id", "")
        records[shape_id] = {
            "id": shape_id,
            "name": properties.get("name", ""),
            "kind": local_name(element.tag),
            "placeholder": placeholder_type(element),
            "text": element_text(element),
        }
    return records


def visible_text(root: ET.Element) -> list[str]:
    result: list[str] = []
    for paragraph in root.findall(".//p:spTree//a:p", NS):
        text = "".join(node.text or "" for node in paragraph.findall(".//a:t", NS))
        if text:
            result.append(text)
    return result


def animation_target_ids(root: ET.Element) -> tuple[list[str], list[str]]:
    raw = [node.get("spid", "") for node in root.findall(".//p:timing//p:spTgt", NS)]
    raw = [shape_id for shape_id in raw if shape_id]
    unique: list[str] = []
    seen: set[str] = set()
    for shape_id in raw:
        if shape_id not in seen:
            unique.append(shape_id)
            seen.add(shape_id)
    return raw, unique


def analyze_slide(archive: zipfile.ZipFile, name: str) -> dict[str, Any]:
    root = ET.fromstring(archive.read(name))
    records = shape_records(root)
    raw_ids, target_ids = animation_target_ids(root)
    targets: list[dict[str, Any]] = []
    for target_id in target_ids:
        record = records.get(target_id)
        if record is None:
            targets.append({"id": target_id, "missing_shape": True, "text": ""})
        else:
            targets.append(record)
    return {
        "slide": slide_number(name),
        "visible_text": visible_text(root),
        "raw_target_refs": raw_ids,
        "targets": targets,
        "shapes": list(records.values()),
    }


def load_plan(path: Path) -> tuple[int, dict[int, list[str]]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read target plan {path}: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("slides"), dict):
        raise ValueError("Target plan must contain an object named 'slides'")
    start_slide = data.get("start_slide", 3)
    if not isinstance(start_slide, int) or start_slide < 1:
        raise ValueError("Target plan 'start_slide' must be a positive integer")
    slides: dict[int, list[str]] = {}
    for key, entries in data["slides"].items():
        try:
            number = int(key)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid slide key in target plan: {key!r}") from exc
        if not isinstance(entries, list) or not all(isinstance(item, str) for item in entries):
            raise ValueError(f"Plan for slide {number} must be a list of strings")
        slides[number] = [normalize_text(item) for item in entries]
    return start_slide, slides


def audit(args: argparse.Namespace) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    final_archive, final_names = read_deck(args.final)
    try:
        final_slides = [analyze_slide(final_archive, name) for name in final_names]
    finally:
        final_archive.close()

    start_slide = args.start_slide
    plan: dict[int, list[str]] | None = None
    if args.plan:
        plan_start, plan = load_plan(args.plan)
        if args.start_slide is not None and args.start_slide != plan_start:
            errors.append(
                f"CLI start slide {args.start_slide} differs from plan start slide {plan_start}"
            )
        start_slide = plan_start
    if start_slide is None:
        start_slide = 3

    source_summary: dict[str, Any] | None = None
    if args.source:
        source_archive, source_names = read_deck(args.source)
        try:
            source_slides = [analyze_slide(source_archive, name) for name in source_names]
        finally:
            source_archive.close()
        if len(source_slides) != len(final_slides):
            errors.append(
                f"Slide count changed: source={len(source_slides)}, final={len(final_slides)}"
            )
        for source, final in zip(source_slides, final_slides):
            source_text = source["visible_text"]
            final_text = final["visible_text"]
            if Counter(source_text) != Counter(final_text):
                errors.append(f"Slide {final['slide']}: visible text content differs from source")
            elif source_text != final_text:
                warnings.append(
                    f"Slide {final['slide']}: visible text is unchanged but XML text order differs"
                )
        source_summary = {"path": str(args.source), "slide_count": len(source_slides)}

    final_count = len(final_slides)
    if start_slide > final_count:
        errors.append(f"Start slide {start_slide} is beyond final slide count {final_count}")

    if plan is not None:
        required = set(range(start_slide, final_count + 1))
        missing = sorted(required - set(plan))
        extra = sorted(set(plan) - required)
        if missing:
            errors.append(f"Target plan omits slides: {missing}")
        if extra:
            errors.append(f"Target plan contains out-of-scope slides: {extra}")

    for slide in final_slides:
        number = slide["slide"]
        targets = slide["targets"]
        target_text = [normalize_text(target.get("text", "")) for target in targets]
        if number < start_slide and targets:
            errors.append(f"Slide {number}: has {len(targets)} animation target(s) before start slide")
        for index, target in enumerate(targets, start=1):
            label = f"Slide {number}, target {index}"
            text = normalize_text(target.get("text", ""))
            if target.get("missing_shape"):
                errors.append(f"{label}: shape id {target['id']} cannot be resolved")
            elif target.get("kind") != "sp":
                errors.append(f"{label}: targets {target.get('kind')} instead of a text shape")
            elif not text:
                errors.append(f"{label}: target has no visible text")
            elif target.get("placeholder") in TITLE_PLACEHOLDERS:
                errors.append(f"{label}: title placeholder must remain static ({text!r})")
            elif text in STATIC_TOKENS:
                errors.append(f"{label}: decorative/static token must not animate ({text!r})")
        if plan is not None and number >= start_slide:
            expected = plan.get(number, [])
            if target_text != expected:
                errors.append(
                    f"Slide {number}: target order mismatch; expected={expected!r}, actual={target_text!r}"
                )

    return {
        "passed": not errors,
        "source": source_summary,
        "final": {"path": str(args.final), "slide_count": final_count},
        "start_slide": start_slide,
        "errors": errors,
        "warnings": warnings,
        "slides": [
            {
                "slide": item["slide"],
                "target_count": len(item["targets"]),
                "targets": item["targets"],
                "shapes": item["shapes"],
            }
            for item in final_slides
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--final", required=True, type=Path, help="Final animated PPTX")
    parser.add_argument("--source", type=Path, help="Clean source PPTX for text comparison")
    parser.add_argument("--plan", type=Path, help="JSON target plan")
    parser.add_argument("--start-slide", type=int, help="First slide allowed to animate")
    parser.add_argument("--report", type=Path, help="Optional JSON report path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report = audit(args)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    output = json.dumps(report, ensure_ascii=False, indent=2)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(output + "\n", encoding="utf-8")
    print("PASS" if report["passed"] else "FAIL")
    for error in report["errors"]:
        print(f"ERROR: {error}")
    for warning in report["warnings"]:
        print(f"WARNING: {warning}")
    for slide in report["slides"]:
        labels = [target.get("text", "") for target in slide["targets"]]
        print(f"Slide {slide['slide']}: {slide['target_count']} target(s) {labels}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
