# -*- coding: utf-8 -*-
"""
Created on Thu Jun  4 16:13:48 2026

@author: Diego
"""

"""
Script de sincronización EEG + Video
=====================================
Compara los TTL registrados en Open Ephys (Binary format)
con los timestamps de la cámara FLIR guardados por Bonsai.

Requiere:
    pip install numpy pandas matplotlib open-ephys-python-tools
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from open_ephys.analysis import Session


# =============================================================================
# CONFIGURACIÓN — editá estas rutas antes de correr el script
# =============================================================================

OPENEPHYS_DIR   = r"Z:\Cavelli\IBL\M2\M2\2026-05-29_14-25-55\Record Node 104\experiment1\recording2"        # carpeta raíz de Open Ephys (contiene structure.oebin)
TIMESTAMPS_CSV  = r"Z:\Cavelli\IBL\M2\exp 29.05.26\rec 2\timestamps_cam_1.csv"  # CSV generado por Bonsai
TTL_CHANNEL     = 8                            # índice del canal digital donde entra el TTL del Arduino (0 = primero)
OUTPUT_DIR      = r"C:\datos\figuras"          # carpeta donde se guardan las figuras (se crea si no existe)

# =============================================================================


def cargar_ttl_openephys(openephys_dir, ttl_channel=TTL_CHANNEL):
    """
    Carga los eventos TTL del canal digital desde un recording de Open Ephys
    en formato Binary. Acepta la ruta directa al recording (la que contiene
    structure.oebin) o a la sesión completa.
    """
    from open_ephys.analysis.formats.BinaryRecording import BinaryRecording
    import os

    print("Cargando datos de Open Ephys...")

    # Si la ruta contiene structure.oebin, la cargamos directamente
    if os.path.exists(os.path.join(openephys_dir, 'structure.oebin')):
        print(f"  Cargando recording directamente desde: {openephys_dir}")
        recording = BinaryRecording(openephys_dir, experiment_index=0, recording_index=0)
    else:
        # Fallback al método original
        session = Session(openephys_dir)
        recording = session.recordnodes[0].recordings[0]

    # Eventos TTL
    events = recording.events
    print(f"  Columnas disponibles en eventos: {list(events.columns)}")

    # Filtramos flancos ascendentes (state == 1) del canal indicado
    ttl = events[(events['line'] == ttl_channel) & (events['state'] == 1)].copy()
    ttl_times = ttl['timestamp'].values

    print(f"  TTLs encontrados: {len(ttl_times)}")
    if len(ttl_times) > 0:
        print(f"  Duración del registro: {ttl_times[-1] - ttl_times[0]:.2f} s")
    return ttl_times


def cargar_timestamps_camara(csv_path):
    """
    Carga el CSV de timestamps generado por Bonsai.
    Convierte el timestamp de hardware (nanosegundos) a segundos relativos.
    """
    print("\nCargando timestamps de la cámara...")
    df = pd.read_csv(csv_path)
    print(f"  Columnas encontradas: {list(df.columns)}")

    # Bonsai puede nombrar la columna de distintas maneras — buscamos la que corresponde
    posibles_ts = [c for c in df.columns if 'timestamp' in c.lower() or 'item1' in c.lower()]
    posibles_id = [c for c in df.columns if 'frame' in c.lower() or 'item2' in c.lower()]

    col_ts = posibles_ts[0] if posibles_ts else df.columns[0]
    col_id = posibles_id[0] if posibles_id else df.columns[1]

    print(f"  Usando columna timestamp: '{col_ts}'")
    print(f"  Usando columna frame ID:  '{col_id}'")

    ts_raw = df[col_ts].values.astype(np.int64)
    frame_ids = df[col_id].values.astype(np.int64)

    # Convertir a segundos relativos al primer frame
    ts_seconds = (ts_raw - ts_raw[0]) / 1e9

    print(f"  Frames registrados: {len(ts_seconds)}")
    print(f"  Duración del video: {ts_seconds[-1]:.2f} s")
    return ts_seconds, frame_ids, ts_raw


def comparar_sincronizacion(ttl_times, cam_times, frame_ids):
    """
    Compara TTLs de Open Ephys con timestamps de la cámara.
    Detecta frames perdidos y calcula el jitter de sincronización.
    """
    print("\n" + "="*50)
    print("ANÁLISIS DE SINCRONIZACIÓN")
    print("="*50)

    n_ttl    = len(ttl_times)
    n_frames = len(cam_times)

    print(f"\nTTLs en Open Ephys : {n_ttl}")
    print(f"Frames en cámara   : {n_frames}")
    print(f"Diferencia         : {abs(n_ttl - n_frames)}")

    if n_ttl == n_frames:
        print("✓ Conteo de frames y TTLs coincide perfectamente.")
    else:
        print("⚠ El conteo NO coincide — hay frames perdidos o TTLs sin capturar.")

    # ------------------------------------------------------------------
    # NUEVO: Diagnóstico de extremos para identificar dónde está el desfase
    # ------------------------------------------------------------------
    print("\n--- Diagnóstico de extremos ---")

    # Normalizamos ambas series al primer evento de cada una
    ttl_rel_all = ttl_times - ttl_times[0]
    cam_rel_all = cam_times  # ya viene normalizada

    # Primeros 3 eventos
    print("\nPrimeros 3 eventos (tiempo relativo al primero de cada serie):")
    print(f"{'idx':<5}{'TTL (s)':<15}{'Frame (s)':<15}{'Diferencia (ms)':<15}")
    for i in range(min(3, n_ttl, n_frames)):
        diff_ms = (cam_rel_all[i] - ttl_rel_all[i]) * 1000
        print(f"{i:<5}{ttl_rel_all[i]:<15.6f}{cam_rel_all[i]:<15.6f}{diff_ms:<15.3f}")

    # Últimos 3 eventos
    print("\nÚltimos 3 eventos (tiempo relativo al primero de cada serie):")
    print(f"{'idx':<5}{'TTL (s)':<15}{'Frame (s)':<15}{'Diferencia (ms)':<15}")
    n_show = min(3, n_ttl, n_frames)
    for i in range(n_show):
        idx_ttl = n_ttl - n_show + i
        idx_cam = n_frames - n_show + i
        diff_ms = (cam_rel_all[idx_cam] - ttl_rel_all[idx_ttl]) * 1000
        print(f"{idx_ttl:<5}{ttl_rel_all[idx_ttl]:<15.6f}{cam_rel_all[idx_cam]:<15.6f}{diff_ms:<15.3f}")

    # Resumen del extremo donde está el desfase
    if n_ttl != n_frames:
        if n_ttl > n_frames:
            extra = n_ttl - n_frames
            print(f"\n→ Hay {extra} TTL(s) extra en Open Ephys que no tienen frame correspondiente.")
            print(f"  TTL extra al inicio: t = {ttl_rel_all[0]:.6f} s")
            print(f"  TTL extra al final:  t = {ttl_rel_all[-1]:.6f} s")
            print(f"  Último frame:         t = {cam_rel_all[-1]:.6f} s")
        else:
            extra = n_frames - n_ttl
            print(f"\n→ Hay {extra} frame(s) extra en la cámara que no tienen TTL correspondiente.")
    print()

    # ------------------------------------------------------------------
    # Alineación: tomamos el mínimo de ambos para comparar 1 a 1
    # ------------------------------------------------------------------
    n = min(n_ttl, n_frames)

    # Normalizamos ambas series al primer evento
    ttl_rel = ttl_times[:n] - ttl_times[0]
    cam_rel = cam_times[:n]

    diferencias_ms = (cam_rel - ttl_rel) * 1000  # en milisegundos

    print(f"Jitter de sincronización (primeros {n} frames):")
    print(f"  Media  : {diferencias_ms.mean():.3f} ms")
    print(f"  Std    : {diferencias_ms.std():.3f} ms")
    print(f"  Mínimo : {diferencias_ms.min():.3f} ms")
    print(f"  Máximo : {diferencias_ms.max():.3f} ms")

    # ------------------------------------------------------------------
    # Detección de frames perdidos
    # ------------------------------------------------------------------
    intervalos_cam = np.diff(cam_times) * 1000   # ms entre frames consecutivos
    intervalo_esperado = np.median(intervalos_cam)
    umbral = intervalo_esperado * 1.8             # si el intervalo supera 1.8x el normal, hubo salto

    frames_perdidos_idx = np.where(intervalos_cam > umbral)[0]

    if len(frames_perdidos_idx) == 0:
        print("\n✓ No se detectaron frames perdidos.")
    else:
        print(f"\n⚠ Se detectaron {len(frames_perdidos_idx)} posibles frames perdidos:")
        for idx in frames_perdidos_idx:
            t = cam_times[idx]
            gap = intervalos_cam[idx]
            frames_faltantes = round(gap / intervalo_esperado) - 1
            print(f"   → Entre frame {frame_ids[idx]} y {frame_ids[idx+1]} "
                  f"(t={t:.3f}s, gap={gap:.1f}ms, ~{frames_faltantes} frames faltantes)")

    return diferencias_ms, intervalos_cam, frames_perdidos_idx, intervalo_esperado

def graficar(ttl_times, cam_times, diferencias_ms, intervalos_cam,
             frames_perdidos_idx, intervalo_esperado, output_dir):
    """Genera y guarda 3 figuras de diagnóstico."""

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    n = len(diferencias_ms)

    fig, axes = plt.subplots(3, 1, figsize=(14, 10))
    fig.suptitle("Diagnóstico de sincronización EEG + Cámara", fontsize=14, fontweight='bold')

    # --- Panel 1: TTL vs timestamps de cámara ---
    ax = axes[0]
    ax.plot(ttl_times[:n] - ttl_times[0], np.ones(n) * 1, '|', color='steelblue',
            markersize=10, label='TTL Open Ephys')
    ax.plot(cam_times[:n], np.ones(n) * 0.5, '|', color='tomato',
            markersize=10, label='Timestamp cámara')
    ax.set_yticks([0.5, 1])
    ax.set_yticklabels(['Cámara', 'Open Ephys'])
    ax.set_xlabel('Tiempo (s)')
    ax.set_title('Eventos TTL vs Timestamps de cámara')
    ax.legend(loc='upper right')
    ax.grid(axis='x', alpha=0.3)

    # --- Panel 2: Diferencia (jitter) frame a frame ---
    ax = axes[1]
    ax.plot(cam_times[:n], diferencias_ms, color='purple', linewidth=0.8)
    ax.axhline(0, color='black', linewidth=0.5, linestyle='--')
    ax.fill_between(cam_times[:n], diferencias_ms, alpha=0.2, color='purple')
    ax.set_xlabel('Tiempo (s)')
    ax.set_ylabel('Diferencia (ms)')
    ax.set_title('Jitter de sincronización (cámara − TTL)')
    ax.grid(alpha=0.3)

    # --- Panel 3: Intervalos entre frames (detección de frames perdidos) ---
    ax = axes[2]
    ax.plot(cam_times[1:], intervalos_cam, color='teal', linewidth=0.8, label='Intervalo entre frames')
    ax.axhline(intervalo_esperado, color='green', linestyle='--', linewidth=1, label='Intervalo esperado')
    ax.axhline(intervalo_esperado * 1.8, color='red', linestyle='--', linewidth=1, label='Umbral frame perdido')

    if len(frames_perdidos_idx) > 0:
        ax.scatter(cam_times[frames_perdidos_idx + 1], intervalos_cam[frames_perdidos_idx],
                   color='red', zorder=5, s=40, label='Frame perdido detectado')

    ax.set_xlabel('Tiempo (s)')
    ax.set_ylabel('Intervalo (ms)')
    ax.set_title('Intervalos entre frames consecutivos')
    ax.legend(loc='upper right')
    ax.grid(alpha=0.3)

    plt.tight_layout()
    ruta = str(Path(output_dir) / "sincronizacion.png")
    #plt.savefig(ruta, dpi=150, bbox_inches='tight')
    #print(f"\nFigura guardada en: {ruta}")
    plt.show()

def buscar_ttl_extra(ttl_times, cam_times, frame_ids):
    """
    Encuentra el/los TTL(s) que no tienen frame correspondiente.
    Compara los intervalos entre TTLs vs intervalos entre frames.
    """
    print("\n" + "="*50)
    print("BÚSQUEDA DE TTL EXTRA")
    print("="*50)

    if len(ttl_times) == len(cam_times):
        print("No hay TTL extra — los conteos coinciden.")
        return

    # Normalizamos al primer evento de cada serie
    ttl_rel = ttl_times - ttl_times[0]
    cam_rel = cam_times.copy()

    # Intervalos entre eventos consecutivos
    intervalos_ttl = np.diff(ttl_rel) * 1000  # ms
    intervalos_cam = np.diff(cam_rel) * 1000  # ms

    # Intervalo esperado (mediana del más frecuente)
    intervalo_esperado = np.median(intervalos_cam)
    print(f"Intervalo esperado entre eventos: {intervalo_esperado:.3f} ms")

    # Buscamos en TTLs algún intervalo anómalo (más corto o más largo de lo normal)
    umbral_corto = intervalo_esperado * 0.5
    umbral_largo = intervalo_esperado * 1.5

    print(f"\nIntervalos anómalos en TTLs (fuera de [{umbral_corto:.1f}, {umbral_largo:.1f}] ms):")
    encontrados = 0
    for i, intervalo in enumerate(intervalos_ttl):
        if intervalo < umbral_corto or intervalo > umbral_largo:
            print(f"  TTL[{i}] → TTL[{i+1}]: intervalo = {intervalo:.3f} ms "
                  f"(en t = {ttl_rel[i]:.3f} s)")
            encontrados += 1
            if encontrados >= 10:
                print("  ... (mostrando solo los primeros 10)")
                break

    if encontrados == 0:
        print("  Ningún intervalo anómalo. El TTL extra puede estar al inicio o al final.")

    # Comparar primer y último TTL con primer y último frame
    print(f"\n--- Comparación primer/último evento ---")
    print(f"Primer TTL absoluto:    {ttl_times[0]:.6f} s")
    print(f"Primer frame absoluto:  {cam_times[0]:.6f} s (relativo: {cam_rel[0]:.6f})")
    print(f"Último TTL relativo:    {ttl_rel[-1]:.6f} s")
    print(f"Último frame relativo:  {cam_rel[-1]:.6f} s")

    # Lógica: si los intervalos al inicio coinciden bien, el extra está al final
    print(f"\n--- Análisis posicional ---")
    print(f"Primer intervalo TTL:   {intervalos_ttl[0]:.3f} ms")
    print(f"Primer intervalo frame: {intervalos_cam[0]:.3f} ms")
    print(f"Último intervalo TTL:   {intervalos_ttl[-1]:.3f} ms")
    print(f"Último intervalo frame: {intervalos_cam[-1]:.3f} ms")
    
    
# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":

    # 1. Cargar datos
    ttl_times              = cargar_ttl_openephys(OPENEPHYS_DIR, TTL_CHANNEL)
    cam_times, frame_ids, ts_raw = cargar_timestamps_camara(TIMESTAMPS_CSV)

    # 2. Comparar
    diferencias_ms, intervalos_cam, frames_perdidos_idx, intervalo_esperado = \
        comparar_sincronizacion(ttl_times, cam_times, frame_ids)

    # 3. Graficar
    graficar(ttl_times, cam_times, diferencias_ms, intervalos_cam,
             frames_perdidos_idx, intervalo_esperado, OUTPUT_DIR)

    # 4. Exportar tabla de alineación
    n = min(len(ttl_times), len(cam_times))
    tabla = pd.DataFrame({
        'frame_id'        : frame_ids[:n],
        'ttl_time_s'      : ttl_times[:n] - ttl_times[0],
        'cam_time_s'      : cam_times[:n],
        'diferencia_ms'   : diferencias_ms,
        'cam_timestamp_raw': ts_raw[:n],
    })
    ruta_tabla = str(Path(OUTPUT_DIR) / "tabla_sincronizacion.csv")
    tabla.to_csv(ruta_tabla, index=False)
    print(f"Tabla de alineación guardada en: {ruta_tabla}")
    
    buscar_ttl_extra(ttl_times, cam_times, frame_ids)