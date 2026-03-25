import cv2
import numpy as np

cap = cv2.VideoCapture(0)   # Kamera 1 als Eingabe

while True:
    ret, frame = cap.read()  # einzelne Bilder lesen
    if not ret:
        print("Fehler beim Lesen des Kamerabilds.")
        break

    # Nur die untersten 150 Pixel
    unten = frame[-150:]

    # Für Anzeige und Zeichnen brauchen wir das Originalbild (unten_rgb)
    unten_rgb = unten.copy()

    unten_gray = cv2.cvtColor(unten, cv2.COLOR_BGR2GRAY) # in Graustufen wandeln
    _, unten_bin = cv2.threshold(unten_gray,127,255,cv2.THRESH_BINARY) # In Binärbild wandeln

    # Mittelpunkt in Zeile 50  (da 0-basiert)
    row_idx1 = 49
    
    if row_idx1 < unten_bin.shape[0]:
        black_cols1 = np.where(unten_bin[row_idx1] == 0)[0]     #schwarzen Bereich finden
        if black_cols1.size > 0:    
            col_idx1 = int(np.mean(black_cols1))                # Mittelpunk bestimmen
            cv2.circle(unten_bin, (col_idx1, row_idx1), 7, 0, -1) # weißen Kreis einzeichnen
            cv2.circle(unten_bin, (col_idx1, row_idx1), 5, 255, -1) # schwarzen Kreis einzeichnen

    cv2.imshow('Webcam', unten_bin)
    if cv2.waitKey(1) & 0xFF == ord('q'):  # q drücken, um Fenster zu schließen
        break

cap.release()
cv2.destroyAllWindows()