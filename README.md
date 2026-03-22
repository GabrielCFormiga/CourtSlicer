# CourtSlicer

Watch basketball footage, flag plays in real time, and automatically cut the video into clips. Audio is preserved (referee whistles, crowd noise). Cuts are lossless and instantaneous via ffmpeg `-c copy`.

## Requirements

- [ffmpeg](https://ffmpeg.org/) (includes ffprobe)
- [python-vlc](https://pypi.org/project/python-vlc/) (for video playback and keypress handling)

## Usage

```sh
python court_slicer.py <input>
```

- `input` — a video file

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
