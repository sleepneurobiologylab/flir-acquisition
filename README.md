# flir-acquisition

Dual-camera video acquisition system for neuroscience experiments using FLIR Chameleon3 USB3 cameras.

## System Overview

```
┌─────────────────┐     TTL pulses      ┌─────────────┐
│     Arduino     │ ──────────────────► │  FLIR Cam 1 │
│  (sync source)  │                     │  Chameleon3 │
│                 │ ──────────────────► │  FLIR Cam 2 │
└─────────────────┘                     └─────────────┘
        │                                      │
        │ TTL to Open Ephys                    │ USB3
        ▼                                      ▼
┌─────────────────┐               ┌────────────────────┐
│   Open Ephys    │               │       Bonsai        │
│ Binary format   │               │ SpinnakerCapture    │
└─────────────────┘               │     workflows       │
        │                         └────────────────────┘
        │                                  │
        └──────────────────────────────────┘
                        │
                        ▼
             ┌─────────────────┐
             │  Python sync    │
             │    script       │
             └─────────────────┘
```

## Components

### Cameras
- 2× [FLIR Chameleon3 CM3-U3-13Y3M](https://www.flir.com/products/chameleon3-usb3/) — USB3 monochrome cameras
- Triggered via hardware TTL from Arduino
- Captured in Bonsai using `Spinnaker` source nodes (`SpinnakerCapture`)

### Bonsai
- Workflows in [`bonsai/workflows/`](bonsai/workflows/) handle dual-camera capture
- Both cameras run in hardware-trigger mode, so each frame is time-locked to an Arduino pulse
- Video saved as `.avi` or raw frame sequences depending on workflow

### Arduino
- Sketch in [`arduino/ttl_pulses/`](arduino/ttl_pulses/) generates TTL pulses at a configurable frame rate
- Pulses are sent simultaneously to both camera trigger inputs and to an Open Ephys digital input channel
- This common signal is what allows post-hoc frame↔ephys alignment

### Python
- Scripts in [`python/`](python/) synchronize camera frames to Open Ephys Binary recordings
- Uses the TTL timestamps recorded by Open Ephys to assign each video frame an exact ephys sample index
- See [`python/README.md`](python/README.md) for usage

### Docs
- Additional wiring diagrams, setup notes, and calibration procedures in [`docs/`](docs/)

## Quick Start

1. **Hardware** — wire Arduino TTL output to both camera trigger pins and to an Open Ephys digital input
2. **Bonsai** — open the workflow in `bonsai/workflows/`, set camera serial numbers, and press Play
3. **Arduino** — upload `arduino/ttl_pulses/ttl_pulses.ino` and set `FRAME_RATE` to match Bonsai
4. **Open Ephys** — start recording; the TTL channel will log every frame trigger
5. **Post-hoc sync** — run `python/sync_frames.py` pointing at the video folder and Open Ephys recording

## Requirements

| Component | Version |
|-----------|---------|
| Bonsai | ≥ 2.8 |
| Bonsai.Spinnaker | latest |
| Arduino IDE | ≥ 2.0 |
| Python | ≥ 3.9 |
| Spinnaker SDK | ≥ 3.x |

See [`python/requirements.txt`](python/requirements.txt) for Python dependencies.

## Repository Structure

```
flir-acquisition/
├── README.md               # this file
├── .gitignore
├── bonsai/
│   ├── workflows/          # .bonsai workflow files
│   └── README.md
├── arduino/
│   ├── ttl_pulses/         # Arduino sketch for TTL sync
│   └── README.md
├── python/
│   ├── README.md
│   └── requirements.txt
└── docs/                   # wiring diagrams, setup notes
```

## License

MIT
