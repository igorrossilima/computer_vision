from vision_core.module import VideoModule
from pathlib import Path
from ultralytics import YOLO
import cv2


class FireDetectionModule(VideoModule):
    id = "fire_detection"
    name =  "Detecção de incêndio"

    def start(self) -> None:
        model_path = Path(__file__).resolve().parent / "models" / "best.pt"
        self.model = YOLO(model_path)

    def process(self, frame):
        results = self.model.predict(frame, conf=0.50, verbose=False)

        for box in results[0].boxes:
            coordinates = box.xyxy[0].cpu().tolist()
            x1, y1, x2, y2 = map(int, coordinates)
            confidence = float(box.conf[0])

            cv2.rectangle(frame, (x1,y1), (x2,y2), (0,0,255), 3)
            cv2.putText(
                frame,
                f"Fire {confidence:.2f}",
                (x1, max(25, y1 - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0,0,255),
                2
            )

        return frame


    def stop(self) -> None:
        self.model = None


def create_module() -> VideoModule:
    return FireDetectionModule()