import cv2
from ultralytics import YOLO
import cvzone
import winsound
import threading

video = cv2.VideoCapture(0)
video.set(3, 1280)
video.set(4, 720)
modelo = YOLO('yolov8x.pt')

controleAlarme = False


def alarme():
    global controleAlarme
    for _ in range(5):
        winsound.Beep(2500,500)
        threading.Thread()
        controleAlarme = False

while True:
    check, img = video.read()
    img = cv2.resize(img, (1080,720))

    resultado = modelo.predict(img, conf=0.5)

    for objetos in resultado:
        obj = objetos.boxes
        for dados in obj:
            x,y,w,h = dados.xyxy[0]
            x,y,w,h = int(x), int(y), int(w), int(h)
            cls = int(dados.cls[0])
            if cls==67:
                cv2.rectangle(img, (x,y), (w,h), (255,0,255), 5)
                cvzone.putTextRect(img, "Celular identificado", (105,65), colorR=(0,0,255))
                if not controleAlarme:
                    controleAlarme = True
                    threading.Thread(target=alarme).start()

    cv2.imshow("Imagem", img)
    if cv2.waitKey(1) == 27:
        break
    