# TTL Synchronization — Open Ephys + FLIR Camera

Script de sincronización entre los eventos TTL registrados en **Open Ephys** (formato Binary) y los timestamps de la cámara **FLIR Chameleon3** guardados por Bonsai.

Permite verificar que cada frame de video tiene un TTL correspondiente, cuantificar el jitter de sincronización, y detectar frames perdidos durante la adquisición.

---

## Requisitos

Python 3.8 o superior.

```bash
pip install numpy pandas matplotlib open-ephys-python-tools
```

---

## Archivos de entrada

| Archivo | Descripción |
|---|---|
| Carpeta de recording de Open Ephys | Debe contener `structure.oebin`. Ejemplo: `.../Record Node 104/experiment1/recording1` |
| CSV de timestamps de Bonsai | Generado por el nodo `CsvWriter` en el workflow de Bonsai. Contiene el timestamp de hardware (nanosegundos) y el frame ID. |

---

## Configuración

Antes de correr el script, editá las cuatro variables al inicio del archivo:

```python
OPENEPHYS_DIR  = r"ruta\a\tu\recording"        # carpeta que contiene structure.oebin
TIMESTAMPS_CSV = r"ruta\a\timestamps_cam_1.csv" # CSV generado por Bonsai
TTL_CHANNEL    = 8                              # índice del canal digital del Arduino (0-indexado)
OUTPUT_DIR     = r"ruta\donde\guardar\figuras"  # se crea automáticamente si no existe
```

> **Nota sobre `TTL_CHANNEL`:** en Open Ephys Binary, los canales digitales se indexan desde 0. Si el Arduino está conectado al canal digital 8 del hardware, usá `TTL_CHANNEL = 8`. Verificá con `print(events['line'].unique())` si no estás seguro.

---

## Uso

```bash
python sync_ttl.py
```

El script imprime en consola un resumen del análisis y genera dos archivos en `OUTPUT_DIR`:

- `sincronizacion.png` — figura con 3 paneles de diagnóstico
- `tabla_sincronizacion.csv` — tabla de alineación frame a frame

---

## Salidas

### Consola

- Conteo de TTLs vs frames, con aviso si no coinciden
- Diagnóstico de extremos: primeros y últimos 3 eventos de cada serie
- Jitter de sincronización (media, std, min, max en milisegundos)
- Lista de frames perdidos detectados (si los hay)
- Análisis de intervalos anómalos entre TTLs

### Figura (`sincronizacion.png`)

| Panel | Descripción |
|---|---|
| Panel 1 | Eventos TTL vs timestamps de cámara, alineados en el tiempo |
| Panel 2 | Jitter frame a frame (diferencia cámara − TTL, en ms) |
| Panel 3 | Intervalos entre frames consecutivos, con umbral de detección de frames perdidos |

### Tabla (`tabla_sincronizacion.csv`)

| Columna | Descripción |
|---|---|
| `frame_id` | ID del frame según Bonsai |
| `ttl_time_s` | Tiempo del TTL en Open Ephys (segundos, relativo al primero) |
| `cam_time_s` | Timestamp de la cámara (segundos, relativo al primero) |
| `diferencia_ms` | Diferencia entre cámara y TTL en milisegundos |
| `cam_timestamp_raw` | Timestamp de hardware original en nanosegundos |

---

## Estructura del pipeline

```
Arduino → TTL pulse → Open Ephys (canal digital)
                   ↘
                    Bonsai (trigger de captura) → CSV de timestamps
                                                              ↓
                                                     sync_ttl.py
```

---

## Notas

- El script acepta la ruta directa al recording (la que contiene `structure.oebin`), no necesita apuntar a la sesión completa.
- Los timestamps de Bonsai se normalizan al primer frame (tiempo relativo). Los TTLs de Open Ephys también se normalizan al primer TTL para la comparación.
- Si hay un TTL extra sin frame correspondiente, la función `buscar_ttl_extra()` analiza los intervalos para localizar si el desfase está al inicio o al final del registro.
- El umbral de detección de frames perdidos es 1.8× el intervalo mediano entre frames. Ajustarlo en la función `comparar_sincronizacion()` si el sistema corre a frecuencias inusuales.
