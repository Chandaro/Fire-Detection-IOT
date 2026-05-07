# Fire Detection & Auto-Suppression System

An AI-powered real-time fire detection and automatic suppression system using a custom YOLO model streamed from an ESP32-CAM, with automatic servo-aimed water pump suppression controlled via an ESP32 microcontroller.

[Watch the Full System Demo](https://youtu.be/e7iuw9bi_Rg?feature=shared)

[View Presentation Slides](https://canva.link/hh019dn70b67avy)

## Table of Content
- [Project Overview](#project-overview)
- [How It Works](#how-it-works)
- [System Architecture](#system-architecture)
- [Logic & Decision-Making](#logic--decision-making)
- [Project Files](#project-files)
- [Hardware Required](#hardware-required)
- [Breadboard Power System](#breadboard-power-system)
- [External Power System](#external-power-system)
- [ESP32 Pin Mapping](#esp32-pin-mapping)
- [Software Setup](#software-setup)
- [Configuration](#configuration)
- [Running the System](#running-the-system)
- [System Behavior](#system-behavior)
- [Servo Calibration](#servo-calibration)
- [Model Credit](#model-credit)
- [Troubleshooting](#troubleshooting)
- [Challenges](#challenges)
- [Future Improvements](#future-improvements)

## Project Overview 
This project combines:
* Computer Vision (YOLO Fire Detection)
* Embedded Systems (ESP32 + ESP32-CAM)
* Environmental Sensing (MQ-5 Gas Sensor)
* Automatic Fire Suppression

The system continuously monitors for:
* Visible flames using AI-based fire detection
* Flammable gas using the MQ-5 gas sensor

Once fire is confirmed:
* The alarm activates
* The servo rotates toward the fire
* The relay activates the water pump
* Water is sprayed directly at the fire source

The system is designed for environments where small fire incidents may occur, such as:
* Kitchen
* Laboratories
* Workshops
* Small indoor spaces


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

## System Architecture
![](https://github.com/Chandaro/IoT_Group_1_Final_Project/blob/ccad3d29a0f60a1fa3fd3175f410d3b855f633b5/SYSTEM%20ARCHITECTURE%20FLOW.png)
The system follows a three-layer workflow that continuously monitors conditions, applies decision logic, and responds automatically when danger is detected.

## Logic and Decision-Making
![](https://github.com/Chandaro/IoT_Group_1_Final_Project/blob/6a10e9773d0dddd0ab896b59ef6c53e066daee49/LOGIC%20%26%20DECISION.png)
The ESP32 applies the following priority logic every cycle:
1. Fire signal receieved? --> FIRE MODE (Highest Priority)
2. Gas Reading > 3200 --> WARNING MODE
3. Neither --> SAFE MODE

## Project Files

| File | Runs on | Purpose |
|---|---|---|
| `Camera.py` | PC | Stream, detect fire, send serial commands |
| `main_local.py` | ESP32 | Servo, relay/pump, LCD, gas sensor |
| `main.py` | ESP32 | Same as main_local.py + Telegram alert |
| `new.py` | PC | Simple detection test (no serial/servo) |
| `fire.pt` | PC | Pre-trained YOLOv10 fire detection model (see Model Credit)|
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
- Breadboard with shared 5V and GND power rails

**Breadboard Power Rails:**
| Rail | Source | Purpose |
|---|---|---|
| + Rail (Red) | ESP32 5V or 3.3V Pin | Distributes power to all component VCC connections |
| - Rail (Blue) | ESP32 GND Pin | Shared ground connection for all components |

The breadboard acts as a power bus — the ESP32's power and GND pins are wired once to the + and − rails, and every component draws power from those rails. GPIO pins are used only for data/signal, not for power.

**Power System**
- External DC power supply (5V)
- Used to power high-current components such as the DC water pump
- Ensures stable operation without overloading the ESP32 board

The ESP32 controls the power supply to the pump through a relay module, which acts as a safe electronic switch.

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
ESP32_PORT = "COM3"  # serial port to ESP32
ESPCAM_STREAM = "http://10.172.23.121:81/stream"  # ESP32-CAM IP

SERVO_CENTER = 50  # center angle (calibrate with servo_test.py)
SERVO_MIN = 0      # left limit
SERVO_MAX = 90     # right limit
CAM_FOV = 60       # camera field of view in degrees

CONF_THRESHOLD = 0.3   # min confidence to trigger relay
FIRE_HOLD = 1.5        # seconds pump stays on after fire disappears
SEND_INTERVAL = 0.3    # seconds between servo update commands

CROSSHAIR_X = 0     # shift crosshair left(-) / right(+)
CROSSHAIR_Y = -50   # shift crosshair up(-) / down(+)
```

### main_local.py (ESP32)

```python
GAS_THRESHOLD = 3200    # MQ-5 reading to trigger smoke alert
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

## Model Credit
The fire detection model `(fire.pt)` was not trained by us. We directly used the pre-trained YOLOv10 fire detection model provided by the original author. No retraining or fine-tuning was done on our end.

* Source tutorial: [Fire Detection: YOLOv10 Training with ESP32-Cam Integration](https://www.youtube.com/watch?v=twiS8Xrz8JM)
* Original model download: [yolov10-firedetection.zip](https://drive.google.com/file/d/1EoMDVYCry3g7Qh3Ibp3wInizeNn0Uz5A/view)

Full credit for fire.pt goes to the original author. His original code does not include any ESP32 integration. Our contribution was building the entire hardware control layer on top of his model, this includes reading the MJPEG stream from the ESP32-CAM, running inference per frame, calculating servo angle from detection coordinates, and sending `FIRE:<angle> / CLEAR` commands to the ESP32 over serial to control the components.

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

## Challenges

| Challenge | Description |
|---|---|
| **Single-axis tracking only** | The servo only moves left and right (horizontal). The system cannot track fire vertically, if fire appears at the top or bottom of the frame, the nozzle may not aim accurately |
| **Wi-Fi stream latency** | The MJPEG stream over Wi-Fi introduces delay between real-world fire movement and detection response, which can reduce suppression accuracy |
| **Dynamic IP address** | The ESP32-CAM gets a new IP from DHCP on every reboot, requiring the user to manually update `ESPCAM_STREAM` in `Camera.py` each session |
| **MQ-5 sensor warmup** | The gas sensor requires a 10-second warmup on boot before it gives reliable readings — the system is blind to smoke during this window |
| **False positives** | The YOLO model can misdetect bright light sources (sunlight, reflections, lamps) as fire, triggering the pump unnecessarily |
| **PC dependency** | YOLO inference runs on the PC — the system cannot operate standalone without a connected computer running `Camera.py` |
| **Power stability** | Running the pump relay, servo, and ESP32 simultaneously puts high demand on the power supply; unstable power causes resets or erratic behavior |
| **Serial cable required** | Commands are sent from PC to ESP32 over USB serial, which limits deployment distance and adds a physical cable constraint |

---

## Future Improvements

| Improvement | Description |
|---|---|
| **Pan-tilt servo mount (2-axis)** | Add a second servo for vertical movement so the nozzle can track fire anywhere in the frame, not just left and right |
| **Wi-Fi command channel** | Replace the USB serial link with MQTT or UDP over Wi-Fi so the PC and ESP32 communicate wirelessly, no cable needed |
| **Edge inference (no PC)** | Port the YOLO model to run on an ESP32-S3 or Raspberry Pi so the system works fully standalone without a PC |
| **Static IP for ESP32-CAM** | Assign a fixed IP in the Arduino firmware to avoid having to update the stream URL after every reboot |
| **Telegram / mobile alerts** | Extend `main.py` (which already has Telegram scaffolding) to send real-time fire photos and alerts to a phone |
| **Water level monitoring** | Add a float sensor to the water tank and display the level on the LCD — stop the pump automatically when the tank is empty |
| **Temperature sensor** | Integrate a DHT22 or thermocouple for ambient temperature logging alongside gas and visual detection |
| **Cloud dashboard** | Log detection events, timestamps, and sensor readings to a cloud service (e.g., ThingSpeak, Firebase) for remote monitoring |
| **Multiple camera support** | Support more than one ESP32-CAM to cover wider areas, with `Camera.py` aggregating feeds |
| **Model retraining pipeline** | Build a simple pipeline to collect false-positive frames and retrain the YOLO model to reduce misdetections over time |

---

Built with Python · MicroPython · OpenCV · YOLO · ESP32
