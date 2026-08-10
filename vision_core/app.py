from vision_core.module_manager import ModuleManager
from vision_core.controls import KeyboardControls
import cv2

class VisionApp:
    def __init__(
        self,
        source,
        module_manager: ModuleManager,
        controls: KeyboardControls
    ):
        self.source = source
        self.module_manager = module_manager
        self.controls = controls

    def run(self):
        capture = cv2.VideoCapture(self.source)

        try:
            while capture.isOpened():
                sucess, frame = capture.read()

                if not sucess:
                    break

                frame = self.module_manager.process(frame)

                cv2.imshow("Imagem", frame)

                key_code = cv2.waitKey(1)

                if key_code & 0xFF == 27:
                    break

                result = self.controls.handle(key_code)

                if result is not None:
                    module_id, active = result
                    state = "ativado" if active else "desativado"
                    print(f"{module_id}: {state}")

        finally:
            capture.release()
            cv2.destroyAllWindows()

            self.module_manager.shutdown()