# Este script de MicroPython recibe datos de temperatura a través del puerto USB
# y los muestra en una pantalla ST7789.

import sys
import time

from machine import PWM, SPI, Pin

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

    # Determina el color basado en el valor
    temp_color = st7789.GREEN
    if temp_value >= 80.0:
        temp_color = st7789.RED
    elif temp_value >= 60.0:
        temp_color = st7789.YELLOW

    # Escribe el nuevo valor de temperatura
    temp_str = f"{temp_value:.1f} C"
    display.write(font, temp_str, TEMP_X, TEMP_Y, temp_color, st7789.BLACK)


def show_initial_message():
    """Muestra un mensaje de bienvenida mientras espera datos."""
    display.fill(st7789.BLACK)
    display.write(font, "Sin datos...", 10, 10, st7789.WHITE, st7789.BLACK)


def main():
    """Bucle principal: lee de USB y actualiza la pantalla."""
    show_initial_message()
    is_display_initialized = False
    while True:
        linea = sys.stdin.readline()
        if linea:
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
        time.sleep(0.1)


if __name__ == "__main__":
    main()
