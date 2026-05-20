#!/bin/bash

cd /opt/robot

# Bezpieczny STOP na pinach BTS7960
for p in 17 18 22 23; do
  pinctrl set "$p" op dl || true
done

# Daj czas na USB: LIDAR, karta audio, kamera
sleep 4

exec /opt/robot/venv/bin/python /opt/robot/app.py
