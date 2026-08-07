import cv2
from ultralytics import YOLO

video = cv2.VideoCapture('conteudo_teste/video1.mp4')
modelo = YOLO('best.pt')

while True:
    check, img = img.read()
    cv2.resize(img, (1280,720))
    resultado = modelo.predict(img,conf=0.5,verbose=False)


    cv2.imshow("Imagem", img)
    if cv2.waitKey(1) == 27:
        break