import RPi.GPIO as GPIO
import time

PINS = [19, 26, 6, 13, 20, 21, 12, 16]

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

for pin in PINS:
    GPIO.setup(pin, GPIO.OUT, initial=GPIO.HIGH)

print("Wszystkie piny HIGH. Ctrl+C aby zakończyć.")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    GPIO.cleanup()
    print("GPIO zwolnione.")
