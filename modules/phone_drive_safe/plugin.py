from ultralytics import YOLO
from pathlib import Path
from vision_core.module import VideoModule
import cv2
import threading
import winsound

class PhoneDriveSafeModule(VideoModule):
    id = "phone_drive_safe"
    name = "Detecção de uso de celular"

    def __init__(self):
        self.model = None
        self._alarm_thread = None

    def start(self) -> None:
        model_path = Path(__file__).resolve().parent / "models" / "yolov8x.pt"
        self.model = YOLO(model_path)

    def _play_alarm(self) -> None:
        winsound.Beep(2500, 500)

    def _trigger_alarm(self) -> None:
        if (
            self._alarm_thread is not None
            and self._alarm_thread.is_alive()
        ):
            return

        self._alarm_thread = threading.Thread(
            target=self._play_alarm,
            daemon=True
        )
        self._alarm_thread.start()

    def process(self, frame):
        results = self.model.predict(
            frame,
            classes=[67],
            conf=0.5,
            verbose=False
        )

        for box in results[0].boxes:
            coordinates = box.xyxy[0].cpu().tolist()
            x1, y1, x2, y2 = map(int, coordinates)
            confidence = float(box.conf[0])

            cv2.rectangle(frame, (x1,y1), (x2,y2), (255,0,255), 3)

            cv2.putText(
                frame,
                f"Celular {confidence:.2f}",
                (x1, max(25, y1 - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0,0,255),
                2
            )

            if len(results[0].boxes) > 0:
                self._trigger_alarm()

        return frame

    def stop(self) -> None:
        if self._alarm_thread is not None:
            self._alarm_thread.join(timeout=1.0)
            self._alarm_thread = None

        self.model = None

def create_module() -> VideoModule:
    return PhoneDriveSafeModule()
    