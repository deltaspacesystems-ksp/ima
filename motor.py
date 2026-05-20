from __future__ import annotations

import os
import time
from dataclasses import dataclass


def clamp(value: float, low: float = -1.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value.strip().lower() in ("1", "true", "yes", "on", "tak")


@dataclass
class MotorState:
    lf: float = 0.0
    lr: float = 0.0
    rf: float = 0.0
    rr: float = 0.0
    updated_at: float = 0.0


class BTS7960Side:
    """
    Sterowanie jedną stroną robota przez BTS7960.

    Dla BTS7960:
    RPWM HIGH / PWM, LPWM LOW  -> kierunek 1
    RPWM LOW, LPWM HIGH / PWM  -> kierunek 2
    RPWM LOW, LPWM LOW         -> STOP / luz

    R_EN i L_EN są u Ciebie podłączone na stałe,
    więc program steruje tylko RPWM i LPWM.
    """

    def __init__(
        self,
        controller,
        name: str,
        rpwm_pin: int,
        lpwm_pin: int,
        invert: bool = False,
    ) -> None:
        self.controller = controller
        self.name = name
        self.rpwm_pin = rpwm_pin
        self.lpwm_pin = lpwm_pin
        self.invert = invert
        self.speed = 0.0
        self.effective_speed = 0.0

    def set_speed(self, speed: float) -> None:
        command_speed = clamp(speed)
        effective_speed = -command_speed if self.invert else command_speed

        changing_direction = (
            self.effective_speed != 0
            and effective_speed != 0
            and (
                (self.effective_speed > 0 and effective_speed < 0)
                or (self.effective_speed < 0 and effective_speed > 0)
            )
        )

        if changing_direction:
            self.stop()
            time.sleep(0.03)

        if effective_speed > 0:
            self.controller.set_pwm(self.lpwm_pin, 0.0)
            self.controller.set_pwm(self.rpwm_pin, abs(effective_speed))
        elif effective_speed < 0:
            self.controller.set_pwm(self.rpwm_pin, 0.0)
            self.controller.set_pwm(self.lpwm_pin, abs(effective_speed))
        else:
            self.stop()

        self.speed = command_speed
        self.effective_speed = effective_speed

    def stop(self) -> None:
        self.controller.set_pwm(self.rpwm_pin, 0.0)
        self.controller.set_pwm(self.lpwm_pin, 0.0)
        self.speed = 0.0
        self.effective_speed = 0.0


class MotorController:
    """
    BTS7960, sterowanie lewą i prawą stroną.

    Prawa strona:
      RPWM / P_PWM -> GPIO17
      LPWM / L_PWM -> GPIO18

    Lewa strona:
      RPWM / P_PWM -> GPIO22
      LPWM / L_PWM -> GPIO23
    """

    PWM_FREQ = 1000

    def __init__(self) -> None:
        self.available = False
        self.lgpio = None
        self.handle = None

        self.pins = [17, 18, 22, 23]

        try:
            import lgpio

            self.lgpio = lgpio
            self.handle = lgpio.gpiochip_open(0)

            for pin in self.pins:
                try:
                    lgpio.gpio_free(self.handle, pin)
                except Exception:
                    pass

                lgpio.gpio_claim_output(self.handle, pin, 0)
                lgpio.gpio_write(self.handle, pin, 0)

            self.available = True
            print("[MOTOR] lgpio initialized for BTS7960")

        except Exception as exc:
            self.available = False
            print(f"[MOTOR] lgpio unavailable, simulation mode: {exc}")

        self.right = BTS7960Side(
            controller=self,
            name="RIGHT",
            rpwm_pin=17,
            lpwm_pin=18,
            invert=env_bool("INVERT_RIGHT", False),
        )

        self.left = BTS7960Side(
            controller=self,
            name="LEFT",
            rpwm_pin=22,
            lpwm_pin=23,
            invert=env_bool("INVERT_LEFT", False),
        )

        self.state = MotorState(updated_at=time.time())

        self.stop()

        print("[MOTOR] BTS7960 configuration:")
        print("[MOTOR] RIGHT: RPWM GPIO17, LPWM GPIO18")
        print("[MOTOR] LEFT : RPWM GPIO22, LPWM GPIO23")
        print(f"[MOTOR] INVERT_RIGHT={self.right.invert}")
        print(f"[MOTOR] INVERT_LEFT={self.left.invert}")

    def set_pwm(self, gpio_pin: int, value: float) -> None:
        """
        value: 0.0 - 1.0

        Dla testów:
        value=1.0 ustawia pin jako zwykłe HIGH,
        więc pinctrl get powinien pokazać hi.
        """
        value = max(0.0, min(1.0, float(value)))

        if not self.available:
            return

        duty = value * 100.0

        try:
            if value <= 0.0:
                try:
                    self.lgpio.tx_pwm(self.handle, gpio_pin, self.PWM_FREQ, 0)
                except Exception:
                    pass
                self.lgpio.gpio_write(self.handle, gpio_pin, 0)

            elif value >= 0.999:
                try:
                    self.lgpio.tx_pwm(self.handle, gpio_pin, self.PWM_FREQ, 0)
                except Exception:
                    pass
                self.lgpio.gpio_write(self.handle, gpio_pin, 1)

            else:
                self.lgpio.tx_pwm(self.handle, gpio_pin, self.PWM_FREQ, duty)

        except Exception as exc:
            print(f"[MOTOR] GPIO{gpio_pin} PWM error: {exc}")

    def set_left(self, speed: float) -> None:
        speed = clamp(speed)
        self.left.set_speed(speed)

        self.state.lf = speed
        self.state.lr = speed
        self.state.updated_at = time.time()

    def set_right(self, speed: float) -> None:
        speed = clamp(speed)
        self.right.set_speed(speed)

        self.state.rf = speed
        self.state.rr = speed
        self.state.updated_at = time.time()

    def set_motor(self, name: str, speed: float) -> None:
        """
        Zachowane dla zgodności z panelem WWW.

        Przy obecnych 4 pinach BTS7960 sterujemy stronami:
        LF/LR -> lewa strona
        RF/RR -> prawa strona
        """
        name = name.upper()
        speed = clamp(speed)

        if name in ("LF", "LR", "LEFT", "L"):
            self.set_left(speed)
        elif name in ("RF", "RR", "RIGHT", "R"):
            self.set_right(speed)
        else:
            raise ValueError(f"Unknown motor/side: {name}")

    def set_all(self, lf: float, lr: float, rf: float, rr: float) -> None:
        left_speed = clamp((float(lf) + float(lr)) / 2.0)
        right_speed = clamp((float(rf) + float(rr)) / 2.0)

        self.set_left(left_speed)
        self.set_right(right_speed)

    def drive(self, throttle: float, turn: float) -> MotorState:
        """
        throttle: -1..1
        turn: -1..1

        + throttle = jazda do przodu
        + turn = skręt w prawo
        """
        throttle = clamp(throttle)
        turn = clamp(turn)

        left_speed = throttle + turn
        right_speed = throttle - turn

        max_mag = max(1.0, abs(left_speed), abs(right_speed))
        left_speed /= max_mag
        right_speed /= max_mag

        self.set_left(left_speed)
        self.set_right(right_speed)

        return self.state

    def stop(self) -> MotorState:
        self.left.stop()
        self.right.stop()

        self.state = MotorState(
            lf=0.0,
            lr=0.0,
            rf=0.0,
            rr=0.0,
            updated_at=time.time(),
        )

        return self.state

    def cleanup(self) -> None:
        try:
            self.stop()

            if self.available:
                for pin in self.pins:
                    try:
                        self.set_pwm(pin, 0.0)
                        self.lgpio.gpio_free(self.handle, pin)
                    except Exception:
                        pass

                try:
                    self.lgpio.gpiochip_close(self.handle)
                except Exception:
                    pass

        except Exception as exc:
            print(f"[MOTOR] Cleanup error: {exc}")

    def as_dict(self) -> dict:
        return {
            "available": self.available,
            "driver": "BTS7960_direct_lgpio",
            "mode": "left_right_drive",
            "left": {
                "rpwm_gpio": 22,
                "lpwm_gpio": 23,
                "speed": round(self.left.speed, 3),
                "effective_speed": round(self.left.effective_speed, 3),
                "invert": self.left.invert,
            },
            "right": {
                "rpwm_gpio": 17,
                "lpwm_gpio": 18,
                "speed": round(self.right.speed, 3),
                "effective_speed": round(self.right.effective_speed, 3),
                "invert": self.right.invert,
            },
            "lf": round(self.state.lf, 3),
            "lr": round(self.state.lr, 3),
            "rf": round(self.state.rf, 3),
            "rr": round(self.state.rr, 3),
            "updated_at": self.state.updated_at,
        }
