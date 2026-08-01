---
name: local-tts
description: "Use when the user wants offline / local / no-API-key text-to-speech via Hermes — install a local neural TTS engine (piper, kittentts, neutts), wire it into tts.provider, and verify it actually produces audio end-to-end."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [tts, voice, audio, piper, local, hermes-config]
    related_skills: [hermes-agent]
---

# Local TTS in Hermes

## Overview

Hermes ships three **built-in** local neural TTS providers — `piper`, `kittentts`, `neutts` — alongside cloud providers (`edge`, `openai`, `elevenlabs`, `xai`, `minimax`, `gemini`, `mistral`). Switching to local means no API keys, no per-character cost, full offline operation. This skill covers the install → wire → verify path that actually works on a fresh machine.

The default config wires `edge` (Microsoft's free public endpoint — best quality-to-friction ratio when online). Local is the right choice when the user is offline, cost-sensitive, privacy-bound, or just wants the box to speak without a network.

## When to Use

- User asks for "voice mode," "voice response," "text to speech," "make Hermes talk," "local TTS," "offline TTS"
- User wants to drop an API key or stop paying per character
- User is on a plane / locked-down network / behind a strict firewall
- User wants to evaluate a local neural engine before committing to a paid tier

Don't use for:
- Browser-side speech (that's the OS/browser TTS, not Hermes)
- Voice *input* (STT) — that's a separate `stt` provider path in config.yaml
- Music or sound-effect generation — use `comfyui` / `audiocraft` skills

## Provider Picker

| Provider | Engine        | Install              | First-run model                   | Quality      | Speed (CPU) |
|----------|---------------|----------------------|-----------------------------------|--------------|-------------|
| `piper`  | piper1-gpl    | `pip install piper-tts` in project venv | Auto-downloads from HF, or point at a pre-downloaded `.onnx` | High (neural) | Fast        |
| `kittentts` | KittenTTS  | `pip install kittentts`              | Bundled nano model                  | Medium       | Very fast   |
| `neutts` | NeuTTS Air (gguf) | `pip install neutts-air`         | Bundled q4 gguf                    | High (with ref audio) | Slower |

Default to `piper` unless the user already has a preference — it has the largest voice catalog and cleanest first-run UX.

## Procedure

### 1. Confirm a venv exists

Hermes refuses system-wide pip on PEP 668 systems (Ubuntu 24.04, Debian 12+, Fedora). Install into the project venv:

```bash
cd {hermes_home}/hermes-agent   # or wherever the checkout lives
source venv/bin/activate             # use .venv if that's what your checkout has
```

Probe with `which python` — if it points at `/usr/bin/python3`, you forgot to activate.

### 2. Install the engine

```bash
pip install piper-tts        # for piper
# pip install kittentts      # for kittentts
# pip install neutts-air     # for neutts
```

Piper's wheel pulls `onnxruntime` (~80MB) and `ctranslate2` (~150MB). Allow a minute on first install.

### 3. Pre-download a voice (skip the auto-fetch)

The first real TTS call will otherwise try to fetch a ~15–65MB ONNX from HuggingFace. In a sandboxed / firewalled / CI box that fetch fails silently. Pre-stage to `~/.hermes/tts/piper/`:

```bash
mkdir -p ~/.hermes/tts/piper
cd ~/.hermes/tts/piper
curl -sL -o en_US-amy-low.onnx \
  "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/low/en_US-amy-low.onnx"
curl -sL -o en_US-amy-low.onnx.json \
  "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/low/en_US-amy-low.onnx.json"
```

Voice catalog: https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/VOICES.md
Tradeoff: `low` ~15MB / real-time on any CPU · `medium` ~60MB / noticeably better · `high` ~120MB / overkill for CLI banter.

### 4. Sanity-check the binary before wiring Hermes

Catches venv mistakes and missing wheels fast:

```bash
cd ~/.hermes/tts/piper
echo "Voice mode is working on Hermes." | piper \
  --model en_US-amy-low.onnx \
  --output_file /tmp/piper_test.wav
file /tmp/piper_test.wav
# expect: RIFF ... WAVE audio, ... 16 bit, mono 16000 Hz
```

If `piper: command not found` — you didn't activate the venv. If it installs but bails on model load — the `.onnx.json` sidecar is missing or mismatched.

### 5. Wire Hermes — via the CLI, not direct edit

`patch`/`write_file` will refuse to touch `~/.hermes/config.yaml` (security guard). Use the config CLI:

```bash
source venv/bin/activate
python -m hermes_cli.main config set tts.provider piper
python -m hermes_cli.main config set tts.piper.voice {hermes_home}/tts/piper/en_US-amy-low.onnx
# optional: speed tweak
python -m hermes_cli.main config set tts.piper.length_scale 1.0
```

The full config schema lives at `hermes_cli/config.py` `~line 1895-1952` — that's where every supported `tts.<provider>` option is documented inline.

### 6. Verify end-to-end through Hermes's tool

Don't trust the config write alone — actually invoke the tool the agent uses:

```bash
source venv/bin/activate
python -c "
import os
os.environ.setdefault('HERMES_HOME', os.path.expanduser('~/.hermes'))
from tools.tts_tool import text_to_speech_tool
print(text_to_speech_tool('Voice mode is working on Hermes with local Piper TTS.'))
"
```

Success looks like:
```json
{"success": true, "file_path": "{hermes_home}/cache/audio/tts_*.mp3", "provider": "piper"}
```

`voice_compatible: false` in the response is normal for local providers — it's a hint for voice-input parity, not a failure.

### 7. Try it in voice mode

Run `hermes --voice` or trigger voice mode from the gateway. If you hear nothing, check:
- `~/.hermes/cache/audio/` for the most recent file — exists means synthesis worked, problem is playback
- `ffplay -nodisp -autoexit <file>.mp3` plays the MP3 with one line and exits cleanly (best for headless verification — no GUI needed)
- `paplay` / `aplay` can play the .mp3 directly to confirm
- `display_hermes_home()` in error messages — confirms the profile-aware path was used

## Voice Quality Upgrades

After the basic setup works, iterate on quality:

1. **Switch voice** — `tts.piper.voice` accepts an absolute path to any `.onnx`. Swap `en_US-amy-low.onnx` for `en_US-lessac-medium.onnx` and notice the difference.
2. **Tune prosody** — `length_scale` (1.0 default, 1.2 = slower/more deliberate, 0.9 = snappier), `noise_scale` (0.667 default), `noise_w_scale` (0.8 default).
3. **Multi-language** — Piper has 30+ languages. Spanish: `es_ES-davefx-medium.onnx`. French: `fr_FR-siwis-medium.onnx`. German: `de_DE-thorsten-medium.onnx`.
4. **GPU** — install `onnxruntime-gpu` instead of `onnxruntime`, then set `tts.piper.use_cuda: true`. Real-time even on `high` voices.

## Common Pitfalls

1. **PEP 668 / system pip.** Ubuntu 24.04+ refuses `pip install` into the system Python. Always `source venv/bin/activate` first — `which pip` should point inside `venv/`.

2. **Forgot to activate the venv.** `piper: command not found` after install. Symptom of installing in one shell, running in another. Re-activate.

3. **`patch` refuses to edit `~/.hermes/config.yaml`.** That's a guard, not a bug. Use `python -m hermes_cli.main config set <dotted.key> <value>` instead.

4. **Auto-download hangs / fails silently.** First synthesis needs network for the model. In a locked-down env, pre-download with `curl` (step 3) or point `tts.piper.voice` at a local file.

5. **Missing `.onnx.json` sidecar.** Piper needs both files — the ONNX weights AND the config JSON. Download them in pairs.

6. **Importing `text_to_speech` from `tools.tts_tool`.** The tool's public symbol is `text_to_speech_tool`, not `text_to_speech`. Easy mistake — `registry.register(name="text_to_speech", handler=lambda args, **kw: text_to_speech_tool(...))` exposes the public name but the function lives as `text_to_speech_tool`.

7. **`HERMES_HOME` not set in ad-hoc scripts.** Hermes dispatches via `os.environ['HERMES_HOME']`. If you `python -c "..."` without setting it (and you're on a profile that doesn't have it pinned), the config loads from the wrong home and your `tts.provider: piper` setting looks like it didn't take. Always set `os.environ.setdefault('HERMES_HOME', os.path.expanduser('~/.hermes'))` in scratch scripts.

8. **Edge TTS as the default is fine.** If you're online and don't need offline, the `edge` provider (Microsoft's free endpoint, no key) is genuinely higher quality than `piper low` and free. Don't reflexively swap to local.

9. **`text_to_speech_tool` returns a JSON string, not a dict.** Most call sites expect a dict and parse it with `json.loads(...)`. If you see `TypeError: string indices must be integers`, you forgot the parse — or you imported the wrong symbol (it's `text_to_speech_tool`, not `text_to_speech`).

10. **"Can you talk now?" almost always means STT, not TTS.** When the user asks whether Hermes can *speak* replies, they usually want full duplex (mic in, audio out). TTS (output) works anywhere; STT (input) requires a real microphone. Before promising voice mode works, probe the audio devices:

    ```python
    python -c "import sounddevice as sd; print(sd.query_devices())"
    ```

    If every device shows `0 in` capture channels (ALSA-only box with no mic, common on servers/workstations), `/voice on` will fail at recording time even though TTS works. Either:
    - Tell the user the limitation honestly and offer `text_to_speech` as on-demand audio trigger.
    - Have them plug in a USB mic/headset and retry.

11. **Auto-TTS in interactive CLI requires `voice.auto_tts: true`.** Setting `tts.provider: piper` only enables *manual* TTS (via the `text_to_speech` tool). For the interactive `hermes` CLI to *automatically speak its replies*, set:

    ```bash
    python -m hermes_cli.main config set voice.auto_tts true
    ```

    This is in the `voice:` config block, not `tts:` — easy to miss.

12. **`uv pip install -e ".[voice]"` may show "Installed 2 packages"** even when the voice deps are already present in the venv — it just bumps a transitive pin (e.g., numpy). Don't be fooled into thinking it failed; verify with `python -c "import faster_whisper, sounddevice"`. If both imports succeed, the extra resolved correctly.

13. **Voice mode runs in the interactive `hermes` CLI, not in backend CLI sessions.** When the user is talking to me through a non-interactive channel, `/voice on` doesn't apply — they need to launch `hermes` (the interactive REPL) themselves. Be honest about this rather than implying it should "just work" in the current session.

## Verification Checklist

- [ ] `which python` points inside `venv/` (or `.venv/`)
- [ ] `piper --version` (or equivalent) reports a version after activation
- [ ] `~/.hermes/tts/piper/<voice>.onnx` AND `.onnx.json` both exist
- [ ] Sanity WAV plays (step 4) — confirms engine + model work outside Hermes
- [ ] `python -m hermes_cli.main config get tts.provider` returns `piper`
- [ ] End-to-end `text_to_speech_tool()` call returns `success: true` with a real file path
- [ ] The output MP3 plays (`ffplay -nodisp -autoexit ~/.hermes/cache/audio/tts_*.mp3` or `paplay`)
- [ ] (Voice mode only) At least one audio device shows `> 0 in` capture channels — see `references/audio-io-probe.md`

## Quick Reference

```bash
# Full setup, copy-paste-able for piper:
cd {hermes_home}/hermes-agent
source venv/bin/activate
pip install piper-tts
mkdir -p ~/.hermes/tts/piper && cd ~/.hermes/tts/piper
curl -sL -o voice.onnx "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx"
curl -sL -o voice.onnx.json "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json"
cd {hermes_home}/hermes-agent
python -m hermes_cli.main config set tts.provider piper
python -m hermes_cli.main config set tts.piper.voice ~/.hermes/tts/piper/voice.onnx
python -c "import os; os.environ.setdefault('HERMES_HOME', os.path.expanduser('~/.hermes')); from tools.tts_tool import text_to_speech_tool; print(text_to_speech_tool('Hello from local Hermes.'))"
```