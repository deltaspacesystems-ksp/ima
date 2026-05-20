import serial
import numpy as np
import matplotlib.pyplot as plt
import time
import struct

# ================= KONFIGURACJA =================
SERIAL_PORT = "/dev/ttyUSB0"          # Zmień na swój port! (np. /dev/ttyUSB0 na Linux/RPi)
BAUDRATE = 230400
# ===============================================

ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=0.5)

# Do wizualizacji
plt.ion()
fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})
ax.set_title("WitMotion D500 / LD19 LiDAR")
points, = ax.plot([], [], 'b.', markersize=2)
ax.set_rlim(0, 12)   # max 12 metrów

def parse_ld19_packet(data):
    """Parsuje paczkę z LD19 / D500"""
    if len(data) != 47:
        return None
    
    # Sprawdzenie nagłówka i CRC (proste)
    if data[0] != 0x54 or data[1] != 0x2C:
        return None
    
    # Prędkość obrotowa (stopnie/s)
    speed = (data[3] << 8 | data[2]) / 100.0
    
    start_angle = (data[5] << 8 | data[4]) / 100.0
    end_angle   = (data[43] << 8 | data[42]) / 100.0
    
    distances = []
    angles = []
    
    for i in range(12):  # 12 pomiarów w paczce
        dist = data[6 + i*3] | (data[7 + i*3] << 8)
        # intensity = data[8 + i*3]   # można wykorzystać później
        
        if dist > 0 and dist < 12000:   # 12m = 12000 mm
            angle = start_angle + (end_angle - start_angle) * (i / 11.0)
            distances.append(dist / 1000.0)   # w metrach
            angles.append(np.radians(angle))
    
    return angles, distances, speed


print("LiDAR uruchomiony... Naciśnij Ctrl+C aby zakończyć")

try:
    buffer = bytearray()
    while True:
        if ser.in_waiting:
            buffer.extend(ser.read(ser.in_waiting))
            
            # Szukamy pełnych paczek (47 bajtów)
            while len(buffer) >= 47:
                if buffer[0] == 0x54 and buffer[1] == 0x2C:
                    packet = buffer[:47]
                    result = parse_ld19_packet(packet)
                    
                    if result:
                        angles, dists, speed = result
                        if dists:
                            # Aktualizacja wykresu
                            points.set_data(angles, dists)
                            ax.set_theta_zero_location('N')   # 0° na górze
                            plt.draw()
                            plt.pause(0.001)
                    
                    buffer = buffer[47:]
                else:
                    buffer = buffer[1:]   # usuwamy śmieci na początku

except KeyboardInterrupt:
    print("\nZakończono.")
finally:
    ser.close()
    plt.close()
