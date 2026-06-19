"""
Detect the PlayStation controller button stream from the Player 2 video.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
LOCAL_PYLIBS = SCRIPT_DIR / "pylibs"
if LOCAL_PYLIBS.exists():
    sys.path.insert(0, str(LOCAL_PYLIBS))

import cv2  # type: ignore  # noqa: E402
import numpy as np  # type: ignore  # noqa: E402


DEFAULT_VIDEO = Path(
    r"C:\Users\yevge\Downloads\YTDown_YouTube_player2_Media_dthKN5GNPOU_001_1080p.mp4"
)

# ROIs are for the 1920x1080 download. Each tuple is x, y, width, height.
# The shoulder ROIs intentionally separate the top "2" boxes from the curved
# lower shoulders, then post-processing suppresses bleed from the top boxes.
ROIS = {
    "L2": (138, 642, 50, 32),
    "R2": (443, 642, 50, 32),
    "L1": (138, 681, 50, 20),
    "R1": (443, 681, 50, 20),
    "UP": (145, 752, 35, 45),
    "DOWN": (145, 832, 35, 50),
    "LEFT": (94, 790, 45, 45),
    "RIGHT": (188, 790, 45, 45),
    "SELECT": (255, 798, 40, 32),
    "START": (365, 798, 42, 32),
    "TRIANGLE": (461, 725, 40, 45),
    "SQUARE": (416, 795, 40, 45),
    "X": (461, 856, 40, 45),
    "CIRCLE": (507, 795, 42, 45),
}

# These were visually checked as detector noise, not real P2 inputs.
KNOWN_FALSE_POSITIVE_STARTS = [
    ("R2", 69.567),
    ("R2", 112.667),
    ("R2", 112.800),
    ("R2", 113.867),
    ("L1", 150.400),
    ("L1", 151.000),
    ("L1", 161.533),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "video",
        nargs="?",
        type=Path,
        default=DEFAULT_VIDEO,
        help="Input MP4. Defaults to the downloaded Player 2 video.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=SCRIPT_DIR / "analysis" / "detected_p2_intervals.json",
        help="Cleaned interval JSON output.",
    )
    parser.add_argument(
        "--raw-output",
        type=Path,
        default=SCRIPT_DIR / "analysis" / "detected_p2_intervals.raw.json",
        help="Raw detector interval JSON output before cleanup.",
    )
    parser.add_argument(
        "--baseline-time",
        type=float,
        default=12.0,
        help="Timestamp, in seconds, of a frame with no lit buttons.",
    )
    parser.add_argument(
        "--stop-time",
        type=float,
        default=212.0,
        help="Stop scanning here, before the final non-message controller hold.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=120.0,
        help="Brightness-difference score required to call a button pressed.",
    )
    parser.add_argument(
        "--min-frames",
        type=int,
        default=3,
        help="Drop intervals shorter than this many frames during cleanup.",
    )
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Write raw detections as the cleaned output too.",
    )
    parser.add_argument(
        "--sheet-dir",
        type=Path,
        default=None,
        help="Optional directory for inspection sheets of detected presses.",
    )
    return parser.parse_args()


def read_frame_at(cap: cv2.VideoCapture, seconds: float) -> np.ndarray:
    cap.set(cv2.CAP_PROP_POS_MSEC, seconds * 1000)
    ok, frame = cap.read()
    if not ok:
        raise RuntimeError(f"Could not read frame at {seconds:.3f}s")
    return frame


def roi_score(gray: np.ndarray, baseline: np.ndarray) -> float:
    """Mean of the brightest 10% positive deltas in a button ROI."""

    delta = np.maximum(gray.astype(np.int16) - baseline, 0).ravel()
    top_n = max(1, len(delta) // 10)
    return float(np.mean(np.partition(delta, -top_n)[-top_n:]))


def choose_pressed(scores: dict[str, float], threshold: float) -> list[str]:
    pressed = [button for button, score in scores.items() if score >= threshold]

    # When L2/R2 top boxes light up, the lower L1/R1 arc ROI also sees some
    # brightness. Prefer the top shoulder in that overlap case.
    if "L2" in pressed and "L1" in pressed:
        pressed.remove("L1")
    if "R2" in pressed and "R1" in pressed:
        pressed.remove("R1")

    # The challenge presses one relevant button at a time. If an unrelated ROI
    # spikes because of background/aliasing, keep the strongest one.
    if len(pressed) > 1:
        pressed = [max(pressed, key=lambda button: scores[button])]

    return pressed


def detect_intervals(
    video: Path,
    baseline_time: float,
    stop_time: float,
    threshold: float,
) -> list[dict]:
    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps:
        raise RuntimeError("Could not determine video FPS")

    baseline_frame = read_frame_at(cap, baseline_time)
    baseline_gray = cv2.cvtColor(baseline_frame, cv2.COLOR_BGR2GRAY).astype(np.int16)
    baselines = {
        button: baseline_gray[y : y + h, x : x + w]
        for button, (x, y, w, h) in ROIS.items()
    }

    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    intervals: list[dict] = []
    active: dict | None = None
    frame_index = 0

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        t = frame_index / fps
        frame_index += 1
        if t > stop_time:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.int16)
        scores = {}
        for button, (x, y, w, h) in ROIS.items():
            scores[button] = roi_score(gray[y : y + h, x : x + w], baselines[button])

        pressed = choose_pressed(scores, threshold)
        key = tuple(pressed)

        if key:
            if active and active["pressed"] == list(key) and t - active["last"] < 0.25:
                active["last"] = t
                active["frames"] += 1
                active["scores"].append(scores)
            else:
                if active:
                    intervals.append(active)
                active = {
                    "start": t,
                    "last": t,
                    "pressed": list(key),
                    "frames": 1,
                    "scores": [scores],
                }
        elif active:
            intervals.append(active)
            active = None

    if active:
        intervals.append(active)

    cap.release()
    return intervals


def is_known_false_positive(interval: dict) -> bool:
    if len(interval["pressed"]) != 1:
        return False

    button = interval["pressed"][0]
    start = interval["start"]
    for false_button, false_start in KNOWN_FALSE_POSITIVE_STARTS:
        if button == false_button and abs(start - false_start) <= 0.04:
            return True
    return False


def clean_intervals(intervals: list[dict], min_frames: int) -> list[dict]:
    cleaned = []
    for interval in intervals:
        if interval["frames"] < min_frames:
            continue
        if is_known_false_positive(interval):
            continue
        cleaned.append(interval)
    return cleaned


def summarize(intervals: list[dict]) -> str:
    lines = []
    for i, interval in enumerate(intervals, 1):
        pressed = "+".join(interval["pressed"])
        lines.append(f"{i:03d} {interval['start']:7.3f} {pressed}")
    return "\n".join(lines)


def write_json(path: Path, intervals: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(intervals, indent=2), encoding="utf-8")


def save_inspection_sheets(video: Path, intervals: list[dict], sheet_dir: Path) -> None:
    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video}")

    sheet_dir.mkdir(parents=True, exist_ok=True)
    cells = []
    for i, interval in enumerate(intervals, 1):
        t = interval["start"]
        frame = read_frame_at(cap, t)
        crop = frame[560:1050, 0:560]
        crop = cv2.resize(crop, (560, 490), interpolation=cv2.INTER_CUBIC)
        cv2.rectangle(crop, (0, 0), (150, 34), (0, 0, 0), -1)
        label = f"{i:03d} {t:.1f} {'+'.join(interval['pressed'])}"
        cv2.putText(
            crop,
            label,
            (7, 24),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )
        cells.append(crop)

    cap.release()

    cols = 4
    chunk_size = 40
    for sheet_index in range(0, len(cells), chunk_size):
        chunk = cells[sheet_index : sheet_index + chunk_size]
        rows = math.ceil(len(chunk) / cols)
        sheet = np.zeros((rows * 490, cols * 560, 3), dtype=np.uint8)
        for i, cell in enumerate(chunk):
            row = i // cols
            col = i % cols
            sheet[row * 490 : (row + 1) * 490, col * 560 : (col + 1) * 560] = cell
        out = sheet_dir / f"detected_{sheet_index // chunk_size + 1:02d}.jpg"
        cv2.imwrite(str(out), sheet)


def main() -> int:
    args = parse_args()

    raw = detect_intervals(
        video=args.video,
        baseline_time=args.baseline_time,
        stop_time=args.stop_time,
        threshold=args.threshold,
    )
    cleaned = raw if args.no_cleanup else clean_intervals(raw, args.min_frames)

    write_json(args.raw_output, raw)
    write_json(args.output, cleaned)

    if args.sheet_dir:
        save_inspection_sheets(args.video, cleaned, args.sheet_dir)

    print(f"raw intervals: {len(raw)} -> {args.raw_output}")
    print(f"clean intervals: {len(cleaned)} -> {args.output}")
    print()
    print(summarize(cleaned))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
