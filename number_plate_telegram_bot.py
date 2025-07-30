import cv2
import pytesseract
import requests
import re
import pywhatkit
import datetime
import threading
import pyttsx3

def speak_alert(plate_number, owner, toll):
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)  # speaking speed
    engine.setProperty('volume', 1.0)  # max volume

    message = f"Vehicle number {plate_number} detected. Owner {owner}. Toll amount is {toll} rupees."
    engine.say(message)
    engine.runAndWait()

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Telegram credentials
BOT_TOKEN = "8103267385:AAHi2GGTtr9xcjGoKZUAG8PTCSNaU5GNH1c"
CHAT_ID = "1480542291"

# Vehicle Database
vehicles = {
    "TN10AB1234": {"owner": "Madhavan R", "phone": "+918838573214", "toll": 75},
    "TN22CD5678": {"owner": "Sekar R", "phone": "+918939548244", "toll": 90},
    "AP01EF4321": {"owner": "Sathish Kumar", "phone": "+918300202494", "toll": 60},
    "KA05GH8765": {"owner": "Uday Bhaskar", "phone": "+918870211154", "toll": 100},
    "MH12JK3456": {"owner": "Naveen S", "phone": "+918610337432", "toll": 50},
    "TS09LM7890": {"owner": "Moniesh Kumar", "phone": "+919150579789", "toll": 80},
    "GJ01MN1122": {"owner": "Ajay Shrikaanth", "phone": "+919498089804", "toll": 70},
    "RJ14OP3344": {"owner": "Devanadhan A", "phone": "+918939087832", "toll": 85},
    "DL03QR5566": {"owner": "Kalai", "phone": "+917530057592", "toll": 95},
    "PB10ST7788": {"owner": "Raman M", "phone": "+919962861561", "toll": 65},
}

# Telegram message

def send_telegram_message(message):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": message})
        print("\U0001F4E9 Telegram message sent.")
    except Exception as e:
        print("\u274C Telegram error:", e)

# WhatsApp message

def send_whatsapp_message(phone, message):
    try:
        print(f"\U0001F4F1 Sending WhatsApp message instantly to {phone}")
        pywhatkit.sendwhatmsg_instantly(phone, message, wait_time=20, tab_close=True)
        print("✅ WhatsApp message sent.")
    except Exception as e:
        print("\u274C WhatsApp error:", e)

# Alert function (runs in background)

def send_alerts(plate_number, info):
    message = (
        f"✅ Vehicle Detected!\n"
        f"Number Plate: {plate_number}\n"
        f"Owner       : {info['owner']}\n"
        f"Phone       : {info['phone']}\n"
        f"Toll Amount : ₹{info['toll']}"
    )
    print("\n" + message)
    send_telegram_message(f"\U0001F698 Toll Alert\n{message}")
    send_whatsapp_message(info["phone"], message)

# Clean and extract plate number

def clean_text(text):
    match = re.search(r"[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}", text.upper())
    return match.group() if match else None

# Initialize
cap = cv2.VideoCapture(0)
detected_once = set()
print("\U0001F6A6 Smart Toll System Running (ESC to stop)")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.bilateralFilter(gray, 11, 17, 17)
    edged = cv2.Canny(blur, 30, 200)

    contours, _ = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

    for contour in contours:
        approx = cv2.approxPolyDP(contour, 10, True)
        if len(approx) == 4:
            x, y, w, h = cv2.boundingRect(contour)
            number_plate_img = gray[y:y + h, x:x + w]
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            plate_resized = cv2.resize(number_plate_img, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)
            _, plate_thresh = cv2.threshold(plate_resized, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
            text = pytesseract.image_to_string(plate_thresh, config=custom_config)

            plate_number = clean_text(text)
            if plate_number and plate_number in vehicles and plate_number not in detected_once:
                info = vehicles[plate_number]

                # Speak the number plate and details
                threading.Thread(target=speak_alert, args=(plate_number, info["owner"], info["toll"])).start()

                # Send Telegram & WhatsApp alerts
                threading.Thread(target=send_alerts, args=(plate_number, info)).start()

                detected_once.add(plate_number)
                cv2.waitKey(1000)

            break

    cv2.imshow("\U0001F698 Smart Number Plate Scanner", frame)
    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()