# Robot Flask + Raspberry Pi + 4 silniki + LIDAR

Projekt zawiera prosty panel WWW we Flasku do sterowania robotem z przeglądarki oraz podgląd lokalnej mapy 2D z LIDAR-a.

## Założenia sprzętowe

Silniki / sterowniki H-bridge podłączone do GPIO BCM:

| Silnik | IN1 | IN2 |
|---|---:|---:|
| LF - lewy przód | GPIO 19 | GPIO 26 |
| LR - lewy tył | GPIO 6 | GPIO 13 |
| RF - prawy przód | GPIO 20 | GPIO 21 |
| RR - prawy tył | GPIO 12 | GPIO 16 |

LIDAR USB/COM domyślnie: `/dev/ttyUSB0`.

## Ważne ograniczenie

Ten kod pokazuje lokalną mapę punktową z LIDAR-a. Bez enkoderów, IMU albo pełnego SLAM-u nie jest to jeszcze poprawna globalna mapa terenu podczas jazdy. Gdy robot stoi, mapa jest wiarygodna lokalnie. Gdy robot jedzie, punkty są nadal przydatne do podglądu i wykrywania przeszkód, ale nie tworzą dokładnej mapy globalnej.

## Uruchomienie na Raspberry Pi

```bash
sudo apt update
sudo apt install -y python3-venv python3-dev python3-lgpio

cd robot_flask_lidar
python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

cp .env.example .env
nano .env
```

Sprawdź port LIDAR-a:

```bash
ls -l /dev/ttyUSB* /dev/ttyACM* 2>/dev/null
```

Jeżeli LIDAR jest np. na `/dev/ttyUSB1`, zmień `LIDAR_PORT` w pliku `.env`.

Uruchomienie:

```bash
source venv/bin/activate
python app.py
```

W przeglądarce otwórz:

```text
http://IP_RASPBERRY_PI:5000
```

Adres IP Raspberry Pi sprawdzisz poleceniem:

```bash
hostname -I
```

## Sterowanie

- W/S - jazda przód/tył
- A/D - skręt w lewo/prawo
- Spacja - stop
- Przyciski w panelu WWW działają również z telefonu

## Kalibracja kierunku silników

Jeżeli któryś silnik kręci się odwrotnie, zmień w `.env`:

```text
INVERT_LF=1
INVERT_LR=1
INVERT_RF=1
INVERT_RR=1
```

dla właściwego silnika.

## Kalibracja przodu LIDAR-a

Jeśli przeszkoda z przodu nie jest widoczna jako "front" w panelu, zmień:

```text
FRONT_ANGLE_DEG=0
```

na 90, 180 lub 270, zależnie od fizycznego montażu LIDAR-a.

## Uprawnienia do portu USB

Jeżeli pojawi się błąd dostępu do LIDAR-a:

```bash
sudo usermod -aG dialout $USER
sudo reboot
```

## Autostart jako usługa systemd

Przykładowy plik:

```ini
[Unit]
Description=Robot Flask LIDAR
After=network-online.target
Wants=network-online.target

[Service]
WorkingDirectory=/home/pi/robot_flask_lidar
ExecStart=/home/pi/robot_flask_lidar/venv/bin/python /home/pi/robot_flask_lidar/app.py
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```

Zapisz jako:

```bash
sudo nano /etc/systemd/system/robot-flask.service
```

Następnie:

```bash
sudo systemctl daemon-reload
sudo systemctl enable robot-flask.service
sudo systemctl start robot-flask.service
sudo systemctl status robot-flask.service
```
