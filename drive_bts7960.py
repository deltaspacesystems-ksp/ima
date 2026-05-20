import RPi.GPIO as GPIO
import time
import signal
import sys

# =========================
# KONFIGURACJA PINÓW - BCM
# =========================

RIGHT_RPWM = 17   # prawa strona - P PWM / RPWM
RIGHT_LPWM = 18   # prawa strona - L PWM / LPWM

LEFT_RPWM = 22    # lewa strona - P PWM / RPWM
LEFT_LPWM = 23    # lewa strona - L PWM / LPWM

PWM_FREQ = 1000   # Hz

# Odwrócenie stron, gdy robot jedzie odwrotnie
INVERT_LEFT = False
INVERT_RIGHT = False

# Domyślna prędkość testowa
DEFAULT_SPEED = 45  # procent


# =========================
# INICJALIZACJA GPIO
# =========================

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

PINS = [RIGHT_RPWM, RIGHT_LPWM, LEFT_RPWM, LEFT_LPWM]

for pin in PINS:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

pwm_right_r = GPIO.PWM(RIGHT_RPWM, PWM_FREQ)
pwm_right_l = GPIO.PWM(RIGHT_LPWM, PWM_FREQ)
pwm_left_r = GPIO.PWM(LEFT_RPWM, PWM_FREQ)
pwm_left_l = GPIO.PWM(LEFT_LPWM, PWM_FREQ)

pwm_right_r.start(0)
pwm_right_l.start(0)
pwm_left_r.start(0)
pwm_left_l.start(0)


# =========================
# FUNKCJE POMOCNICZE
# =========================

def clamp(value, min_value=-100, max_value=100):
    return max(min_value, min(max_value, value))


def set_side(rpwm, lpwm, speed):
    """
    Sterowanie jedną stroną BTS7960.

    speed > 0  -> RPWM aktywne, LPWM = 0
    speed < 0  -> LPWM aktywne, RPWM = 0
    speed = 0  -> STOP
    """

    speed = clamp(speed)

    if speed > 0:
        lpwm.ChangeDutyCycle(0)
        rpwm.ChangeDutyCycle(abs(speed))

    elif speed < 0:
        rpwm.ChangeDutyCycle(0)
        lpwm.ChangeDutyCycle(abs(speed))

    else:
        rpwm.ChangeDutyCycle(0)
        lpwm.ChangeDutyCycle(0)


def set_left(speed):
    if INVERT_LEFT:
        speed = -speed

    set_side(pwm_left_r, pwm_left_l, speed)


def set_right(speed):
    if INVERT_RIGHT:
        speed = -speed

    set_side(pwm_right_r, pwm_right_l, speed)


def drive(left_speed, right_speed):
    """
    left_speed, right_speed: od -100 do 100
    """
    set_left(left_speed)
    set_right(right_speed)


def stop():
    drive(0, 0)
    print("STOP")


# =========================
# RUCH ROBOTA
# =========================

def forward(speed=DEFAULT_SPEED):
    print("Jazda do przodu")
    drive(speed, speed)


def backward(speed=DEFAULT_SPEED):
    print("Jazda do tyłu")
    drive(-speed, -speed)


def turn_left(speed=DEFAULT_SPEED):
    print("Skręt w lewo")
    drive(-speed, speed)


def turn_right(speed=DEFAULT_SPEED):
    print("Skręt w prawo")
    drive(speed, -speed)


def soft_left(speed=DEFAULT_SPEED):
    print("Łagodny skręt w lewo")
    drive(int(speed * 0.35), speed)


def soft_right(speed=DEFAULT_SPEED):
    print("Łagodny skręt w prawo")
    drive(speed, int(speed * 0.35))


# =========================
# SPRZĄTANIE
# =========================

def cleanup():
    print("Zatrzymywanie robota i czyszczenie GPIO...")
    stop()

    pwm_right_r.stop()
    pwm_right_l.stop()
    pwm_left_r.stop()
    pwm_left_l.stop()

    for pin in PINS:
        GPIO.output(pin, GPIO.LOW)

    GPIO.cleanup()


def signal_handler(sig, frame):
    cleanup()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


# =========================
# TRYB TESTOWY Z KLAWIATURY
# =========================

def print_menu():
    print()
    print("Sterowanie robotem BTS7960")
    print("--------------------------")
    print("w  - przód")
    print("s  - tył")
    print("a  - obrót w lewo")
    print("d  - obrót w prawo")
    print("q  - łagodny skręt w lewo")
    print("e  - łagodny skręt w prawo")
    print("x  - STOP")
    print("+  - zwiększ prędkość")
    print("-  - zmniejsz prędkość")
    print("0  - STOP i wyjście")
    print()


if __name__ == "__main__":
    speed = DEFAULT_SPEED

    try:
        stop()
        print_menu()

        while True:
            print(f"Aktualna prędkość: {speed}%")
            cmd = input("Komenda: ").strip().lower()

            if cmd == "w":
                forward(speed)

            elif cmd == "s":
                backward(speed)

            elif cmd == "a":
                turn_left(speed)

            elif cmd == "d":
                turn_right(speed)

            elif cmd == "q":
                soft_left(speed)

            elif cmd == "e":
                soft_right(speed)

            elif cmd == "x":
                stop()

            elif cmd == "+":
                speed = min(100, speed + 5)
                print(f"Prędkość: {speed}%")

            elif cmd == "-":
                speed = max(10, speed - 5)
                print(f"Prędkość: {speed}%")

            elif cmd == "0":
                stop()
                break

            else:
                print("Nieznana komenda")
                print_menu()

    finally:
        cleanup()
