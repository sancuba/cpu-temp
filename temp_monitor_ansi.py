import glob
import sys
import time

# Anchos de columnas
ZONE_W = 15
SENSOR_W = 25
TEMP_W = 10

TEMP_COL = ZONE_W + 1 + SENSOR_W + 1
TABLE_W = ZONE_W + SENSOR_W + TEMP_W + 2

STATUS_TEXT = "THERMAL ZONE MONITORING"
SPINNER = "/-\\|"


def get_thermal_sensors():
    sensors = []
    for zone in sorted(glob.glob("/sys/class/thermal/thermal_zone*")):
        try:
            with open(f"{zone}/type") as f:
                sensor_type = f.read().strip()
            with open(f"{zone}/temp") as f:
                temp_c = int(f.read()) / 1000
            sensors.append(
                {"zone": zone.split("/")[-1], "type": sensor_type, "temp_c": temp_c}
            )
        except:
            continue
    return sensors


def move_cursor(row, col):
    sys.stdout.write(f"\033[{row};{col}H")


def draw_static_table(sensors):
    print(f"{'ZONE':<{ZONE_W}} {'SENSOR':<{SENSOR_W}} {'TEMP (°C)':>{TEMP_W}}")
    print("-" * TABLE_W)
    for s in sensors:
        print(f"{s['zone']:<{ZONE_W}} {s['type']:<{SENSOR_W}} {'':>{TEMP_W}}")
    print("-" * TABLE_W)
    print(f"{STATUS_TEXT} [ ]")


def main():
    sensors = get_thermal_sensors()

    # limpiar pantalla
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()

    draw_static_table(sensors)

    start_row = 3
    row_map = {s["zone"]: start_row + i for i, s in enumerate(sensors)}

    # Fila de la línea TEMP ZONE MONITORING
    status_row = start_row + len(sensors) + 1
    spinner_row = status_row

    # Columna exacta del corchete [
    spinner_col = len(STATUS_TEXT) + 2  # el '[' está en columna len(STATUS_TEXT)+2

    tick = 0

    try:
        while True:
            sensors = get_thermal_sensors()

            # actualizar temperaturas
            for s in sensors:
                row = row_map.get(s["zone"])
                if row:
                    move_cursor(row, TEMP_COL + 1)
                    sys.stdout.write(f"{s['temp_c']:>{TEMP_W}.1f}")

            # actualizar spinner
            move_cursor(spinner_row, spinner_col + 1)
            sys.stdout.write(SPINNER[tick % len(SPINNER)])

            sys.stdout.flush()  # Forzar impresion del buffer de salida
            tick += 1
            time.sleep(1)

    except KeyboardInterrupt:
        move_cursor(spinner_row + 2, 1)
        print("END THERMAL ZONE MONITORING...")


if __name__ == "__main__":
    main()
