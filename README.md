# THERMAL ZONE MONITORING

## Descripción

`THERMAL ZONE MONITORING` es una pequeña herramienta de consola para monitorear las temperaturas de los sensores del CPU y otros componentes térmicos en Linux en tiempo real.

Está diseñada para ejecutarse en terminales estándar, usando códigos ANSI para:

*   Actualizar los valores de temperatura sin parpadear
*   Mantener la tabla fija en pantalla
*   Mostrar un spinner animado que indica que el monitoreo está activo

## Características

*   Muestra todas las zonas térmicas detectadas en `/sys/class/thermal/thermal_zone*`
*   Tabla con columnas alineadas: zona, nombre de sensor y temperatura en °C
*   Actualización de la temperatura cada segundo sin parpadear
*   Spinner animado `/ - \ |` indicando actividad
*   Solo depende de Python estándar (sin librerías externas)
*   Compatible con cualquier terminal Linux que soporte códigos ANSI

## Ejemplo de salida

```
ZONE            SENSOR                     TEMP (°C)
----------------------------------------------------
thermal_zone0   acpitz                          27.8
thermal_zone1   acpitz                          29.8
thermal_zone10  iwlwifi_1                       42.0
thermal_zone11  x86_pkg_temp                    45.0
thermal_zone2   INT3400 Thermal                 20.0
thermal_zone3   SEN1                            43.0
thermal_zone4   SEN2                            43.0
thermal_zone5   SEN3                            40.0
thermal_zone6   SEN4                            44.0
thermal_zone7   SEN5                            38.0
thermal_zone8   pch_skylake                     42.5
thermal_zone9   B0D4                            45.0
----------------------------------------------------
THERMAL ZONE MONITORING [ / ]
```

La barra `/` cambia cada segundo, mostrando que la aplicación sigue ejecutándose.

## Cómo funciona

### Lectura de sensores

La aplicación recorre todas las carpetas `/sys/class/thermal/thermal_zone*` y lee los archivos `type` y `temp`.

*   `type` → nombre del sensor
*   `temp` → temperatura en miligrados, convertida a °C

### Impresión de la tabla inicial

La tabla se dibuja solo una vez usando `print()`.

Se reserva espacio para la columna de temperatura y para la línea del spinner.

### Actualización en tiempo real

Se usa un bucle infinito con `time.sleep(1)` para actualizar solo los valores de temperatura y el spinner.

Se usan códigos ANSI (`\033[<row>;<col>H`) para mover el cursor a la posición exacta de cada valor.

Esto evita que toda la pantalla se redibuje, eliminando el parpadeo.

### Spinner animado

La barra `/ - \ |` gira dentro de los corchetes `[...]` cada segundo, indicando que el programa sigue activo.

## Salida

`Ctrl+C` termina el programa de forma limpia.

Se imprime un mensaje END THERMAL ZONE MONITORING...

## Requisitos

*   Linux con `/sys/class/thermal/thermal_zone*` accesible
*   Python 3.x
*   Terminal que soporte códigos ANSI

## Uso

```bash
python3 temp_monitor_ansi.py
```

Opcionalmente, para evitar problemas de buffering:

```bash
python3 -u temp_monitor_ansi.py
```

La aplicación se ejecutará en consola mostrando la tabla de temperaturas y el spinner animado.

## Notas

*   Se puede redirigir la salida a una pantalla externa conectada vía USB, ya que solo usa ASCII y códigos ANSI.
*   La tabla está diseñada para terminales con al menos 80 columnas.