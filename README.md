# Fire Detection & Auto-Suppression System

![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python)
![MicroPython](https://img.shields.io/badge/MicroPython-ESP32-orange?style=for-the-badge&logo=espressif)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green?style=for-the-badge&logo=opencv)
![YOLO](https://img.shields.io/badge/AI-YOLOv8-red?style=for-the-badge)

Real-time fire detection using a custom YOLO model streamed from an ESP32-CAM, with automatic servo-aimed water pump suppression controlled via an ESP32 microcontroller.

---

## How It Works

```
┌─────────────┐   MJPEG stream    ┌──────────────────────────┐
│  ESP32-CAM  │ ────────────────▶ │  Camera.py  (PC)         │
│  Wi-Fi      │  :81/stream       │  - YOLO fire detection   │
└─────────────┘                   │  - Servo angle calc      │
                                  │  - Sends FIRE:XX / CLEAR │
                                  └────────────┬─────────────┘
                                               │ Serial (COM3)
                                               ▼
                                  ┌──────────────────────────┐
                                  │  main_local.py  (ESP32)  │
                                  │  - Servo tracks fire     │
                                  │  - Water pump relay ON   │
                                  │  - LED + buzzer alert    │
                                  │  - LCD status display    │
                                  │  - MQ-5 gas sensor       │
                                  └──────────────────────────┘
```

1. ESP32-CAM streams live video over Wi-Fi
2. `Camera.py` on the PC runs YOLO detection on each frame
3. When fire is detected, it calculates servo angle and sends `FIRE:45` via serial
4. ESP32 receives the command, aims servo at fire, turns on water pump
5. When fire is gone (after 1.5s hold), `CLEAR` is sent and pump stops

---

## Project Files

| File | Runs on | Purpose |
|---|---|---|
| `Camera.py` | PC | Stream, detect fire, send serial commands |
| `main_local.py` | ESP32 | Servo, relay/pump, LCD, gas sensor |
| `main.py` | ESP32 | Same as main_local.py + Telegram alert |
| `new.py` | PC | Simple detection test (no serial/servo) |
| `fire.pt` | PC | Custom-trained YOLO fire detection model |
| `servo_test.py` | ESP32 | Servo calibration utility |
| `relay_test.py` | ESP32 | Relay/pump test utility |

---

## Hardware Required

**PC side:**
- Any PC running Python 3.8+

**ESP32-CAM:**
- AI-Thinker ESP32-CAM module
- 5V stable power supply

**ESP32 controller:**
- ESP32 development board
- Servo motor (connected to GPIO 13)
- 2× relay module (GPIO 15, GPIO 16) → water pump
- MQ-5 gas sensor (GPIO 33)
- I2C LCD 16×2 (SDA GPIO 21, SCL GPIO 22)
- Green LED (GPIO 18), Yellow LED (GPIO 2), Red LED (GPIO 23)
- Buzzer (GPIO 4)

**ESP32 Pin Summary:**

| Pin | Component |
|---|---|
| GPIO 13 | Servo PWM |
| GPIO 15 | Relay speed |
| GPIO 16 | Relay pump |
| GPIO 33 | MQ-5 gas sensor |
| GPIO 21 | LCD SDA |
| GPIO 22 | LCD SCL |
| GPIO 18 | Green LED |
| GPIO 2  | Yellow LED |
| GPIO 23 | Red LED |
| GPIO 4  | Buzzer |

---

## Software Setup

### PC — Install Python dependencies

```bash
pip install opencv-python ultralytics pyserial numpy
```

### ESP32 — Flash MicroPython

1. Download MicroPython firmware for ESP32 from micropython.org
2. Flash using Thonny or esptool:
   ```bash
   esptool.py --chip esp32 --port COM3 erase_flash
   esptool.py --chip esp32 --port COM3 write_flash -z 0x1000 firmware.bin
   ```
3. Upload `main_local.py` (rename to `main.py` on device) using Thonny
4. Upload `machine_i2c_lcd.py` library to the ESP32

### ESP32-CAM — Flash camera firmware

1. Open Arduino IDE
2. File → Examples → ESP32 → Camera → CameraWebServer
3. Set your Wi-Fi credentials and `#define CAMERA_MODEL_AI_THINKER`
4. Upload, then open Serial Monitor (115200 baud) to get the IP address

---

## Configuration

### Camera.py (PC)

```python
ESP32_PORT    = "COM3"                         # serial port to ESP32
ESPCAM_STREAM = "http://10.172.23.121:81/stream"  # ESP32-CAM IP

SERVO_CENTER   = 50     # center angle (calibrate with servo_test.py)
SERVO_MIN      = 0      # left limit
SERVO_MAX      = 90     # right limit
CAM_FOV        = 60     # camera field of view in degrees

CONF_THRESHOLD = 0.3    # min confidence to trigger relay
FIRE_HOLD      = 1.5    # seconds pump stays on after fire disappears
SEND_INTERVAL  = 0.3    # seconds between servo update commands

CROSSHAIR_X    = 0      # shift crosshair left(-) / right(+)
CROSSHAIR_Y    = -50    # shift crosshair up(-) / down(+)
```

### main_local.py (ESP32)

```python
GAS_THRESHOLD = 4000    # MQ-5 reading to trigger smoke alert
SERVO_CENTER  = 45      # confirmed center = duty 51
```

---

## Running the System

### Step 1 — Upload to ESP32

Open Thonny, connect ESP32, open `main_local.py`:
- **File → Save as → MicroPython device** → save as `main.py`
- Reset the ESP32 — it will warm up the gas sensor for 10 seconds then print `READY`

### Step 2 — Update ESP32-CAM IP

Find the current IP from Arduino Serial Monitor, then update `Camera.py`:

```python
ESPCAM_STREAM = "http://<YOUR_IP>:81/stream"
```

### Step 3 — Run Camera.py

```bash
python Camera.py
```

The window will open showing the live stream with:
- Green crosshair at center
- Red bounding box around detected fire
- Servo angle displayed on detection
- Status bar at top

**To quit:** press `Q`

---

## System Behavior

| Condition | LEDs | Buzzer | Servo | Pump | LCD |
|---|---|---|---|---|---|
| Normal | Green ON | OFF | Center 45° | OFF | SYSTEM SAFE |
| Gas detected | Yellow ON | Beep | Center 45° | OFF | SMOKE DETECTED |
| Fire detected | Red ON | ON | Tracks fire | ON | FIRE DETECTED |
| Fire cleared | Green ON | OFF | Returns 45° | OFF | SYSTEM SAFE |

---

## Servo Calibration

Upload `servo_test.py` to ESP32 and run in Thonny. It sweeps 0°→45°→90° and prints the duty value. Confirmed calibration:

| Angle | Duty | Position |
|---|---|---|
| 0° | 26 | Full left |
| 45° | 51 | Center |
| 90° | 77 | Full right |

Update `SERVO_CENTER` in both `Camera.py` and `main_local.py` if your center differs.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `ERROR: No frame` | ESP32-CAM offline — check IP in Serial Monitor |
| ESP32 not found | Check `ESP32_PORT` in Camera.py matches Device Manager |
| Relay not triggering | Check if relay module is active LOW — swap `.on()` / `.off()` |
| Pump stuttering | Increase `FIRE_HOLD` in Camera.py |
| LCD shows garbage | Strings > 16 chars — already handled with `.ljust(16)` |
| Servo not centering | Run `servo_test.py` and update `SERVO_CENTER` |
| Fire not detected | Lower `CONF_THRESHOLD` in Camera.py |

---

Built with Python · MicroPython · OpenCV · YOLO · ESP32
