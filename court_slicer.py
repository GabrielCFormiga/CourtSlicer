"""CourtSlicer — flag basketball plays and cut video into clips."""

import argparse
import subprocess
import sys
from pathlib import Path

import tkinter as tk
import vlc


def parse_args():
    parser = argparse.ArgumentParser(description="Flag plays and cut video clips.")
    parser.add_argument("video", help="Path to the video file")
    return parser.parse_args()


class CourtSlicerApp(tk.Tk):
    def __init__(self, video_path: str):
        super().__init__()
        self.video_path = Path(video_path)
        self.flags: list[int] = []  # timestamps in ms
        self.total_ms: int = 0
        self._quitting = False

        self.title("CourtSlicer")
        self.resizable(False, False)
        self.configure(bg="black")

        self._build_ui()
        self._setup_vlc(video_path)
        self._bind_keys()

        # Embed VLC after window is realized
        self.after(150, self._embed_vlc)
        # Start status polling
        self.after(250, self._update_status)

    def _build_ui(self):
        self.canvas = tk.Canvas(self, width=1280, height=720, bg="black",
                                highlightthickness=0)
        self.canvas.pack()

        self.status_var = tk.StringVar(value="Loading...")
        self.status_bar = tk.Label(
            self,
            textvariable=self.status_var,
            bg="#1a1a1a",
            fg="#e0e0e0",
            font=("Monospace", 11),
            anchor="w",
            padx=8,
        )
        self.status_bar.pack(fill=tk.X)

        help_text = (
            "  A: -5s   D: +5s   SPACE: pause/play   "
            "F: flag   Q/Esc: quit & cut"
        )
        tk.Label(
            self,
            text=help_text,
            bg="#111111",
            fg="#888888",
            font=("Monospace", 10),
            anchor="w",
            padx=8,
        ).pack(fill=tk.X)

    def _setup_vlc(self, path: str):
        self.instance = vlc.Instance(
            "--quiet",
            "--no-video-title-show",
        )
        self.player = self.instance.media_player_new()
        media = self.instance.media_new_path(path)
        self.player.set_media(media)

        # Parse for duration at startup
        media.parse_with_options(vlc.MediaParseFlag.local, timeout=5000)
        self.total_ms = media.get_duration()

    def _embed_vlc(self):
        xid = self.canvas.winfo_id()
        print(f"[debug] embedding into XID={xid}")
        self.player.set_xwindow(xid)
        ret = self.player.play()
        print(f"[debug] play() returned {ret}")
        self.after(500, self._check_state)
        self.canvas.focus_set()

    def _check_state(self):
        state = self.player.get_state()
        t = self.player.get_time()
        print(f"[debug] state={state}  time={t}ms")
        if state == vlc.State.Error:
            mrl = self.player.get_media().get_mrl() if self.player.get_media() else "?"
            print(f"[debug] VLC error on media: {mrl}")

    def _bind_keys(self):
        self.bind("<KeyPress-a>", lambda e: self._on_rewind())
        self.bind("<KeyPress-d>", lambda e: self._on_ff())
        self.bind("<KeyPress-space>", lambda e: self._on_pause_toggle())
        self.bind("<KeyPress-f>", lambda e: self._on_flag())
        self.bind("<KeyPress-q>", lambda e: self._on_quit())
        self.bind("<Escape>", lambda e: self._on_quit())
        self.focus_set()

    def _on_rewind(self):
        current = self.player.get_time()
        self.player.set_time(max(0, current - 5000))

    def _on_ff(self):
        current = self.player.get_time()
        self.player.set_time(current + 5000)

    def _on_pause_toggle(self):
        self.player.pause()

    def _on_flag(self):
        t = self.player.get_time()
        if t >= 0:
            self.flags.append(t)
            self._refresh_status(t)

    def _on_quit(self):
        if self._quitting:
            return
        self._quitting = True

        length = self.player.get_length()
        if length > 0:
            self.total_ms = length

        self.player.stop()
        self.destroy()

    def _refresh_status(self, flagged_at: int = -1):
        current = self.player.get_time()
        total = self.total_ms
        flags_str = ", ".join(f"{ms/1000:.1f}s" for ms in self.flags) or "none"
        msg = f"  {_fmt_ms(current)} / {_fmt_ms(total)}   |   Flags: [{flags_str}]"
        if flagged_at >= 0:
            msg += f"   ← flagged {flagged_at/1000:.1f}s"
        self.status_var.set(msg)

    def _update_status(self):
        if self._quitting:
            return
        self._refresh_status()
        self.after(250, self._update_status)


def _fmt_ms(ms: int) -> str:
    if ms < 0:
        return "--:--"
    s = ms // 1000
    m, s = divmod(s, 60)
    return f"{m:02d}:{s:02d}"


def _get_duration_ffprobe(path: Path) -> float:
    """Fallback: ask ffprobe for duration in seconds."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        return float(result.stdout.strip())
    except Exception:
        return 0.0


def cut_video(source: Path, boundaries: list[float]):
    """Cut source into segments defined by boundaries (seconds)."""
    out_dir = source.parent
    total_cut = 0

    for i in range(len(boundaries) - 1):
        start = boundaries[i]
        end = boundaries[i + 1]

        if end - start < 0.5:
            print(f"  Skipping segment {i+1}: too short ({end - start:.2f}s)")
            continue

        output_path = out_dir / f"cut_{i+1:02d}.mp4"
        cmd = [
            "ffmpeg", "-y",
            "-ss", f"{start:.3f}",
            "-to", f"{end:.3f}",
            "-i", str(source),
            "-c", "copy",
            "-avoid_negative_ts", "make_zero",
            str(output_path),
        ]
        print(f"  Cutting segment {i+1}: {start:.1f}s → {end:.1f}s → {output_path.name}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            print(f"    WARNING: ffmpeg exited {result.returncode}")
            print(result.stderr[-500:] if result.stderr else "")
        else:
            total_cut += 1

    return total_cut


def main():
    args = parse_args()
    video_path = Path(args.video).resolve()

    if not video_path.exists():
        print(f"Error: file not found: {video_path}")
        sys.exit(1)

    print(f"Opening: {video_path}")
    print("Controls: A=-5s  D=+5s  SPACE=pause  F=flag  Q/Esc=quit & cut\n")

    app = CourtSlicerApp(str(video_path))
    app.mainloop()

    flags = app.flags
    total_ms = app.total_ms

    if not flags:
        print("No flags set — nothing to cut.")
        sys.exit(0)

    # Resolve total duration
    if total_ms <= 0:
        print("Resolving duration via ffprobe...")
        total_ms = int(_get_duration_ffprobe(video_path) * 1000)

    if total_ms <= 0:
        print("Error: could not determine video duration.")
        sys.exit(1)

    flags_sorted = sorted(set(flags))
    boundaries = [0.0] + [f / 1000.0 for f in flags_sorted] + [total_ms / 1000.0]

    print(f"\nFlags ({len(flags_sorted)}): {[f/1000 for f in flags_sorted]}")
    print(f"Total duration: {total_ms/1000:.1f}s")
    print(f"Cutting {len(boundaries)-1} segment(s)...\n")

    n = cut_video(video_path, boundaries)
    print(f"\nDone — {n} clip(s) written to {video_path.parent}/")


if __name__ == "__main__":
    main()
