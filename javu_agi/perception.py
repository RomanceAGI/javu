import cv2, speech_recognition as sr
from javu_agi.utils.logger import log_user

def capture_audio(user_id="user-001"):
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("[LISTENING]...")
        audio = r.listen(source)
        try:
            text = r.recognize_google(audio)
        except sr.UnknownValueError:
            log_user(user_id, "[AUDIO] Tidak bisa dikenali.")
            return "[UNRECOGNIZED]"
        except sr.RequestError:
            log_user(user_id, "[AUDIO] Google Speech API error.")
            return "[API ERROR]"
        except Exception:
            log_user(user_id, "[AUDIO] Error transcribing.")
            return ""
        else:
            log_user(user_id, f"[AUDIO] {text}")
            return text

def capture_image(user_id="user-001"):
    cam = cv2.VideoCapture(0)
    ret, frame = cam.read()
    if ret:
        cv2.imwrite("capture.jpg", frame)
        log_user(user_id, "[VISION] Image captured.")
    cam.release()
