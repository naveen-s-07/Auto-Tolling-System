import cv2
import pytesseract
import requests
import time
from number_plate_telegram_bot import send_telegram_alert, send_whatsapp_message

# Vehicle database
vehicles = {
    "TN10AB1234": {"owner": "Madhavan R", "phone": "+918838573214", "toll": 75},
    "TN20CD5678": {"owner": "Keerthi V", "phone": "+918754237819", "toll": 100},
    "KA01XY4321": {"owner": "Ravi Kumar", "phone": "+919999123456", "toll": 80},
    "MH12MN3456": {"owner": "Anjali Patil", "phone": "+919812345678", "toll": 60},
    "DL8CAF9988": {"owner": "Arun Mehta", "phone": "+918765432190", "toll": 90},
    "PY05PQ7890": {"owner": "Sneha Das", "phone": "+919001234567", "toll": 70},
    "AP10ZZ9999": {"owner": "Karthik Rao", "phone": "+917896543210", "toll": 95},
    "HR26DK8337": {"owner": "Neha Sharma", "phone": "+918765219999", "toll": 85},
    "GJ01AB2233": {"owner": "Amit Joshi", "phone": "+917878123456", "toll": 50},
    "RJ14CC4444": {"owner": "Pooja Verma", "phone": "+919876123456", "toll": 65},
}

# Setup video capture
cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)
cap.set(cv2.CAP_PROP_FPS, 30)

# Frame skipping and detection cooldown
frame_count = 0
skip_frames = 5
last_detection_time = {}
cooldown = 5  # seconds

# Tesseract config
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
config = r'--oem 3 --psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

print("\U0001F6A6 Smart Toll System Running (ESC to stop)")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1
    if frame_count % skip_frames != 0:
        cv2.imshow("\U0001F698 Smart Toll - Live Detection", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break
        continue

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blur, 50, 200)

    contours, _ = cv2.findContours(edged, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

    for cnt in contours:
        approx = cv2.approxPolyDP(cnt, 0.02 * cv2.arcLength(cnt, True), True)
        if len(approx) == 4:
            x, y, w, h = cv2.boundingRect(cnt)
            roi = gray[y:y+h, x:x+w]
            roi = cv2.resize(roi, (0, 0), fx=2, fy=2)
            roi = cv2.medianBlur(roi, 3)

            text = pytesseract.image_to_string(roi, config=config)
            plate_number = text.strip().replace(" ", "")

            if plate_number in vehicles:
                now = time.time()
                if plate_number not in last_detection_time or (now - last_detection_time[plate_number]) > cooldown:
                    vehicle = vehicles[plate_number]
                    print(f"\n\u2705 Vehicle Detected!\nNumber Plate: {plate_number}")
                    print(f"Owner       : {vehicle['owner']}")
                    print(f"Phone       : {vehicle['phone']}")
                    print(f"Toll Amount : ₹{vehicle['toll']}")

                    data = {
                        "number_plate": plate_number,
                        "owner": vehicle['owner'],
                        "phone": vehicle['phone'],
                        "toll": vehicle['toll']
                    }

                    requests.post("http://localhost:5000/api/log", json=data)
                    print(f"\U0001F4E6 Logged to dashboard.")

                    send_telegram_alert(data)
                    send_whatsapp_message(vehicle['phone'], plate_number, vehicle['toll'])

                    last_detection_time[plate_number] = now

                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 3)
                    cv2.putText(frame, plate_number, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    break

    cv2.imshow("\U0001F698 Smart Toll - Live Detection", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
