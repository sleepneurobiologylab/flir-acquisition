# Arduino TTL Sync

Arduino sketch that generates TTL pulses to hardware-trigger both FLIR cameras and timestamp frames in Open Ephys.

## Sketch

`ttl_pulses/ttl_pulses.ino`

## Wiring

```
Arduino pin 2  ──►  FLIR Cam 1 GPIO trigger input (Line0)
Arduino pin 3  ──►  FLIR Cam 2 GPIO trigger input (Line0)
Arduino pin 4  ──►  Open Ephys digital input channel
Arduino GND    ──►  common ground with cameras and Open Ephys
```

> All three outputs are pulsed simultaneously so a single rising edge appears in
> the Open Ephys recording for every camera frame.

## Configuration

Edit the top of `ttl_pulses.ino` to set:

```cpp
const int FRAME_RATE = 30;   // Hz — must match Bonsai exposure settings
const int PULSE_WIDTH_US = 1000;  // microseconds
```

## Upload

1. Open `ttl_pulses/ttl_pulses.ino` in the Arduino IDE (≥ 2.0)
2. Select your board (e.g., Arduino Uno / Mega)
3. Upload

## Notes

- Pulse timing uses `micros()` for accuracy; avoid adding blocking code to the loop
- The sketch sends a short status byte over Serial at startup so you can confirm it is running
