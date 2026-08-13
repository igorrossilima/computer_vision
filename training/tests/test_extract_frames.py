from __future__ import annotations

import csv
import importlib.util
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import cv2
import numpy as np


SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "extract_frames.py"
SPEC = importlib.util.spec_from_file_location("extract_frames", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
extract_frames = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = extract_frames
SPEC.loader.exec_module(extract_frames)


class FakeCapture:
    def __init__(self, frames: list[np.ndarray], fps: float = 1.0, opened: bool = True):
        self.frames = [frame.copy() for frame in frames]
        self.fps = fps
        self.opened = opened
        self.position = 0
        self.released = False

    def isOpened(self) -> bool:
        return self.opened

    def get(self, property_id: int) -> float:
        if property_id == cv2.CAP_PROP_FPS:
            return self.fps
        return 0.0

    def read(self) -> tuple[bool, np.ndarray | None]:
        if self.position >= len(self.frames):
            return False, None
        frame = self.frames[self.position]
        self.position += 1
        return True, frame.copy()

    def release(self) -> None:
        self.released = True


def black_frame() -> np.ndarray:
    return np.zeros((100, 100, 3), dtype=np.uint8)


def frame_with_changed_rows(rows: int) -> np.ndarray:
    frame = black_frame()
    frame[:rows, :, :] = 255
    return frame


def write_fake_jpeg(path: str, _frame: np.ndarray, _params: list[int]) -> bool:
    Path(path).write_bytes(b"jpeg")
    return True


class ExtractionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temporary_directory.name)
        self.video = self.output_dir / "source.mp4"
        self.manifest = extract_frames.Manifest(self.output_dir / "manifest.csv")

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def extract(
        self,
        frames: list[np.ndarray],
        *,
        fps: float = 1.0,
        config: object | None = None,
    ):
        capture = FakeCapture(frames, fps=fps)
        selected_config = config or extract_frames.ExtractionConfig()
        with (
            patch.object(extract_frames.cv2, "VideoCapture", return_value=capture),
            patch.object(extract_frames.cv2, "imwrite", side_effect=write_fake_jpeg),
        ):
            result = extract_frames.extract_video(
                self.video, self.output_dir, selected_config, self.manifest
            )
        self.assertTrue(capture.released)
        return result

    def test_first_frame_is_always_selected(self) -> None:
        result = self.extract([black_frame(), black_frame()])

        self.assertEqual(result.selected, 1)
        self.assertEqual(result.rejected, 1)
        self.assertTrue((self.output_dir / "source__f00000000__t0000000000.jpg").exists())

    def test_candidate_is_compared_with_last_selected_frame(self) -> None:
        result = self.extract(
            [black_frame(), frame_with_changed_rows(3), frame_with_changed_rows(6)]
        )

        self.assertEqual(result.selected, 2)
        self.assertEqual(result.rejected, 1)
        self.assertTrue((self.output_dir / "source__f00000002__t0000002000.jpg").exists())

    def test_minimum_interval_uses_video_fps(self) -> None:
        result = self.extract(
            [black_frame(), frame_with_changed_rows(100), frame_with_changed_rows(100)],
            fps=2.0,
        )

        self.assertEqual(result.selected, 2)
        self.assertTrue((self.output_dir / "source__f00000002__t0000001000.jpg").exists())
        self.assertFalse((self.output_dir / "source__f00000001__t0000000500.jpg").exists())

    def test_maximum_frames_is_respected(self) -> None:
        config = extract_frames.ExtractionConfig(max_frames=2)
        result = self.extract(
            [black_frame(), frame_with_changed_rows(100), black_frame()], config=config
        )

        self.assertEqual(result.selected, 2)

    def test_rerun_reuses_files_and_does_not_duplicate_manifest(self) -> None:
        frames = [black_frame(), frame_with_changed_rows(100)]
        first = self.extract(frames)
        self.manifest = extract_frames.Manifest(self.output_dir / "manifest.csv")
        second = self.extract(frames)

        self.assertEqual(first.written, 2)
        self.assertEqual(second.written, 0)
        self.assertEqual(second.reused, 2)
        with (self.output_dir / "manifest.csv").open(newline="", encoding="utf-8") as file:
            self.assertEqual(len(list(csv.DictReader(file))), 2)

    def test_unreadable_video_raises_clear_error_and_releases_capture(self) -> None:
        capture = FakeCapture([], opened=False)
        with patch.object(extract_frames.cv2, "VideoCapture", return_value=capture):
            with self.assertRaisesRegex(extract_frames.ExtractionError, "não pôde ser aberto"):
                extract_frames.extract_video(
                    self.video,
                    self.output_dir,
                    extract_frames.ExtractionConfig(),
                    self.manifest,
                )
        self.assertTrue(capture.released)

    def test_argument_validation_rejects_invalid_values(self) -> None:
        parser = extract_frames.build_parser()
        invalid_arguments = (
            ["--problem", "../epi", "--batch", "batch_001"],
            ["--problem", "epi", "--batch", "batch_001", "--min-interval", "0"],
            ["--problem", "epi", "--batch", "batch_001", "--changed-ratio", "1.1"],
            ["--problem", "epi", "--batch", "batch_001", "--pixel-threshold", "256"],
            ["--problem", "epi", "--batch", "batch_001", "--max-frames", "0"],
        )
        for arguments in invalid_arguments:
            with (
                self.subTest(arguments=arguments),
                self.assertRaises(SystemExit),
                patch("sys.stderr", new=io.StringIO()),
            ):
                parser.parse_args(arguments)


if __name__ == "__main__":
    unittest.main()
