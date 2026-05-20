import lgpio
import time

# PP = Prawy Przód, PT = Prawy Tył, LP = Lewy Przód, LT = Lewy Tył
MOTORS = {
    'LP': (27, 22),
    'LT': (23, 24),
    'PP': (4,  17),
    'PT': (25,  5),
}

h = lgpio.gpiochip_open(0)

for name, (in1, in2) in MOTORS.items():
    lgpio.gpio_claim_output(h, in1, 0)
    lgpio.gpio_claim_output(h, in2, 0)

def set_motor(in1, in2, state):
    if state == 'forward':
        lgpio.gpio_write(h, in1, 1)
        lgpio.gpio_write(h, in2, 0)
    elif state == 'backward':
        lgpio.gpio_write(h, in1, 0)
        lgpio.gpio_write(h, in2, 1)
    else:
        lgpio.gpio_write(h, in1, 0)
        lgpio.gpio_write(h, in2, 0)

def all_stop():
    for name, (in1, in2) in MOTORS.items():
        lgpio.gpio_write(h, in1, 0)
        lgpio.gpio_write(h, in2, 0)

try:
    print("=== TEST SILNIKÓW (lgpio / Pi 5) ===\n")

    for name, (in1, in2) in MOTORS.items():
        input(f"[ ENTER ] Testuj silnik {name} (IN1=GPIO{in1}, IN2=GPIO{in2})")

        print(f"  {name}: DO PRZODU 2s")
        set_motor(in1, in2, 'forward')
        time.sleep(2)

        print(f"  {name}: STOP 1s")
        set_motor(in1, in2, 'stop')
        time.sleep(1)

        print(f"  {name}: DO TYLU 2s")
        set_motor(in1, in2, 'backward')
        time.sleep(2)

        print(f"  {name}: STOP\n")
        set_motor(in1, in2, 'stop')
        time.sleep(1)

    input("[ ENTER ] Wszystkie DO PRZODU 3s")
    for name, (in1, in2) in MOTORS.items():
        set_motor(in1, in2, 'forward')
    time.sleep(3)
    all_stop()
    time.sleep(1)

    input("[ ENTER ] Wszystkie DO TYLU 3s")
    for name, (in1, in2) in MOTORS.items():
        set_motor(in1, in2, 'backward')
    time.sleep(3)
    all_stop()

    print("\nTest zakończony.")

except KeyboardInterrupt:
    print("\nPrzerwano.")
finally:
    all_stop()
    lgpio.gpiochip_close(h)
