"""Record one Sonic Pi theme to a WAV, without touching the GUI.

The old pipeline was manual: open Sonic Pi, press Rec, press Run, wait, press Rec again, save. That
is where "press Rec BEFORE Run" came from - a take that starts late loses the downbeat and cut_loop
has nothing to find. Doing it by hand also means eight takes of a boss theme playing out loud.

None of that is necessary. Sonic Pi 4 runs its server as a daemon and the GUI is just an OSC client,
so this script is the GUI: it boots the daemon, reads the ports and token off its first line of
stdout, keeps it alive, and sends the same four messages the Rec button sends.

    /start-recording <token>
    /run-code        <token> <code>
    /stop-recording  <token>
    /save-recording  <token> <path>

Rec goes first here for the same reason it did by hand. The take then runs `--cycles` times round the
piece (2.5 by default: cut_loop wants a clean second cycle, and the half gives the tail somewhere to
be ragged).

    python record_theme.py eric_theme_v3.rb 138 --out raw/eric_theme_v3_raw.wav

The daemon dies with this process, so nothing is left running.
"""

import argparse
import os
import pathlib
import socket
import struct
import subprocess
import sys
import threading
import time

SONIC_PI = pathlib.Path(os.environ.get("SONIC_PI_HOME", r"C:\Program Files\Sonic Pi"))
RUBY = SONIC_PI / "app" / "server" / "native" / "ruby" / "bin" / "ruby.exe"
DAEMON = SONIC_PI / "app" / "server" / "ruby" / "bin" / "daemon.rb"


def osc(path, *args):
    """One OSC 1.0 message. Only the int and string types are needed here."""
    def pad(b):
        return b + b"\0" * (4 - len(b) % 4)

    out = pad(path.encode())
    tags = ","
    body = b""
    for a in args:
        if isinstance(a, int):
            tags += "i"
            body += struct.pack(">i", a)
        else:
            tags += "s"
            body += pad(str(a).encode("utf-8"))
    return out + pad(tags.encode()) + body


class Daemon:
    """Sonic Pi's server, booted and kept alive for as long as this object is open."""

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.proc = None
        self.stop = threading.Event()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send(self, port, message):
        self.sock.sendto(message, ("127.0.0.1", port))

    def __enter__(self):
        if not RUBY.exists():
            sys.exit("no bundled ruby at %s - set SONIC_PI_HOME" % RUBY)
        self.proc = subprocess.Popen(
            [str(RUBY), str(DAEMON)],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            cwd=str(DAEMON.parent),
        )
        # "daemon-keep-alive gui-listen-to-server gui-send-to-server scsynth osc-cues token"
        line = self.proc.stdout.readline().decode().strip()
        if not line:
            sys.exit("the daemon exited without announcing its ports")
        bits = line.split()
        if len(bits) < 6:
            sys.exit("unexpected daemon line: %r" % line)
        self.keep_alive_port = int(bits[0])
        self.spider_port = int(bits[2])
        self.token = int(bits[5])
        if self.verbose:
            print("daemon up: spider=%d token=%d" % (self.spider_port, self.token))

        # It kills the whole stack if these stop arriving.
        def beat():
            while not self.stop.wait(1.0):
                try:
                    self.send(self.keep_alive_port, osc("/daemon/keep-alive", self.token))
                except OSError:
                    return

        self.beat = threading.Thread(target=beat, daemon=True)
        self.beat.start()
        return self

    def tell(self, path, *args):
        self.send(self.spider_port, osc(path, self.token, *args))

    def __exit__(self, *_):
        try:
            self.tell("/stop-all-jobs")
            time.sleep(0.5)
        except OSError:
            pass
        self.stop.set()
        if self.proc:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.kill()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source", help="the .rb theme to run")
    ap.add_argument("bpm", type=int)
    ap.add_argument("--bars", type=int, default=16)
    ap.add_argument("--beats", type=int, default=4)
    ap.add_argument("--cycles", type=float, default=2.5)
    ap.add_argument("--boot", type=float, default=18.0,
                    help="seconds to let scsynth come up before the take starts")
    ap.add_argument("--out", required=True)
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    code = pathlib.Path(args.source).read_text(encoding="utf-8")
    cycle = args.bars * args.beats * 60.0 / args.bpm
    take = cycle * args.cycles
    out = pathlib.Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    print("%s: cycle %.4f s, take %.1f s" % (pathlib.Path(args.source).name, cycle, take))

    with Daemon(args.verbose) as d:
        # scsynth has to be listening before Rec, or the head of the take is silence and cut_loop
        # hunts its downbeat inside a boot gap.
        time.sleep(args.boot)
        d.tell("/start-recording")
        time.sleep(0.3)
        d.tell("/run-code", code)
        time.sleep(take)
        d.tell("/stop-recording")
        time.sleep(0.5)
        d.tell("/save-recording", str(out))
        # save is asynchronous: it writes on the server's thread, so wait for the file to stop
        # growing rather than guessing.
        last, still = -1, 0
        for _ in range(120):
            time.sleep(0.5)
            size = out.stat().st_size if out.exists() else 0
            still = still + 1 if size == last and size > 0 else 0
            last = size
            if still >= 4:
                break
        if not out.exists() or out.stat().st_size == 0:
            sys.exit("no recording landed at %s" % out)
        print("wrote %s (%.1f MB)" % (out, out.stat().st_size / 1e6))


if __name__ == "__main__":
    main()
