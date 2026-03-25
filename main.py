from flask import Flask, Response, render_template_string
import cv2
import time
import numpy as np
import socket
from arduino.app_utils import *

# --- Erweiterte Linienerkennung mit Parabelanpassung und Motorsteuerung ---
def erkenne_linienpunkte(frame, zeilen=[49, 99]):
    height, width = frame.shape[:2]
    unten = frame[height-150:, :, :]
    unten_gray = cv2.cvtColor(unten, cv2.COLOR_BGR2GRAY)
    # Adaptive Schwellenwertbestimmung (Otsu)
    _, unten_bin = cv2.threshold(unten_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # Morphologisches Schließen, um Lücken zu schließen
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
    unten_bin = cv2.morphologyEx(unten_bin, cv2.MORPH_CLOSE, kernel)
    punkte = []
    for row_idx in zeilen:
        if row_idx < unten_bin.shape[0]:
            row = unten_bin[row_idx]
            # Finde zusammenhängende schwarze Bereiche (0)
            in_region = False
            regions = []
            start = 0
            for i, val in enumerate(row):
                if val == 0 and not in_region:
                    in_region = True
                    start = i
                elif val != 0 and in_region:
                    in_region = False
                    regions.append((start, i-1))
            if in_region:
                regions.append((start, len(row)-1))
            # Wähle größten Bereich
            if regions:
                largest = max(regions, key=lambda r: r[1]-r[0])
                col_idx = (largest[0] + largest[1]) // 2
                cv2.circle(unten_bin, (col_idx, row_idx), 5, 255, -1)
                y_erkannt = height - 150 + row_idx
                punkte.append((col_idx, y_erkannt))
            else:
                punkte.append((None, None))
        else:
            punkte.append((None, None))
    # Unterer Bildmittelpunkt als dritter Punkt
    x_mitte_unten = width // 2
    y_unten = height - 1
    punkte.append((x_mitte_unten, y_unten))
    return punkte, unten_bin

app = Flask(__name__)

# HTML-Template für die Webseite
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Webcam Livestream</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            margin: 0;
            background-color: #1a1a2e;
            color: white;
        }
        h1 {
            margin-bottom: 20px;
        }
        img {
            border: 3px solid #4a4a6a;
            border-radius: 10px;
            max-width: 90%;
        }
    </style>
</head>
<body>
    <h1>🎥 Webcam Livestream</h1>
    <img src="{{ url_for('video_feed') }}" alt="Webcam Stream">
</body>
</html>
"""




def find_camera_index(max_index=10):
    """Sucht den ersten verfügbaren Kamera-Index sehr schnell."""
    for idx in range(max_index):
        cap = cv2.VideoCapture(idx)
        if cap.isOpened():
            cap.release()
            return idx
        cap.release()
    return None

# Automatische Kameraerkennung (schnelle Suche)
camera_index = find_camera_index()
if camera_index is None:
    raise RuntimeError("Keine Kamera gefunden!")
camera = cv2.VideoCapture(camera_index)

def generate_frames():
    """Generator-Funktion für Video-Frames mit Linienverfolgung und Motorsteuerung"""
    # Kamera-Einstellungen für bessere Performance
    camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    camera.set(cv2.CAP_PROP_FPS, 30)
    camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    actual_width = camera.get(cv2.CAP_PROP_FRAME_WIDTH)
    actual_height = camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
    actual_fps = camera.get(cv2.CAP_PROP_FPS)
    print(f"Kamera: {actual_width}x{actual_height} @ {actual_fps} FPS")

    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 60]
    prev_time = time.time()
    fps = 0
    fps_smooth = 0

    # --- Automatische Kalibrierung zu Beginn ---
    # (Hier Dummy: Drehung für 2 Sekunden, kann angepasst werden)
    print("Starte Kalibrierung: Drehe für 2 Sekunden...")
    Bridge.call("set_motor", 1, 0, 1,100)  # Links drehen
    time.sleep(2)
    Bridge.call("set_motor", 1, 100, 1, 0)   # Rechts drehen
    time.sleep(2)
    Bridge.call("set_motor", 1, 100, 1, 100)   # Geradeaus
    print("Kalibrierung abgeschlossen.")

    try:
        while True:
            success, frame = camera.read()
            if not success:
                break

            # FPS berechnen
            current_time = time.time()
            time_diff = current_time - prev_time
            if time_diff > 0:
                fps = 1 / time_diff
                fps_smooth = 0.9 * fps_smooth + 0.1 * fps
            prev_time = current_time

            fps_text = f"FPS: {round(fps_smooth)}"
            cv2.rectangle(frame, (5, 5), (200, 70), (0, 0, 0), -1)
            cv2.putText(frame, fps_text, (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # --- Linienpunkte finden ---
            punkte, _ = erkenne_linienpunkte(frame, zeilen=[49, 99])
            # Visualisierung der Mittelpunkte
            farben = [(0, 0, 255), (0, 255, 255), (255, 0, 0)]  # rot, gelb, blau
            for i, p in enumerate(punkte):
                if p[0] is not None and p[1] is not None:
                    cv2.circle(frame, (int(p[0]), int(p[1])), 8, farben[i % len(farben)], -1)

            # punkte: [(x1, y1), (x2, y2), (x3, y3)]
            # x3, y3 ist der Bildmittelpunkt unten
            xs = []
            ys = []
            for p in punkte:
                if p[0] is not None:
                    xs.append(p[0])
                    ys.append(p[1])

            if len(xs) == 3:
                # Parabel fitten: y = a*x^2 + b*x + c, wir wollen aber x = f(y)
                coeffs = np.polyfit(ys, xs, 2)  # x = a*y^2 + b*y + c
                # Ableitung am unteren Bildrand (y = max(ys))
                y_eval = max(ys)
                dx_dy = 2*coeffs[0]*y_eval + coeffs[1]
                # Steuerwert: negativ = links, positiv = rechts
                steuerwert = dx_dy
                # Motorsteuerung (Differentialantrieb, Beispielwerte)
                basis = 220  # möglichst schnell, aber noch Regelreserve
                k = 1.5  # stärkere Lenkung für hohe Geschwindigkeit
                left = int(basis - k*steuerwert)
                right = int(basis + k*steuerwert)
                # Richtung bestimmen: 0 = vorwärts, 1 = rückwärts
                left_dir = 0 if left >= 0 else 1
                right_dir = 0 if right >= 0 else 1
                left = abs(left)
                right = abs(right)
                left = max(min(left, 255), 0)
                right = max(min(right, 255), 0)
                Bridge.call("set_motor", left_dir, left, right_dir, right)
                # Visualisierung
                cv2.putText(frame, f"Steuerwert: {steuerwert:.2f}", (10, 65), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
                # Parabel zeichnen
                for y_draw in range(frame.shape[0]-150, frame.shape[0]):
                    x_draw = int(coeffs[0]*y_draw**2 + coeffs[1]*y_draw + coeffs[2])
                    if 0 <= x_draw < frame.shape[1]:
                        frame[y_draw, x_draw] = (0, 0, 255)
            else:
                # Fallback: nur unterer Punkt
                if punkte[0][0] is not None:
                    abweichung = punkte[0][0] - (frame.shape[1]//2)
                    k = 1.5
                    basis = 220
                    left = int(basis - k*abweichung)
                    right = int(basis + k*abweichung)
                    left_dir = 0 if left >= 0 else 1
                    right_dir = 0 if right >= 0 else 1
                    left = abs(left)
                    right = abs(right)
                    left = max(min(left, 255), 0)
                    right = max(min(right, 255), 0)
                    Bridge.call("set_motor", left_dir, left, right_dir, right)

            # Frame als JPEG kodieren
            ret, buffer = cv2.imencode('.jpg', frame, encode_param)
            if not ret:
                continue
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
    finally:
        camera.release()


@app.route('/')
def index():
    """Hauptseite mit dem Video-Stream"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/video_feed')
def video_feed():
    """Route für den Video-Stream"""
    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )



if __name__ == '__main__':
    # Gerätenamen automatisch ermitteln
    print("Starte Webcam-Server...")
    print("=" * 50)
    print(f"🌐 Öffne im Browser:")
    print(f"   [hier Gerätename einfügen].local")
    print("=" * 50)
    app.run(host='0.0.0.0', port=80, debug=False, threaded=True)