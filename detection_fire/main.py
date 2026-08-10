import cv2
from ultralytics import YOLO
import cvzone
import winsound

video = cv2.VideoCapture('conteudo_teste/video1.mp4')
modelo = YOLO('best.pt')

while True:
    check, img = video.read()
    cv2.resize(img, (1280,720))

    resultado = modelo.predict(img,conf=0.5,verbose=False)

    for obj in resultado[0].boxes:
        x1, y1, x2, y2 = obj.xyxy[0]
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        cv2.rectangle(img, (x1,y1), (x2,y2), (255,0,255), 3)
        area = (x2-x1) * (y2-y1)
        prop = area/(1280*720)
        cvzone.putTextRect(img, str(round(prop, 2)), (x1,y1+10), scale=1.2, thickness=2, colorR=(255,0,0))
        if prop >= 0.05:
            cvzone.putTextRect(img, "Alerta Fogo", (50,50), colorR=(0,0,255))
            winsound.Beep(1500,100)

    #print(resultado)


    cv2.imshow("Imagem", img)
    if cv2.waitKey(1) == 27:
        break