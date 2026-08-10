import cv2
from cvzone.FaceDetectionModule import FaceDetector # cvzone é uma abstração de outras bibliotecas de uso mais facilitado

video = cv2.VideoCapture(0,cv2.CAP_DSHOW) # CAP_DSHOW serve para melhorar acelerar a abertura de camera e evitar bugs em cameras logitech
if not video.isOpened():
    raise RuntimeError("Não foi possivel abrir a câmera.")

detector = FaceDetector(minDetectionCon=0.3)


while True:

    _, img = video.read()
    img, bboxes = detector.findFaces(img, draw=False)
    if bboxes:
        alto, largo, _ = img.shape

        for bbox in bboxes:
            x, y, w, h = bbox['bbox']

            x1 = max(0, x - int(w * 0.15))
            y1 = max(0, y - int(h * 0.25))
            x2 = min(largo, x + w + int(w * 0.15))
            y2 = min(alto, y + h + int(h * 0.15))

            if x2 <= x1 or y2 <= y1:
                continue

            recorte = img[y1:y2, x1:x2]

            largura_rosto = x2 - x1
            altura_rosto = y2 - y1

            tamanho_blur = int(min(largura_rosto, altura_rosto) * 0.35)
            tamanho_blur = max(15, tamanho_blur)

            recorte_blur = cv2.blur(recorte, (tamanho_blur,tamanho_blur))
            img[y1:y2, x1:x2] = recorte_blur

        texto = f"Rostos: {len(bboxes)}"
        posicao_x = largo
        posicao_y = alto
        cv2.putText(img, "Sistema de Privacidade Ativo", (10,40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,0,0), 2)
        cv2.putText(img, texto, (posicao_x - 150, posicao_y - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)

    cv2.imshow("Imagem", img)
    if cv2.waitKey(1) == 27:
        break

video.release()
cv2.destroyAllWindows()