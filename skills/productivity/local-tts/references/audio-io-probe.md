# Audio I/O Probe — TTS vs STT capability check

When a user asks "can Hermes talk now?" or wants to enable voice mode, you need to
determine what their box can actually do before promising anything. This reference
captures the diagnostic recipes that came out of the June 2026 setup session.

## The question has two parts

| Question | What it needs | Diagnostic |
|----------|---------------|------------|
| "Can Hermes speak replies?" | Audio **output** device | `ffplay -nodisp -autoexit <file>.mp3` succeeds |
| "Can I talk to Hermes?" | Audio **input** device (microphone) | `sounddevice.query_devices()` shows ≥1 device with `> 0 in` capture channels |

TTS-only setups work fine on a server, headless workstation, or anywhere with
speakers/HDMI-out. Full voice mode (STT) needs an actual microphone plugged in.

## Probing audio I/O with sounddevice

```python
import sounddevice as sd
for i, dev in enumerate(sd.query_devices()):
    n_in, n_out = dev['max_input_channels'], dev['max_output_channels']
    flag = '*' if i == sd.default.device[0] or i == sd.default.device[1] else ' '
    print(f"{flag} {i:2d} {dev['name']:40s} ({n_in} in, {n_out} out)")
```

Read each row:
- `0 in` = no capture = no microphone on this device
- `>0 in` = has a microphone path (may still need enabling via PulseAudio/PipeWire)
- `*` marker = the system default

### Typical pattern on a Linux workstation without a mic

```
   0 HDA Intel PCH: ALC3246 Analog        (0 in, 4 out)
   1 HDA Intel PCH: HDMI 0                 (0 in, 8 out)
   ...
  11 pipewire                              (64 in, 64 out)
  12 dmix                                  (0 in, 2 out)
* 13 default                               (64 in, 64 out)
```

The `pipewire` / `default` devices show `64 in` because they're virtual sinks;
the `64` is just capacity, not an attached mic. The physical HDA devices at the
top (`0 in`) are what tells you whether a mic is actually wired up.

## Probing audio I/O with `arecord` (CLI fallback)

```bash
arecord -l    # list capture hardware
```

If `arecord -l` shows no cards with capture devices, there's no mic.

## What to do when there's no mic

Honest path: tell the user, then offer alternatives.

- **`text_to_speech` tool** as on-demand audio trigger — works fine, no mic needed
- **Gateway platforms** (Telegram, Discord) — they push voice messages to Hermes
  via the platform's voice input; the user's phone provides the mic, the box
  just runs STT
- **USB mic / headset** — `lsusb` after plugging in should show a new device,
  then re-probe

## What to do when there's no audio output

Less common on Linux, but if `ffplay` reports "No such file or directory" or the
playback is silent:

- `pactl list short sinks` — PulseAudio/PipeWire sinks
- `speaker-test -c 2 -l 1` — generates test tone, will tell you if the speakers
  are wired and the volume isn't muted
- `alsamixer` — interactive volume/mute controls

## Notes from the June 2026 session

- User asked "can you talk now?" after wiring piper. I correctly identified that
  TTS works but no mic was detected on a Linux workstation with only HDA Intel
  outputs.
- User opted for `text_to_speech`-as-trigger mode rather than fixing the mic gap.
- `voice.auto_tts: true` was set so when the user later launches the interactive
  `hermes` CLI with `/voice on`, replies auto-speak (assuming they plug in a mic
  by then).