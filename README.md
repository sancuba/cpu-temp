# THERMAL ZONE MONITORING

## Descripción

`THERMAL ZONE MONITORING` es una herramienta de consola para monitorear las temperaturas de los sensores de la CPU en Linux. Además del monitoreo en la consola, ahora puede **enviar los datos de una zona térmica específica a un microcontrolador externo**, como un ESP32-C6, para ser mostrados en su pantalla LCD.

Utiliza códigos ANSI para una visualización limpia en la terminal y un protocolo simple de texto para la comunicación serie.

## Modos de Operación

1.  **Modo de Monitoreo en Consola:** Muestra una tabla con todas las zonas térmicas que se actualiza en tiempo real en la terminal.
2.  **Modo TTY Sender:** Envía los datos de una zona específica a un puerto serie (TTY), permitiendo la integración con hardware externo.

---

## Modo de Monitoreo en Consola

Esta es la funcionalidad original de la herramienta.

### Ejemplo de Salida

```
ZONE            SENSOR                     TEMP (°C)
----------------------------------------------------
thermal_zone0   acpitz                          27.8
thermal_zone1   acpitz                          29.8
thermal_zone10  iwlwifi_1                       42.0
thermal_zone11  x86_pkg_temp                    45.0
----------------------------------------------------
THERMAL ZONE MONITORING [ / ]
```

### Características

*   Muestra todas las zonas térmicas detectadas en `/sys/class/thermal/thermal_zone*`.
*   Tabla con columnas alineadas y actualización sin parpadeo.
*   Spinner animado (`/ - \ |`) que indica actividad.
*   Compatible con cualquier terminal Linux que soporte códigos ANSI.

### Uso

```bash
python3 linux_temp_monitor.py
```
La aplicación se ejecutará mostrando la tabla de temperaturas en la consola.

---

## Modo TTY Sender (Envío a ESP32-C6)

Esta nueva capacidad permite visualizar la temperatura de una zona de la CPU de tu PC en una pantalla LCD conectada a un ESP32-C6.

El sistema consta de dos componentes:
*   **Emisor (PC Linux):** El script `linux_temp_monitor.py` se ejecuta con parámetros especiales para enviar datos.
*   **Receptor (ESP32-C6):** El script `esp32c6_temp_display.py` recibe los datos por USB y los muestra en la pantalla.

### Componente 1: `linux_temp_monitor.py` (Emisor)

Al ejecutarse en modo TTY, el script monitorea la consola como siempre, pero con dos cambios visuales importantes:
*   La zona térmica seleccionada para el envío **aparecerá resaltada** en la tabla.
*   La línea de estado en la parte inferior cambiará para indicar el envío, por ejemplo: `SENDING TO /dev/ttyACM0 @ 115200bps [|]`.

Esto permite ver toda la información en el PC y, al mismo tiempo, tener la confirmación de qué datos se están enviando al microcontrolador.

#### Parámetros
*   `--tty PUERTO`: El puerto serie al que se conectará (ej. `/dev/ttyACM0`).
*   `--zone NUMERO`: El número de la zona térmica a enviar (ej. `0` para `thermal_zone0`).
*   `--baud VELOCIDAD`: El baud rate para la comunicación (default: `115200`).

#### Ejemplo de Uso
```bash
python3 linux_temp_monitor.py --tty /dev/ttyACM0 --zone 0
```

### Componente 2: `esp32c6_temp_display.py` (Receptor)

Este script de MicroPython se ejecuta en el ESP32-C6. Inicializa la pantalla ST7789, se queda esperando datos por el puerto USB y actualiza la temperatura en la pantalla de forma optimizada (sin parpadeo).

#### Archivos Requeridos en el ESP32-C6
1.  `esp32c6_temp_display.py` (script principal)
2.  `st7789py.py` (driver de la pantalla)
3.  `NotoSansMono_32.py` (fuente para el texto)

### Firmware MicroPython para ESP32-C6

Antes de poder cargar los scripts, la placa debe tener el firmware de MicroPython. Puedes descargarlo y encontrar las instrucciones de instalación (que usualmente implican usar `esptool.py`) en el sitio oficial:

*   **[Descargar Firmware para ESP32-C6 Genérico](https://micropython.org/download/ESP32_GENERIC_C6/)**

### Guía de Inicio Rápido (Linux + ESP32-C6)

Sigue estos pasos para poner todo el sistema en funcionamiento:

**1. Instala `mpremote` en tu PC:**
`mpremote` es la herramienta oficial de MicroPython para interactuar con la placa.
```bash
pip install mpremote
```

**2. Carga los archivos al ESP32-C6:**
Conecta tu placa. Luego, usa `mpremote` para copiar los archivos necesarios. Renombraremos `esp32c6_temp_display.py` a `main.py` para que se ejecute automáticamente al iniciar la placa.

```bash
# Reemplaza /dev/ttyACM0 por tu puerto si es diferente
mpremote connect /dev/ttyACM0 fs cp esp32c6_temp_display.py :main.py
mpremote fs cp st7789py.py :
mpremote fs cp NotoSansMono_32.py :
```

**3. Reinicia el ESP32-C6:**
Usa `mpremote` para reiniciar la placa y ejecutar el nuevo `main.py`.
```bash
mpremote reset
```
Después de reiniciar, la pantalla del ESP32-C6 debería mostrar "Esperando datos...".

**4. Inicia el emisor en Linux:**
Ejecuta el script de monitoreo en tu PC, apuntando al puerto de la placa.
```bash
# Asegúrate de que --zone y --tty sean los correctos
python3 linux_temp_monitor.py --tty /dev/ttyACM0 --zone 0
```

**5. ¡Listo!**
Ahora deberías ver la temperatura de la zona 0 en la pantalla de tu ESP32-C6, actualizándose cada segundo.

## Requisitos Generales

*   Linux con `/sys/class/thermal/thermal_zone*` accesible.
*   Python 3.x.
*   Para el modo TTY:
    *   Placa ESP32-C6 (u otra compatible con MicroPython).
    *   Pantalla LCD ST7789.
    *   `mpremote` instalado (`pip install mpremote`).

---

## Agradecimientos

*   Un agradecimiento especial a **Russ Hughes** por su excelente librería `st7789py` para MicroPython, que sirvió como base para el driver de la pantalla. El proyecto original se encuentra en:
    *   [russhughes/st7789py_mpy en GitHub](https://github.com/russhughes/st7789py_mpy/)
*   **Nota:** La versión de la librería incluida en este proyecto fue modificada para añadir soporte para la resolución nativa (172x320) de la placa Waveshare ESP32-C6 Display 1.47.