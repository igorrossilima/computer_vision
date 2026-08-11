from ultralytics import YOLO
from pathlib import Path
from vision_core.module import VideoModule
import cv2

class SecurityModule(VideoModule):
    id = "security"
    name = "Monitoramento da área"

    def __init__(self, roi=None, confidence: float = 0.4):
        if roi is None:
            roi = (0.0, 0.0, 1.0, 1.0)

        if not isinstance(roi, (list, tuple)) or len(roi) != 4:
                    raise ValueError("A ROI deve possuir quatro valores.")

        x1, y1, x2, y2 = map(float, roi)

        if not(
            0.0 <= x1 < x2 <= 1.0
            and 0.0 <= y1 < y2 <= 1.0
        ):
            raise ValueError(
                "A ROI deve seguir 0 <= x1 < x2 <= 1 "
                "e 0 <= y1 < y2 <= 1."
            )

        confidence = float(confidence)

        if not 0.0 < confidence <= 1.0:
            raise ValueError(
                "A confiança deve estar entre 0 e 1."
            )

        self.roi = (x1, y1, x2, y2)
        self.confidence = confidence
        self.model = None



    def start(self) -> None:
        model_path = Path(__file__).resolve().parent / "models" / "yolov8n.pt"
        self.model = YOLO(model_path)

    def process(self, frame):
        height, width = frame.shape[:2]

        roi_x1 = int(self.roi[0] * width)
        roi_y1 = int(self.roi[1] * height)
        roi_x2 = int(self.roi[2] * width)
        roi_y2 = int(self.roi[3] * height)

        intrusion = False

        results = self.model.predict(
            frame,
            classes=[0],
            conf=self.confidence,
            verbose=False
        )

        for box in results[0].boxes:
            coordinates = box.xyxy[0].cpu().tolist()
            x1, y1, x2, y2 = map(int, coordinates)
            detection_confidence = float(box.conf[0])

            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2

            inside_roi = (
                roi_x1 <= center_x <= roi_x2
                and roi_y1 <= center_y <= roi_y2
            )

            if inside_roi:
                intrusion = True

            person_color = (
                (0, 0, 255)
                if inside_roi
                else (255, 0, 0)
            )

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                person_color,
                2
            )

            cv2.circle(
                frame,
                (center_x, center_y),
                5,
                person_color,
                -1
            )

            cv2.putText(
                frame,
                f"Person {detection_confidence:.2f}",
                (x1, max(25, y1 - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                person_color,
                2
            )

        roi_color = (
            (0, 0, 255)
            if intrusion
            else (0, 255, 0)
        )

        cv2.rectangle(
            frame,
            (roi_x1, roi_y1),
            (roi_x2, roi_y2),
            roi_color,
            2
        )

        if intrusion:
            cv2.putText(
                frame,
                "Invasor detectado",
                (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                3
            )

        return frame


    def stop(self) -> None:
        self.model = None

def create_module(roi=None, confidence: float = 0.4) -> VideoModule:
    return SecurityModule(
         roi=roi,
         confidence=confidence
    )