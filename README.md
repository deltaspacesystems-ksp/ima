# Robot – mobilny przewodnik muzealny

Projekt robota przygotowany na zawody **WRO Future Innovators – Junior**.

Robot pełni funkcję mobilnego przewodnika muzealnego. Może być sterowany ręcznie z telefonu lub działać w trybie autonomicznym, podjeżdżając do kolejnych obrazów i odtwarzając ich opisy dźwiękowe.

## Główne funkcje

- sterowanie robotem przez przeglądarkę WWW,
- mobilny panel sterowania `/mobile`,
- joystick do jazdy ręcznej,
- obraz z kamery CSI ZeroCam 120°,
- lokalna mapa z LIDAR-a LDROBOT D500,
- wykrywanie przeszkód i automatyczne zatrzymanie,
- tryb autonomicznego przejazdu po muzeum,
- odtwarzanie opisów obrazów w języku polskim i angielskim,
- dźwięk ostrzegawczy przy przeszkodzie,
- regulacja głośności z poziomu strony,
- automatyczny start programu przez `systemd`.

## Wykorzystane elementy

- Raspberry Pi,
- LIDAR LDROBOT D500,
- kamera CSI ZeroCam 120°,
- sterowniki silników BTS7960,
- karta dźwiękowa USB,
- głośnik,
- Python,
- Flask,
- Picamera2,
- HTML / CSS / JavaScript.

## Sterowanie

Panel główny:

```text
http://adres-raspberry:5000/
