# CourtSlicer

Watch basketball footage, flag plays in real time, and automatically cut the video into clips. Audio is preserved (referee whistles, crowd noise). Cuts are lossless and instantaneous via ffmpeg `-c copy`.

## Requirements

- [ffmpeg](https://ffmpeg.org/) (includes ffprobe)
- [python-vlc](https://pypi.org/project/python-vlc/) (for video playback and keypress handling)
- [tkinter](https://docs.python.org/3/library/tkinter.html) (for the GUI window and keyboard input)

## Installation

### Build from source

```sh
git clone https://github.com/GabrielCFormiga/CourtSlicer.git
cd CourtSlicer
bash install.sh
```

The script checks system dependencies (Python ≥3.10, tkinter, ffmpeg), installs [uv](https://docs.astral.sh/uv/) if needed, and wires up the `court-slicer` entry point in `.venv/bin/`.

Options:
- `--yes` — non-interactive (auto-install uv)
- `--no-uv` — force pip instead of uv

## Usage

```sh
source .venv/bin/activate
court-slicer <video_file>
```

Or without activating:

```sh
.venv/bin/court-slicer <video_file>
```

### Controls

| Key | Action |
|-----|--------|
| `F` | Flag current timestamp |
| `Space` | Pause / play |
| `A` | Rewind 5 seconds |
| `D` | Fast-forward 5 seconds |
| `Q` / `Esc` | Quit and cut clips |

### Output

Clips are written alongside the source file:

```
game.mp4
cut_01.mp4   # start → first flag
cut_02.mp4   # first flag → second flag
...
cut_N.mp4    # N-1 flag → end
```


## Notes

- Cuts land on the nearest keyframe (up to ~2s before the flag). Extra footage at the start of a clip is expected and acceptable.
- Duplicate flags are silently deduplicated.
- Segments shorter than 0.5s are skipped.
