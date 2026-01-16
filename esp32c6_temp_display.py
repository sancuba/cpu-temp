# Este script de MicroPython recibe datos de temperatura a través del puerto USB
# y los muestra en una pantalla ST7789.

import select
import sys
import time

from machine import PWM, SPI, Pin
from neopixel import NeoPixel

import NotoSansMono_32 as font
import st7789py as st7789

WIDTH = 172
HEIGHT = 320
OFFSET_X = 34
OFFSET_Y = 0

LCD_MOSI = 6
LCD_SCK = 7
LCD_CS = 14
LCD_DC = 15
LCD_RESET = 21
LCD_BL = 22
RGB_PIN = 8

# Inicializar SPI y Display
spi = SPI(1, baudrate=12000000, sck=Pin(LCD_SCK), mosi=Pin(LCD_MOSI))
display = st7789.ST7789(
    spi,
    WIDTH,
    HEIGHT,
    reset=Pin(LCD_RESET, Pin.OUT),
    cs=Pin(LCD_CS, Pin.OUT),
    dc=Pin(LCD_DC, Pin.OUT),
    backlight=Pin(LCD_BL, Pin.OUT),
    rotation=1,  # Landscape
    color_order=st7789.BGR,
)

# Inicializar NeoPixel y apagarlo
np = NeoPixel(Pin(RGB_PIN, Pin.OUT), 1)
np[0] = (0, 0, 0)
np.write()

# Configurar brillo del backlight con PWM
bl_pwm = PWM(Pin(LCD_BL))
bl_pwm.freq(1000)
bl_pwm.duty(50)  # Brillo ~5% (0-1023)


def setup_display(zone_name):
    """Dibuja el texto estático una sola vez."""
    display.fill(st7789.BLACK)
    display.write(font, "MONITOR LINUX", 10, 10, st7789.WHITE, st7789.BLACK)
    display.write(font, zone_name.upper(), 10, 50, st7789.CYAN, st7789.BLACK)


def update_temperature(temp_value):
    """Refresca únicamente la línea de la temperatura."""
    # Define el área rectangular donde se escribe la temperatura
    TEMP_X = 10
    TEMP_Y = 90
    # Usamos el ancho completo de la pantalla para asegurarnos de borrar el número anterior
    # sin importar su longitud.
    TEMP_W = display.width - TEMP_X
    TEMP_H = font.HEIGHT

    # Borra solo el rectángulo donde estaba la temperatura anterior
    display.fill_rect(TEMP_X, TEMP_Y, TEMP_W, TEMP_H, st7789.BLACK)

    # Determina el color y si se debe parpadear
    temp_color = st7789.GREEN
    should_blink_red = False
    if temp_value >= 80.0:
        temp_color = st7789.RED
        should_blink_red = True
    elif temp_value >= 60.0:
        temp_color = st7789.YELLOW

    # Escribe el nuevo valor de temperatura en la pantalla
    temp_str = f"{temp_value:.1f} C"
    display.write(font, temp_str, TEMP_X, TEMP_Y, temp_color, st7789.BLACK)

    # Si la temperatura es alta, parpadea en rojo DESPUÉS de actualizar la pantalla.
    if should_blink_red:
        set_led_color(255, 0, 0)
        time.sleep(0.100)
        set_led_color(0, 0, 0)


def show_initial_message():
    """Muestra un mensaje de bienvenida mientras espera datos."""
    display.fill(st7789.BLACK)
    display.write(font, "Sin datos...", 10, 10, st7789.WHITE, st7789.BLACK)


def set_led_color(r, g, b):
    """Establece el color del LED NeoPixel, corrigiendo el orden a GRB."""
    np[0] = (g, r, b)
    np.write()


def main():
    """Bucle principal: lee de USB y actualiza la pantalla."""
    show_initial_message()
    is_display_initialized = False
    # Usamos 'poll' para poder detectar si dejamos de recibir datos.
    poller = select.poll()
    poller.register(sys.stdin, select.POLLIN)

    while True:
        # Esperar datos con un timeout de 3 segundos
        if poller.poll(3000):
            linea = sys.stdin.readline()
            if linea:
                # Apagar el LED al recibir datos
                set_led_color(0, 0, 0)
                try:
                    linea_limpia = linea.strip()
                    partes = linea_limpia.split(":")
                    if len(partes) == 2:
                        zone_name = partes[0]
                        temp_value = float(partes[1])
                        # Si es la primera vez que recibimos datos, dibujamos el fondo estático
                        if not is_display_initialized:
                            setup_display(zone_name)
                            is_display_initialized = True
                        # En cada ciclo, solo actualizamos el valor que cambia
                        update_temperature(temp_value)
                except (ValueError, IndexError) as e:
                    print(f"Dato no válido recibido: {linea.strip()} ({e})")
            else:
                # La conexión se cerró. Parpadear y volver al estado inicial.
                # Se realiza el parpadeo ANTES de actualizar la pantalla para evitar conflictos.
                set_led_color(0, 0, 255)  # Azul
                time.sleep(0.100)
                set_led_color(0, 0, 0)  # Apagado

                show_initial_message()
                is_display_initialized = False
        else:
            # Timeout: no se recibieron datos. Parpadear y volver al estado inicial.
            # Se realiza el parpadeo ANTES de actualizar la pantalla para evitar conflictos.
            set_led_color(0, 0, 255)  # Azul
            time.sleep(0.100)
            set_led_color(0, 0, 0)  # Apagado

            show_initial_message()
            is_display_initialized = False


if __name__ == "__main__":
    main()
