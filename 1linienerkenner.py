import cv2
import numpy as np

cap = cv2.VideoCapture(1)   # Kamera 0 als Eingabe

while True:
    ret, frame = cap.read()  # einzelne Bilder lesen
    if not ret:
        print("Fehler beim Lesen des Kamerabilds.")
        break

    height, width = frame.shape[:2]

    # Nur die untersten 150 Pixel und die 80 mittleren Spalten
    unten = frame[height-150:,round(width/2)-40:round(width/2)+40,:]

    unten_gray = cv2.cvtColor(unten, cv2.COLOR_BGR2GRAY) # in Graustufen wandeln
    _, unten_bin = cv2.threshold(unten_gray,127,255,cv2.THRESH_BINARY) # In Binärbild wandeln

    cv2.imshow('Webcam', unten_bin)
    if cv2.waitKey(1) & 0xFF == ord('q'):  # q drücken, um Fenster zu schließen
        break

cap.release()
cv2.destroyAllWindows()


