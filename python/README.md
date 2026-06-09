# Python — Frame Synchronization

Scripts for aligning camera frames to Open Ephys Binary recordings using the shared TTL pulse signal.

## How It Works

1. The Arduino fires a TTL pulse for every camera frame
2. Open Ephys records the rising edges of that pulse on a digital input channel
3. `sync_frames.py` reads those timestamps and maps frame index → ephys sample number

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
python sync_frames.py \
    --ephys   /path/to/open-ephys-recording \
    --video   /path/to/frames-or-video \
    --channel TTL_1 \
    --output  sync_table.csv
```

| Argument | Description |
|----------|-------------|
| `--ephys` | Root folder of an Open Ephys Binary recording |
| `--video` | Folder of frame images **or** path to `.avi` file |
| `--channel` | Name of the digital input channel carrying TTL pulses |
| `--output` | Output CSV with columns `frame_idx`, `ephys_sample`, `time_s` |

## Output

`sync_table.csv` contains one row per frame:

```
frame_idx, ephys_sample, time_s
0,         30000,        1.000
1,         31000,        1.033
...
```

## Dependencies

See `requirements.txt`.
