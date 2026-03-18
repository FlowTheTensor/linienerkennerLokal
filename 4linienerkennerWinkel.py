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

    # Mittelpunkte in Zeile 50 und 99 (letzte Zeile ist 99, da 0-basiert)
    row_idx1 = 50
    row_idx2 = 99
    col_idx1 = col_idx2 = None
    if row_idx1 < unten_bin.shape[0]:
        black_cols1 = np.where(unten_bin[row_idx1] == 0)[0]
        if black_cols1.size > 0:
            col_idx1 = int(np.mean(black_cols1))
            cv2.circle(unten_rgb, (col_idx1, row_idx1), 5, 255, -1)
    if row_idx2 < unten_bin.shape[0]:
        black_cols2 = np.where(unten_bin[row_idx2] == 0)[0]
        if black_cols2.size > 0:
            col_idx2 = int(np.mean(black_cols2))
            cv2.circle(unten_rgb, (col_idx2, row_idx2), 5, 255, -1)

    # Linie zwischen den Mittelpunkten zeichnen, falls beide gefunden
    if col_idx1 is not None and col_idx2 is not None:
        cv2.line(unten_bin, (col_idx1, row_idx1), (col_idx2, row_idx2), 255, 2)
        # Winkel berechnen (0° = senkrecht nach oben)
        dx = col_idx2 - col_idx1
        dy = row_idx1 - row_idx2  # y-Achse nach unten, daher row_idx1 - row_idx2
        angle_rad = np.arctan2(dy, dx)
        angle_deg = np.degrees(angle_rad)
        print(angle_deg+90)
        
    cv2.imshow('Webcam', unten_bin)
    if cv2.waitKey(1) & 0xFF == ord('q'):  # q drücken, um Fenster zu schließen
        break

cap.release()
cv2.destroyAllWindows()