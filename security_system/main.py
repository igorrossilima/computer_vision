import cv2
from ultralytics import YOLO
import winsound
import threading

video = cv2.VideoCapture("conteudo_teste/ex01.mp4")
modelo = YOLO("yolov8n.pt")

area = [510, 230, 930, 700 ]
#area = [100, 190, 1150, 700 ]

alarme_controle = False
def alarme():
    global alarme_controle
    for _ in range(7):
        winsound.Beep(2500, 500)
        alarme_controle = False

while True:
    check, img = video.read()
    img = cv2.resize(img, (1270, 720))
    detection = img.copy()
    cv2.rectangle(detection, (area[0], area[1]), (area[2], area[3]), (0,255,0), -1 )
    resultado = modelo(img)
    for objeto in resultado:
        obj = objeto.boxes
        for dados in obj:
            x,y,w,h = dados.xyxy[0]
            x,y,w,h = int(x), int(y), int(w), int(h)
            cls = int(dados.cls[0]) # index que representa a classe person
            cx, cy = (x+w)//2, (y+h)//2
            if cls == 0:
                cv2.rectangle(img, (x,y), (w,h), (255,0,0), 3)

                if cx >= area[0] and cx <= area[2] and cy >= area[1] and cy <= area[3]:
                    cv2.rectangle(detection, (area[0], area[1]), (area[2], area[3]), (0,0,255), -1 )
                    cv2.rectangle(img, (100,30), (470,80), (0,0,255), -1)
                    cv2.putText(img,"Invasor Detectado", (105,65), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 3)
                    if not alarme_controle:
                        alarme_controle = True
                        threading.Thread(target=alarme).start()



    imgFinal = cv2.addWeighted(detection,0.5,img,0.5,0)
    cv2.imshow('img', imgFinal)
    if cv2.waitKey(5) == 27:
        break

    