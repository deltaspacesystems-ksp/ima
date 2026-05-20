import os
import subprocess
import threading
\
from __future__ import annotations

import atexit
import time

from flask import Flask, jsonify, render_template, request

from robot.config import (
    ENABLE_OBSTACLE_STOP,
    FLASK_DEBUG,
    FLASK_HOST,
    FLASK_PORT,
    SAFE_DISTANCE_MM,
)
from robot.lidar import LidarMapper
from robot.motor import MotorController, clamp

app = Flask(__name__)

motors = MotorController()
lidar = LidarMapper()
lidar.start()


def shutdown() -> None:
    print("[APP] Shutting down")
    motors.cleanup()
    lidar.stop()


atexit.register(shutdown)


@app.route("/")
def index():
    return render_template(
        "index.html",
        safe_distance_mm=SAFE_DISTANCE_MM,
        obstacle_stop=int(ENABLE_OBSTACLE_STOP),
    )


@app.route("/api/status")
def api_status():
    lidar_data = lidar.get_data(include_map=False)
    return jsonify(
        {
            "ok": True,
            "time": time.time(),
            "motors": motors.as_dict(),
            "lidar": lidar_data["status"],
            "safe_distance_mm": SAFE_DISTANCE_MM,
            "obstacle_stop": ENABLE_OBSTACLE_STOP,
        }
    )


@app.route("/api/drive", methods=["POST"])
def api_drive():
    data = request.get_json(silent=True) or {}

    throttle = clamp(float(data.get("throttle", 0.0)))
    turn = clamp(float(data.get("turn", 0.0)))

    front_distance = lidar.get_front_distance()
    blocked = False

    if (
        ENABLE_OBSTACLE_STOP
        and throttle > 0.05
        and front_distance is not None
        and front_distance < SAFE_DISTANCE_MM
    ):
        motors.stop()
        blocked = True
    else:
        motors.drive(throttle=throttle, turn=turn)

    return jsonify(
        {
            "ok": True,
            "blocked": blocked,
            "front_distance_mm": front_distance,
            "motors": motors.as_dict(),
        }
    )


@app.route("/api/stop", methods=["POST"])
def api_stop():
    motors.stop()
    return jsonify({"ok": True, "motors": motors.as_dict()})


@app.route("/api/motor/<name>", methods=["POST"])
def api_single_motor(name: str):
    """
    Endpoint testowy do sprawdzania kierunku pojedynczego silnika.
    JSON:
    {
      "speed": 0.4
    }
    """
    data = request.get_json(silent=True) or {}
    speed = clamp(float(data.get("speed", 0.0)))
    motors.set_motor(name, speed)
    return jsonify({"ok": True, "motors": motors.as_dict()})


@app.route("/api/lidar")
def api_lidar():
    return jsonify({"ok": True, **lidar.get_data(include_map=True)})


@app.route("/api/lidar/clear", methods=["POST"])
def api_lidar_clear():
    lidar.clear_map()
    return jsonify({"ok": True})





@app.route("/mobile")
def mobile_panel():
    return render_template("mobile.html")



# === AUDIO NA RASPBERRY PI ===

audio_process = None
audio_lock = threading.Lock()

AUDIO_FILES = {
    "panorama": "/opt/robot/static/panorama.mp3",
    "stanczyk": "/opt/robot/static/stanczyk.mp3",
    "grunwald": "/opt/robot/static/grunwald.mp3",
}


def stop_audio_process():
    global audio_process

    with audio_lock:
        try:
            if audio_process and audio_process.poll() is None:
                audio_process.terminate()
                audio_process.wait(timeout=1.0)
        except Exception:
            try:
                audio_process.kill()
            except Exception:
                pass

        audio_process = None


@app.route("/api/audio/play/<name>", methods=["POST"])
def api_audio_play(name):
    global audio_process

    if name not in AUDIO_FILES:
        return jsonify({"ok": False, "error": "Nieznany plik audio"}), 404

    audio_path = AUDIO_FILES[name]

    if not os.path.exists(audio_path):
        return jsonify({
            "ok": False,
            "error": f"Brak pliku: {audio_path}"
        }), 404

    audio_device = os.getenv("AUDIO_DEVICE", "").strip()

    cmd = ["mpg123", "-q"]

    if audio_device:
        cmd += ["-a", audio_device]

    cmd.append(audio_path)

    stop_audio_process()

    with audio_lock:
        try:
            audio_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            return jsonify({
                "ok": True,
                "playing": name,
                "device": audio_device or "default",
                "cmd": " ".join(cmd),
            })

        except Exception as exc:
            return jsonify({
                "ok": False,
                "error": str(exc)
            }), 500


@app.route("/api/audio/stop", methods=["POST"])
def api_audio_stop():
    stop_audio_process()
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG, threaded=True)
