from machine import Pin, ADC, PWM, SoftI2C
import time, sys, select, network, json
import urequests
from machine_i2c_lcd import I2cLcd

# ======================
# HARDWARE SETUP
# ======================
green = Pin(18, Pin.OUT)
yellow = Pin(2, Pin.OUT)
red = Pin(23, Pin.OUT)
buzzer = Pin(4, Pin.OUT)

relay_speed = Pin(15, Pin.OUT)
relay_pump  = Pin(16, Pin.OUT)

mq5 = ADC(Pin(33))
mq5.atten(ADC.ATTN_11DB)
mq5.width(ADC.WIDTH_12BIT)

servo = PWM(Pin(13), freq=50)

i2c = SoftI2C(sda=Pin(21), scl=Pin(22), freq=400000)
lcd = I2cLcd(i2c, 0x27, 2, 16)

# ======================
# CONFIG
# ======================
GAS_THRESHOLD = 4000

WIFI_SSID  = "POCO F6 Pro"
WIFI_PASS  = "12345678"    # <-- change this
BOT_TOKEN  = "7977075771:AAFwBVdM4HopQW8JY4ti1YsXKg5Y_E34I1Y"
CHAT_ID    = "-5184381589"

SERVO_CENTER = 45

current_state   = ""
fire_detected   = False
was_suppressing = False
fire_angle      = SERVO_CENTER
fire_alerted    = False

# ======================
# WIFI + TELEGRAM
# ======================
def wifi_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(WIFI_SSID, WIFI_PASS)
        for _ in range(20):
            if wlan.isconnected(): break
            time.sleep(0.5)
    if wlan.isconnected():
        print("WiFi OK: {}".format(wlan.ifconfig()[0]))
    else:
        print("WiFi FAILED")
    return wlan.isconnected()

def tg_send(text):
    try:
        url = "https://api.telegram.org/bot{}/sendMessage".format(BOT_TOKEN)
        r = urequests.post(url,
            headers={"Content-Type": "application/json"},
            data=json.dumps({"chat_id": CHAT_ID, "text": text}))
        r.close()
        print("TG sent: {}".format(text))
    except Exception as e:
        print("TG error: {}".format(e))

# ======================
# SERVO
# ======================
def set_servo_angle(angle):
    angle = max(0, min(90, angle))
    duty  = int(26 + (angle / 180) * 102)
    servo.duty(duty)

# ======================
# BOOT — everything off, servo to center
# ======================
green.off()
yellow.off()
red.off()
buzzer.off()
relay_speed.off()
relay_pump.off()
set_servo_angle(SERVO_CENTER)
print("BOOT_OK")

# ======================
# PUMP HELPERS
# ======================
def pump_on():
    relay_speed.on()
    time.sleep(0.1)
    relay_pump.on()
    print("Pump ON")

def pump_off():
    relay_pump.off()
    time.sleep(0.1)
    relay_speed.off()
    print("Pump OFF")

# ======================
# LCD UPDATE
# ======================
def set_lcd(state, line1, line2=""):
    global current_state
    if state != current_state:
        lcd.clear()
        lcd.putstr(line1)
        lcd.move_to(0, 1)
        lcd.putstr(line2)
        current_state = state

# ======================
# READ SERIAL COMMAND
# ======================
def read_command():
    global fire_detected, fire_angle
    try:
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            command = sys.stdin.readline().strip()
            if command.startswith("FIRE"):
                fire_detected = True
                if ":" in command:
                    fire_angle = int(command.split(":")[1])
                print("CMD: FIRE angle={}".format(fire_angle))
            elif command == "CLEAR":
                fire_detected = False
                fire_angle    = SERVO_CENTER
                print("CMD: CLEAR")
    except:
        pass

# ======================
# SAFE MODE
# ======================
def safe_mode():
    green.on()
    yellow.off()
    red.off()
    buzzer.off()
    pump_off()
    set_servo_angle(SERVO_CENTER)
    set_lcd("safe", "SYSTEM SAFE", "No Fire/Gas")

# ======================
# SMOKE MODE
# ======================
def smoke_mode():
    green.off()
    yellow.on()
    red.off()
    set_lcd("smoke", "SMOKE DETECTED", "WARNING")
    buzzer.on()
    time.sleep(0.1)
    buzzer.off()
    set_servo_angle(SERVO_CENTER)

# ======================
# FIRE MODE
# ======================
def fire_mode(angle=SERVO_CENTER):
    green.off()
    yellow.off()
    red.on()
    buzzer.on()
    set_servo_angle(angle)
    set_lcd("fire", "FIRE DETECTED", "DANGER!")
    pump_on()

# ======================
# STOP SUPPRESSION
# ======================
def stop_suppression():
    global was_suppressing
    pump_off()
    set_servo_angle(SERVO_CENTER)
    was_suppressing = False
    print("Suppression stopped")

# ======================
# WARM UP SENSOR
# ======================
print("Warming up MQ-5...")
lcd.clear()
lcd.putstr("Warming up...")
lcd.move_to(0, 1)
lcd.putstr("Please wait...")

for i in range(10):
    read_command()
    time.sleep(1)
    print("Warm up: {}/10".format(i + 1))

wifi_ok = wifi_connect()

print("READY")
lcd.clear()
lcd.putstr("System Ready!")
time.sleep(1)

# ======================
# MAIN LOOP
# ======================
while True:
    read_command()

    gas_value = mq5.read()
    print("GAS:{}|FIRE:{}|ANGLE:{}".format(gas_value, fire_detected, fire_angle))

    # --- Telegram fire alert (send once per event) ---
    if wifi_ok:
        if fire_detected and not fire_alerted:
            tg_send("FIRE detected!")
            fire_alerted = True
        elif not fire_detected and fire_alerted:
            fire_alerted = False

    # --- Priority system ---
    if fire_detected:
        was_suppressing = True
        fire_mode(angle=fire_angle)

    elif gas_value >= GAS_THRESHOLD:
        was_suppressing = True
        smoke_mode()

    else:
        if was_suppressing:
            stop_suppression()
        safe_mode()

    time.sleep(0.3)
