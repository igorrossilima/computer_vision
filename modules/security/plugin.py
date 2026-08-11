from ultralytics import YOLO
from pathlib import Path
from vision_core.module import VideoModule
import cv2

class SecurityModule(VideoModule):
    id = "security"
    name = "Monitoramento da área"

    def start(self) -> None:
        model_path = Path(__file__).resolve().parent / "models" / "yolov8n.pt"
        self.model = YOLO(model_path)

    def process(self, frame):
        results = self.model.predict(
            frame,
            classes=[0],
            conf=0.4,
            verbose=False
        )

        for box in results[0].boxes:
            coordinates = box.xyxy[0].cpu().tolist()
            x1, y1, x2, y2 = map(int, coordinates)
            confidence = float(box.conf[0])

            center_x = (x1+x2) // 2
            center_y = (y1+y2) // 2

            cv2.rectangle(frame, (x1,y1), (x2,y2), (255,0,0), 2)
            cv2.circle(frame, (center_x, center_y), 5, (0,0,255), -1)
            cv2.putText(
                frame,
                f"Person {confidence:.2f}",
                (x1, max(25, y1 - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255,0,0),
                2
            )
        return frame

    def stop(self) -> None:
        self.model = None

def create_module() -> VideoModule:
    return SecurityModule()