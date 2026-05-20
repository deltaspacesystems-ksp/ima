#!/bin/bash

# Próba zatrzymania przez API
curl -s -X POST http://127.0.0.1:5000/api/stop >/dev/null 2>&1 || true
curl -s -X POST http://127.0.0.1:5000/api/audio/krzyk/stop >/dev/null 2>&1 || true
curl -s -X POST http://127.0.0.1:5000/api/audio/lang/stop >/dev/null 2>&1 || true
curl -s -X POST http://127.0.0.1:5000/api/autonomy/stop >/dev/null 2>&1 || true

# Twardy STOP na pinach BTS7960
for p in 17 18 22 23; do
  pinctrl set "$p" op dl || true
done
