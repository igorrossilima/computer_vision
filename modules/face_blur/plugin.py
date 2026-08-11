from cvzone.FaceDetectionModule import FaceDetector
from vision_core.module import VideoModule
import cv2

class FaceBlurModule(VideoModule):
    id = "face_blur"
    name = "Desfoque de rostos"

    def start(self) -> None:
        self.detector = FaceDetector(minDetectionCon=0.3)

    def process(self, frame):
        
        frame, bboxes = self.detector.findFaces(frame, draw=False)
        if bboxes:
            alto, largo, _ = frame.shape

            for bbox in bboxes:
                x,y,w,h = bbox['bbox']

                x1 = max(0, x - int(w*0.15))
                y1 = max(0, y - int(h*0.25))
                x2 = min(largo, x + w + int(w*0.15))
                y2 = min(alto, y + h + int(h*0.15))

                if x2 <= x1 or y2 <= y1:
                    continue

                recorte = frame[y1:y2, x1:x2]

                largura_rosto = x2 - x1
                altura_rosto = y2 - y1

                tamanho_blur = int(min(largura_rosto, altura_rosto) * 0.35)
                tamanho_blur = max(15, tamanho_blur)

                recorte_blur = cv2.blur(recorte, (tamanho_blur, tamanho_blur))
                frame[y1:y2, x1:x2] = recorte_blur


        return frame

def create_module() -> VideoModule:
    return FaceBlurModule()