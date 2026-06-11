# IBL Camera TTL Trigger — Arduino

Sketch de Arduino que genera pulsos TTL periódicos para disparar la captura de la cámara FLIR Chameleon3 a una frecuencia de frames fija. El mismo pulso se registra en Open Ephys como evento digital, lo que permite sincronizar el video con los datos electrofisiológicos.

---

## Funcionamiento

El Arduino genera un pulso TTL en el **pin 13** a la frecuencia definida por `FPS`. Cada pulso dura **500 µs** y queda en LOW el resto del intervalo.

El sketch arranca en estado **detenido** y espera comandos por puerto Serial para iniciar o detener la emisión de pulsos. Esto permite coordinar el inicio de la adquisición con el resto del sistema.

```
Pin 13 ──────┐
             ├──► Cámara FLIR (trigger de hardware)
             └──► Open Ephys (canal digital)
```

---

## Configuración

La única variable que normalmente necesitás cambiar es la frecuencia de frames:

```cpp
float FPS = 60.0;   // frecuencia de disparo en Hz
```

El intervalo entre pulsos se calcula automáticamente como `1.000.000 / FPS` microsegundos.

---

## Conexiones de hardware

| Arduino | Destino |
|---|---|
| Pin 13 | Entrada de trigger de la cámara FLIR |
| Pin 13 | Canal digital de Open Ephys (mismo cable, splitter o BNC-T) |
| GND | GND común con cámara y Open Ephys |

> **Importante:** el pin 13 se conecta en paralelo a la cámara y a Open Ephys. Usá un cable BNC-T o un splitter para dividir la señal. Asegurate de tener GND común entre todos los dispositivos.

---

## Control por Serial

El sketch se controla enviando un carácter por el puerto Serial (9600 baud):

| Comando | Acción |
|---|---|
| `s` | Inicia la emisión de pulsos TTL |
| `p` | Detiene la emisión. El pin queda en LOW. |

Podés enviar los comandos desde el **Serial Monitor** del IDE de Arduino, o desde cualquier script de Python usando `pyserial`:

```python
import serial
import time

arduino = serial.Serial('COM3', 9600, timeout=1)  # ajustar puerto
time.sleep(2)  # esperar inicialización

arduino.write(b's')   # iniciar
# ... adquisición ...
arduino.write(b'p')   # detener
arduino.close()
```

---

## Características técnicas

| Parámetro | Valor |
|---|---|
| Pin de salida | 13 |
| Frecuencia por defecto | 60 Hz |
| Duración del pulso | 500 µs |
| Nivel en reposo | LOW |
| Baud rate Serial | 9600 |
| Temporización | `micros()` — resolución de 4 µs en Arduino Uno/Mega |

> **Nota sobre jitter:** el sketch usa acumulación de tiempo (`lastTriggerTime += interval_us`) en lugar de `lastTriggerTime = now`, lo que evita que el jitter se acumule entre pulsos. En la práctica el jitter es del orden de unos pocos microsegundos.

---

## Compatibilidad

Probado con **Arduino Uno** y **Arduino Mega**. Compatible con cualquier placa que tenga salidas digitales de 5V. Si el trigger de la cámara requiere 3.3V, usá un divisor de tensión o un level shifter.
