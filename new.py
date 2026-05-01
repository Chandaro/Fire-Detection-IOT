import cv2
import urllib.request
import numpy as np
import time
from ultralytics import YOLO
import os

model = YOLO(f"{os.path.dirname(os.path.abspath(__file__))}/fire.pt")

url = "http://10.172.23.121:81/stream"

def stream_video(url):
    buf = b""

    while True:
        try:
            with urllib.request.urlopen(url, timeout=10) as stream:
                print("Stream connected!")
                while True:
                    buf += stream.read(4096)   # larger chunk = less stutter
                    a = buf.find(b"\xff\xd8")
                    b = buf.find(b"\xff\xd9")

                    if a != -1 and b != -1:
                        jpg = buf[a:b+2]
                        buf = buf[b+2:]

                        img = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)

                        if img is not None:
                            results = model(img, conf=0.5, device="cpu", verbose=False)

                            for result in results:
                                for box in result.boxes:
                                    x1,y1,x2,y2 = map(int, box.xyxy.tolist()[0])
                                    label = model.names[int(box.cls)]
                                    cv2.rectangle(img,(x1,y1),(x2,y2),(0,0,255),2)
                                    cv2.putText(img,label,(x1,y1-10),
                                                cv2.FONT_HERSHEY_SIMPLEX,0.9,(0,255,0),2)

                            cv2.imshow("Fire Detection", img)

                        if cv2.waitKey(1) & 0xFF == ord("q"):
                            cv2.destroyAllWindows()
                            return

        except urllib.error.HTTPError as e:
            print(f"HTTP Error: {e.code} - {e.reason}")
            time.sleep(1)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    stream_video(url)
