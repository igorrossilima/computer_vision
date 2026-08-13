"""Extract diverse frames from the raw videos of a training batch."""

from __future__ import annotations

import argparse
import csv
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import cv2
import numpy as np


SUPPORTED_VIDEO_EXTENSIONS = {".avi", ".mkv", ".mov", ".mp4"}
ANALYSIS_SIZE = (320, 180)
JPEG_QUALITY = 95
MANIFEST_FIELDS = (
    "image",
    "source_video",
    "frame_index",
    "timestamp_ms",
    "difference_ratio",
    "selection_reason",
)


class ExtractionError(RuntimeError):
    """Raised when a video or extraction input cannot be processed."""


@dataclass(frozen=True)
class ExtractionConfig:
    min_interval: float = 1.0
    changed_ratio: float = 0.05
    pixel_threshold: int = 25
    max_frames: int = 10


@dataclass
class VideoResult:
    selected: int = 0
    written: int = 0
    reused: int = 0
    rejected: int = 0


@dataclass
class RunSummary:
    videos_found: int = 0
    videos_processed: int = 0
    images_selected: int = 0
    images_written: int = 0
    images_reused: int = 0
    candidates_rejected: int = 0
    errors: int = 0

    def add(self, result: VideoResult) -> None:
        self.videos_processed += 1
        self.images_selected += result.selected
        self.images_written += result.written
        self.images_reused += result.reused
        self.candidates_rejected += result.rejected


class Manifest:
    """Append frame traceability while avoiding duplicate image rows."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._registered_images = self._load_registered_images()

    def _load_registered_images(self) -> set[str]:
        if not self.path.exists():
            return set()

        try:
            with self.path.open("r", newline="", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                if reader.fieldnames is None:
                    return set()
                if tuple(reader.fieldnames) != MANIFEST_FIELDS:
                    expected = ", ".join(MANIFEST_FIELDS)
                    raise ExtractionError(
                        f"Manifest existente possui colunas incompatíveis. Esperado: {expected}"
                    )
                return {row["image"] for row in reader if row.get("image")}
        except OSError as exc:
            raise ExtractionError(f"Não foi possível ler o manifest: {exc}") from exc

    def register(
        self,
        *,
        image: str,
        source_video: str,
        frame_index: int,
        timestamp_ms: int,
        difference_ratio: float | None,
        selection_reason: str,
    ) -> bool:
        if image in self._registered_images:
            return False

        write_header = not self.path.exists() or self.path.stat().st_size == 0
        row = {
            "image": image,
            "source_video": source_video,
            "frame_index": frame_index,
            "timestamp_ms": timestamp_ms,
            "difference_ratio": (
                "" if difference_ratio is None else f"{difference_ratio:.6f}"
            ),
            "selection_reason": selection_reason,
        }

        try:
            with self.path.open("a", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=MANIFEST_FIELDS)
                if write_header:
                    writer.writeheader()
                writer.writerow(row)
        except OSError as exc:
            raise ExtractionError(f"Não foi possível atualizar o manifest: {exc}") from exc

        self._registered_images.add(image)
        return True


def prepare_for_comparison(frame: np.ndarray) -> np.ndarray:
    """Create a small grayscale copy used only by the difference metric."""
    resized = cv2.resize(frame, ANALYSIS_SIZE, interpolation=cv2.INTER_AREA)
    return cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)


def calculate_changed_ratio(
    reference: np.ndarray, candidate: np.ndarray, pixel_threshold: int
) -> float:
    difference = cv2.absdiff(reference, candidate)
    changed_pixels = np.count_nonzero(difference >= pixel_threshold)
    return float(changed_pixels / difference.size)


def build_image_name(video: Path, frame_index: int, timestamp_ms: int) -> str:
    return f"{video.stem}__f{frame_index:08d}__t{timestamp_ms:010d}.jpg"


def save_selected_frame(
    *,
    frame: np.ndarray,
    video: Path,
    output_dir: Path,
    manifest: Manifest,
    frame_index: int,
    timestamp_ms: int,
    difference_ratio: float | None,
    selection_reason: str,
) -> bool:
    image_name = build_image_name(video, frame_index, timestamp_ms)
    image_path = output_dir / image_name
    reused = image_path.exists()

    if not reused:
        written = cv2.imwrite(
            str(image_path), frame, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]
        )
        if not written:
            raise ExtractionError(f"Não foi possível salvar a imagem {image_name}")

    manifest.register(
        image=image_name,
        source_video=video.name,
        frame_index=frame_index,
        timestamp_ms=timestamp_ms,
        difference_ratio=difference_ratio,
        selection_reason=selection_reason,
    )
    return reused


def extract_video(
    video: Path,
    output_dir: Path,
    config: ExtractionConfig,
    manifest: Manifest,
) -> VideoResult:
    capture = cv2.VideoCapture(str(video))
    if not capture.isOpened():
        capture.release()
        raise ExtractionError("vídeo não pôde ser aberto")

    try:
        fps = float(capture.get(cv2.CAP_PROP_FPS))
        if not math.isfinite(fps) or fps <= 0:
            raise ExtractionError("vídeo possui FPS inválido")

        interval_frames = max(1, math.ceil(config.min_interval * fps))
        next_candidate_frame = 0
        frame_index = -1
        last_selected_analysis: np.ndarray | None = None
        result = VideoResult()

        while result.selected < config.max_frames:
            success, frame = capture.read()
            if not success:
                break

            frame_index += 1
            if frame_index < next_candidate_frame:
                continue

            next_candidate_frame += interval_frames
            while next_candidate_frame <= frame_index:
                next_candidate_frame += interval_frames

            analysis_frame = prepare_for_comparison(frame)
            timestamp_ms = round((frame_index / fps) * 1000)

            if last_selected_analysis is None:
                difference_ratio = None
                selection_reason = "first_frame"
                should_select = True
            else:
                difference_ratio = calculate_changed_ratio(
                    last_selected_analysis,
                    analysis_frame,
                    config.pixel_threshold,
                )
                selection_reason = "visual_change"
                should_select = difference_ratio >= config.changed_ratio

            if not should_select:
                result.rejected += 1
                continue

            reused = save_selected_frame(
                frame=frame,
                video=video,
                output_dir=output_dir,
                manifest=manifest,
                frame_index=frame_index,
                timestamp_ms=timestamp_ms,
                difference_ratio=difference_ratio,
                selection_reason=selection_reason,
            )
            result.selected += 1
            if reused:
                result.reused += 1
            else:
                result.written += 1
            last_selected_analysis = analysis_frame

        if frame_index < 0:
            raise ExtractionError("vídeo não contém frames legíveis")

        return result
    finally:
        capture.release()


def validate_component(value: str, label: str) -> str:
    if not value or value in {".", ".."} or Path(value).name != value:
        raise argparse.ArgumentTypeError(
            f"{label} deve ser apenas o nome do diretório, sem separadores de caminho"
        )
    return value


def positive_float(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("o valor deve ser numérico") from exc
    if not math.isfinite(parsed) or parsed <= 0:
        raise argparse.ArgumentTypeError("o valor deve ser maior que zero")
    return parsed


def changed_ratio_value(value: str) -> float:
    parsed = positive_float(value)
    if parsed > 1:
        raise argparse.ArgumentTypeError("o valor deve estar no intervalo (0, 1]")
    return parsed


def pixel_threshold_value(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("o valor deve ser um número inteiro") from exc
    if not 1 <= parsed <= 255:
        raise argparse.ArgumentTypeError("o valor deve estar entre 1 e 255")
    return parsed


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("o valor deve ser um número inteiro") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("o valor deve ser maior que zero")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extrai frames visualmente diversos dos vídeos brutos de um batch."
    )
    parser.add_argument(
        "--problem",
        required=True,
        type=lambda value: validate_component(value, "problem"),
        help="Problema em training/data, por exemplo: epi_detection.",
    )
    parser.add_argument(
        "--batch",
        required=True,
        type=lambda value: validate_component(value, "batch"),
        help="Batch dentro de raw, por exemplo: batch_001.",
    )
    parser.add_argument("--min-interval", type=positive_float, default=1.0)
    parser.add_argument("--changed-ratio", type=changed_ratio_value, default=0.05)
    parser.add_argument("--pixel-threshold", type=pixel_threshold_value, default=25)
    parser.add_argument("--max-frames", type=positive_int, default=10)
    return parser


def find_videos(input_dir: Path) -> list[Path]:
    return sorted(
        (
            path
            for path in input_dir.iterdir()
            if path.is_file() and path.suffix.lower() in SUPPORTED_VIDEO_EXTENSIONS
        ),
        key=lambda path: path.name.casefold(),
    )


def print_summary(summary: RunSummary, output_dir: Path) -> None:
    print("\nResumo da extração")
    print(f"  Vídeos encontrados: {summary.videos_found}")
    print(f"  Vídeos processados: {summary.videos_processed}")
    print(f"  Imagens selecionadas: {summary.images_selected}")
    print(f"  Imagens novas: {summary.images_written}")
    print(f"  Imagens reaproveitadas: {summary.images_reused}")
    print(f"  Candidatos semelhantes descartados: {summary.candidates_rejected}")
    print(f"  Erros: {summary.errors}")
    print(f"  Saída: {output_dir}")


def run(args: argparse.Namespace) -> int:
    project_root = Path(__file__).resolve().parents[2]
    data_root = project_root / "training" / "data"
    input_dir = data_root / args.problem / "raw" / args.batch / "videos"
    output_dir = data_root / args.problem / "extracted" / args.batch

    if not input_dir.is_dir():
        raise ExtractionError(f"Diretório de vídeos não encontrado: {input_dir}")

    videos = find_videos(input_dir)
    if not videos:
        extensions = ", ".join(sorted(SUPPORTED_VIDEO_EXTENSIONS))
        raise ExtractionError(
            f"Nenhum vídeo suportado encontrado. Extensões aceitas: {extensions}"
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = Manifest(output_dir / "manifest.csv")
    config = ExtractionConfig(
        min_interval=args.min_interval,
        changed_ratio=args.changed_ratio,
        pixel_threshold=args.pixel_threshold,
        max_frames=args.max_frames,
    )
    summary = RunSummary(videos_found=len(videos))

    for video in videos:
        try:
            summary.add(extract_video(video, output_dir, config, manifest))
        except (ExtractionError, cv2.error) as exc:
            summary.errors += 1
            print(f"Aviso: falha ao processar {video.name}: {exc}", file=sys.stderr)

    print_summary(summary, output_dir)
    return 1 if summary.errors else 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return run(args)
    except ExtractionError as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
