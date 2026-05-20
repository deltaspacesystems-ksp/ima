import serial
import time

PORT = "/dev/ttyUSB0"
BAUDRATES = [115200, 128000, 153600, 230400, 256000, 460800, 921600]

def hx(data):
    if not data:
        return "<brak danych>"
    return data.hex(" ")

for baud in BAUDRATES:
    print("=" * 70)
    print(f"Test baudrate: {baud}")

    try:
        ser = serial.Serial(PORT, baudrate=baud, timeout=0.5)
        time.sleep(0.2)

        ser.reset_input_buffer()
        ser.reset_output_buffer()

        # RPLidar STOP
        ser.write(bytes([0xA5, 0x25]))
        time.sleep(0.2)
        ser.reset_input_buffer()

        # RPLidar GET_INFO
        ser.write(bytes([0xA5, 0x50]))
        time.sleep(0.4)
        data = ser.read(64)
        print("Odpowiedź po komendzie RPLidar GET_INFO:")
        print(hx(data))

        ser.reset_input_buffer()
        time.sleep(1.0)
        passive = ser.read(64)
        print("Dane pasywne z portu, bez komendy:")
        print(hx(passive))

        ser.close()

    except Exception as e:
        print("Błąd:", e)
