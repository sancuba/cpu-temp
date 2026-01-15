import argparse
import glob
import subprocess
import sys
import time

# Anchos de columnas para el modo ANSI
ZONE_W = 15
SENSOR_W = 25
TEMP_W = 10

TEMP_COL = ZONE_W + 1 + SENSOR_W + 1
TABLE_W = ZONE_W + SENSOR_W + TEMP_W + 2

STATUS_TEXT = "THERMAL ZONE MONITORING"
SPINNER = "/-\\|"


def get_thermal_sensors():
    """Lee y devuelve una lista de todos los sensores térmicos."""
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
        except (IOError, ValueError):
            continue
    return sensors


def move_cursor(row, col):
    """Mueve el cursor del terminal a la posición especificada."""
    sys.stdout.write(f"\033[{row};{col}H")


def draw_static_table(sensors, status_line):
    """Dibuja la tabla estática con una línea de estado personalizable."""
    print(f"{'ZONE':<{ZONE_W}} {'SENSOR':<{SENSOR_W}} {'TEMP (°C)':>{TEMP_W}}")
    print("-" * TABLE_W)
    for s in sensors:
        print(f"{s['zone']:<{ZONE_W}} {s['type']:<{SENSOR_W}} {'':>{TEMP_W}}")
    print("-" * TABLE_W)
    print(f"{status_line} [ ]")


def run_ansi_monitor():
    """Ejecuta el monitor de temperatura en el terminal con formato ANSI."""
    sensors = get_thermal_sensors()

    # Limpiar pantalla
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()

    draw_static_table(sensors, STATUS_TEXT)

    start_row = 3
    row_map = {s["zone"]: start_row + i for i, s in enumerate(sensors)}
    status_row = start_row + len(sensors) + 1
    spinner_col = len(STATUS_TEXT) + 2

    tick = 0
    try:
        while True:
            sensors = get_thermal_sensors()
            for s in sensors:
                row = row_map.get(s["zone"])
                if row:
                    move_cursor(row, TEMP_COL + 1)
                    sys.stdout.write(f"{s['temp_c']:>{TEMP_W}.1f}")

            # Actualizar spinner
            move_cursor(status_row, spinner_col + 1)
            sys.stdout.write(SPINNER[tick % len(SPINNER)])

            sys.stdout.flush()
            tick += 1
            time.sleep(1)
    except KeyboardInterrupt:
        move_cursor(status_row + 2, 1)
        print("END THERMAL ZONE MONITORING...")


def run_tty_sender(tty_port, baud_rate, zone_to_monitor):
    """Muestra el monitor ANSI y envía la temperatura de una zona a un puerto TTY."""
    # 1. Configurar el puerto usando stty de forma explícita y robusta
    try:
        print(
            f"Configuring {tty_port} to {baud_rate}bps, raw, -echo, clocal, -crtscts..."
        )
        # clocal: Ignora las líneas de control del módem. Esencial para conexiones directas.
        # -crtscts: Desactiva el control de flujo por hardware (RTS/CTS).
        stty_command = [
            "stty",
            "-F",
            tty_port,
            "raw",
            str(baud_rate),
            "-echo",
            "clocal",
            "-crtscts",
        ]
        subprocess.run(
            stty_command,
            check=True,
            capture_output=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(
            f"Error: Failed to configure port using 'stty'. Make sure 'stty' is installed and the port '{tty_port}' exists."
        )
        if isinstance(e, subprocess.CalledProcessError):
            print(f"stty stderr: {e.stderr.decode().strip()}")
        sys.exit(1)

    # 2. Configurar UI y abrir puerto
    try:
        with open(tty_port, "wb", buffering=0) as f:
            # --- Inicio del bloque con variables de UI ---
            sensors = get_thermal_sensors()

            sys.stdout.write("\033[2J\033[H")
            sys.stdout.flush()

            status_line = f"SENDING TO {tty_port} @ {baud_rate}bps"
            draw_static_table(sensors, status_line)

            start_row = 3
            row_map = {s["zone"]: start_row + i for i, s in enumerate(sensors)}
            status_row = start_row + len(sensors) + 1
            spinner_col = len(status_line) + 2
            tick = 0

            HIGHLIGHT = "\033[7m"
            RESET = "\033[0m"

            try:
                # 3. Bucle principal de monitoreo y envío
                while True:
                    sensors = get_thermal_sensors()
                    target_sensor = next(
                        (s for s in sensors if s["zone"] == zone_to_monitor), None
                    )

                    if target_sensor:
                        data_string = (
                            f"{target_sensor['type']}:{target_sensor['temp_c']:.1f}\n"
                        )
                        f.write(data_string.encode("utf-8"))

                    for s in sensors:
                        row = row_map.get(s["zone"])
                        if row:
                            move_cursor(row, TEMP_COL + 1)
                            temp_str = f"{s['temp_c']:>{TEMP_W}.1f}"
                            if s["zone"] == zone_to_monitor:
                                sys.stdout.write(f"{HIGHLIGHT}{temp_str}{RESET}")
                            else:
                                sys.stdout.write(temp_str)

                    move_cursor(status_row, spinner_col + 1)
                    sys.stdout.write(SPINNER[tick % len(SPINNER)])

                    sys.stdout.flush()
                    tick += 1
                    time.sleep(1)

            except KeyboardInterrupt:
                # Mover el cursor debajo de la tabla antes de imprimir el mensaje de salida
                move_cursor(status_row + 2, 1)
                print("\nStopping TTY sender...")
            # --- Fin del bloque con variables de UI ---

    except OSError as e:
        print(f"\nError writing to port {tty_port}: {e}")
        sys.exit(1)
    finally:
        print("Port closed.")


def main():
    parser = argparse.ArgumentParser(
        description="Monitor de temperatura de CPU. Muestra datos en la consola o los envía a un puerto TTY."
    )
    parser.add_argument(
        "--tty",
        type=str,
        help="Puerto serie (TTY) al que enviar los datos. Ej: /dev/ttyUSB0",
    )
    parser.add_argument(
        "--baud",
        type=int,
        default=115200,
        help="Baud rate para la comunicación serie. (default: 115200)",
    )
    parser.add_argument(
        "--zone",
        type=int,
        help="Número de la zona térmica a monitorear (ej: 0 para thermal_zone0).",
    )

    args = parser.parse_args()

    # Si se especifica el puerto TTY y el número de zona, se activa el modo TTY.
    # Se comprueba 'is not None' porque --zone 0 es un valor válido.
    if args.tty and args.zone is not None:
        # Construir el nombre completo de la zona.
        zone_name = f"thermal_zone{args.zone}"
        run_tty_sender(args.tty, args.baud, zone_name)
    else:
        print("No TTY port or zone specified. Running in only terminal mode.")
        print("Use --help for more options.")
        time.sleep(2)
        run_ansi_monitor()


if __name__ == "__main__":
    main()
