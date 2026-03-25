import cv2
import numpy as np

cap = cv2.VideoCapture(1)   # Kamera index als Eingabe

while True:
    ret, frame = cap.read()  # einzelne Bilder lesen
    if not ret:
        print("Fehler beim Lesen des Kamerabilds.")
        break

    height, width = frame.shape[:2]


    # Nur die untersten 150 Pixel und die 80 mittleren Spalten
    unten = frame[height-150:, round(width/2)-40:round(width/2)+40, :]
    unten_gray = cv2.cvtColor(unten, cv2.COLOR_BGR2GRAY)
    _, unten_bin = cv2.threshold(unten_gray, 127, 255, cv2.THRESH_BINARY)

    # Erkennung nur in Zeile 50 (Index 49 im Ausschnitt)
    row_idx = 49
    col_idx = None
    if row_idx < unten_bin.shape[0]:
        black_cols = np.where(unten_bin[row_idx] == 0)[0]
        if black_cols.size > 0:
            col_idx = int(np.mean(black_cols))
            cv2.circle(unten_bin, (col_idx, row_idx), 5, 255, -1)

    # Linie und Winkel von der Mitte des unteren Bildrandes (im Originalbild) aus bestimmen
    if col_idx is not None:
        # Berechne die Koordinaten im Originalbild
        x_mitte_unten = width // 2
        y_unten = height - 1
        # Koordinate des erkannten Punktes im Originalbild
        x_erkannt = (width // 2 - 40) + col_idx
        y_erkannt = height - 150 + row_idx
        # Linie zeichnen
        cv2.line(frame, (x_mitte_unten, y_unten), (x_erkannt, y_erkannt), (0, 255, 0), 2)
        # Winkel berechnen (0° = senkrecht nach oben)
        dx = x_erkannt - x_mitte_unten
        dy = y_unten - y_erkannt
        angle_rad = np.arctan2(dx, dy)
        angle_deg = np.degrees(angle_rad)
        print(f"Winkel: {angle_deg:.2f}°")
        
    cv2.imshow('Webcam', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):  # q drücken, um Fenster zu schließen
        break

cap.release()
cv2.destroyAllWindows()