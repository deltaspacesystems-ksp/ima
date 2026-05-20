from flask import Flask, request, render_template_string
import lgpio
import logging
import signal
import sys
import atexit

app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# PP = Prawy Przód, PT = Prawy Tył, LP = Lewy Przód, LT = Lewy Tył
PP_IN1 = 4
PP_IN2 = 17
PT_IN1 = 25
PT_IN2 = 5
LP_IN1 = 27
LP_IN2 = 22
LT_IN1 = 23
LT_IN2 = 24

ALL_PINS = [PP_IN1, PP_IN2, PT_IN1, PT_IN2, LP_IN1, LP_IN2, LT_IN1, LT_IN2]

h = lgpio.gpiochip_open(0)

for pin in ALL_PINS:
    lgpio.gpio_claim_output(h, pin, 0)  # 0 = LOW od razu


def set_pin(pin, val):
    lgpio.gpio_write(h, pin, val)

def stop():
    for pin in ALL_PINS:
        set_pin(pin, 0)
    logger.info("Jazda: zatrzymano")

def forward():
    set_pin(LP_IN1, 1); set_pin(LP_IN2, 0)
    set_pin(LT_IN1, 1); set_pin(LT_IN2, 0)
    set_pin(PP_IN1, 1); set_pin(PP_IN2, 0)
    set_pin(PT_IN1, 1); set_pin(PT_IN2, 0)
    logger.info("Jazda: do przodu")

def backward():
    set_pin(LP_IN1, 0); set_pin(LP_IN2, 1)
    set_pin(LT_IN1, 0); set_pin(LT_IN2, 1)
    set_pin(PP_IN1, 0); set_pin(PP_IN2, 1)
    set_pin(PT_IN1, 0); set_pin(PT_IN2, 1)
    logger.info("Jazda: do tyłu")

def left():
    set_pin(LP_IN1, 0); set_pin(LP_IN2, 1)
    set_pin(LT_IN1, 0); set_pin(LT_IN2, 1)
    set_pin(PP_IN1, 1); set_pin(PP_IN2, 0)
    set_pin(PT_IN1, 1); set_pin(PT_IN2, 0)
    logger.info("Jazda: w lewo")

def right():
    set_pin(LP_IN1, 1); set_pin(LP_IN2, 0)
    set_pin(LT_IN1, 1); set_pin(LT_IN2, 0)
    set_pin(PP_IN1, 0); set_pin(PP_IN2, 1)
    set_pin(PT_IN1, 0); set_pin(PT_IN2, 1)
    logger.info("Jazda: w prawo")

def cleanup():
    stop()
    lgpio.gpiochip_close(h)

atexit.register(cleanup)

def signal_handler(sig, frame):
    logger.info("Przechwycono Ctrl+C")
    cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Robot Control</title>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f9;
            margin: 0;
            padding: 20px;
            text-align: center;
        }
        h1 { color: #333; font-size: 36px; margin-bottom: 20px; }
        .joystick {
            width: 300px;
            height: 300px;
            background-color: #ddd;
            border-radius: 50%;
            position: relative;
            margin: 20px auto;
            touch-action: none;
        }
        .joystick-button {
            width: 90px;
            height: 90px;
            background-color: #555;
            border-radius: 50%;
            position: absolute;
            top: 105px;
            left: 105px;
        }
        .control-button {
            padding: 15px 30px;
            margin: 10px;
            font-size: 20px;
            border: none;
            border-radius: 5px;
            background-color: #F44336;
            color: white;
            cursor: pointer;
        }
        .control-button:hover { background-color: #d32f2f; }
    </style>
</head>
<body>
    <h1>Robot Control</h1>
    <div class="joystick" id="joystick">
        <div class="joystick-button" id="joystick-button"></div>
    </div>
    <button class="control-button" id="stop">STOP</button>

    <script>
        const joystick = document.getElementById('joystick');
        const joystickButton = document.getElementById('joystick-button');
        let active = false;
        let direction = '';

        function sendCommand(cmd) {
            fetch('/control?cmd=' + cmd);
        }

        function handleMove(e) {
            if (!active) return;
            const rect = joystick.getBoundingClientRect();
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            let clientX, clientY;

            if (e.type === 'mousemove') {
                clientX = e.clientX - rect.left;
                clientY = e.clientY - rect.top;
            } else if (e.type === 'touchmove') {
                clientX = e.touches[0].clientX - rect.left;
                clientY = e.touches[0].clientY - rect.top;
            }

            const x = clientX - centerX;
            const y = clientY - centerY;
            const distance = Math.min(Math.sqrt(x*x + y*y), centerX - 45);
            const angle = Math.atan2(y, x);
            joystickButton.style.left = (centerX + distance * Math.cos(angle) - 45) + 'px';
            joystickButton.style.top  = (centerY + distance * Math.sin(angle) - 45) + 'px';

            let newDirection = 'stop';
            if (distance > 60) {
                if (Math.abs(x) > Math.abs(y)) {
                    newDirection = x > 0 ? 'right' : 'left';
                } else {
                    newDirection = y > 0 ? 'backward' : 'forward';
                }
            }

            if (newDirection !== direction) {
                direction = newDirection;
                sendCommand(direction);
            }
        }

        function handleStart(e) {
            active = true;
            if (e.type === 'touchstart') e.preventDefault();
            handleMove(e);
        }

        function handleEnd() {
            active = false;
            direction = 'stop';
            sendCommand('stop');
            joystickButton.style.left = '105px';
            joystickButton.style.top  = '105px';
        }

        joystick.addEventListener('mousedown', handleStart);
        document.addEventListener('mousemove', handleMove);
        document.addEventListener('mouseup', handleEnd);
        joystick.addEventListener('touchstart', handleStart);
        joystick.addEventListener('touchmove', handleMove);
        joystick.addEventListener('touchend', handleEnd);

        document.getElementById('stop').addEventListener('click', () => sendCommand('stop'));
        document.getElementById('stop').addEventListener('touchstart', (e) => {
            e.preventDefault();
            sendCommand('stop');
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/control')
def control():
    try:
        cmd = request.args.get('cmd', 'stop')
        if cmd == 'forward':    forward()
        elif cmd == 'backward': backward()
        elif cmd == 'left':     left()
        elif cmd == 'right':    right()
        else:                   stop()
        return f"Command: {cmd}"
    except Exception as e:
        logger.error(f"Błąd w control: {e}")
        return f"Error: {str(e)}"

if __name__ == '__main__':
    stop()
    logger.info("Uruchamianie serwera")
    app.run(host="0.0.0.0", port=5000, debug=False)

