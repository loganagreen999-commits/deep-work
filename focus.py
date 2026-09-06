#!/usr/bin/env python3
"""
Deep Work, laptop half.

  focus start "Controls lab 2" 45 --est 20   block the distracting sites, run a clock
  focus stop                                 end early and unblock
  focus status                               what is running
  focus serve                                serve the phone app on the LAN + take its sessions
  focus stats                                where the time went

Blocking rewrites the Windows hosts file, which needs Administrator. One elevated
helper is launched per session; it restores the file when the clock runs out, or
sooner if `focus stop` drops the stop flag. So: one UAC prompt per session, not two.
"""
import argparse, datetime as dt, json, os, re, subprocess, sys, time, uuid
from pathlib import Path

HOME     = Path(__file__).resolve().parent
STATE    = HOME / "state"
SESSIONS = STATE / "sessions.json"
LIVE     = STATE / "live.json"
STOPFLAG = STATE / "stop"
BLOCKLIST= HOME / "blocklist.txt"
HOSTS    = Path("/mnt/c/Windows/System32/drivers/etc/hosts")
MARK_A   = "# >>> deep work >>>"
MARK_B   = "# <<< deep work <<<"

def now(): return time.time()
def load(p, d):
    try: return json.loads(p.read_text())
    except Exception: return d
def save(p, v):
    STATE.mkdir(exist_ok=True)
    p.write_text(json.dumps(v, indent=1))

# ---------- blocklist ----------
def domains():
    out = []
    if not BLOCKLIST.exists(): return out
    for line in BLOCKLIST.read_text().splitlines():
        line = line.split("#")[0].strip().lower()
        if not line: continue
        out.append(line)
        for pre in ("www.", "m."):
            if not line.startswith(pre): out.append(pre + line)
    return sorted(set(out))

def hosts_block(doms):
    body = "\n".join("0.0.0.0 %s" % d for d in doms)
    return "%s\n%s\n%s\n" % (MARK_A, body, MARK_B)

def strip_block(text):
    return re.sub(re.escape(MARK_A) + r".*?" + re.escape(MARK_B) + r"\n?", "", text, flags=re.S)

# ---------- the elevated helper ----------
HELPER = r'''
$hosts = "$env:SystemRoot\System32\drivers\etc\hosts"
$flag  = "{flag}"
$block = @"
{block}
"@
$orig = Get-Content -Raw -LiteralPath $hosts
if ($orig -notmatch [regex]::Escape("{mark_a}")) {{
  Set-Content -LiteralPath $hosts -Value ($orig.TrimEnd() + "`r`n" + $block) -Encoding ASCII
}}
ipconfig /flushdns | Out-Null
$deadline = (Get-Date).AddSeconds({secs})
while ((Get-Date) -lt $deadline) {{
  if (Test-Path -LiteralPath $flag) {{ break }}
  Start-Sleep -Milliseconds 800
}}
$cur = Get-Content -Raw -LiteralPath $hosts
$clean = [regex]::Replace($cur, [regex]::Escape("{mark_a}") + "(.|`n|`r)*?" + [regex]::Escape("{mark_b}") + "(`r`n|`n)?", "")
Set-Content -LiteralPath $hosts -Value $clean.TrimEnd() -Encoding ASCII
ipconfig /flushdns | Out-Null
Remove-Item -LiteralPath $flag -ErrorAction SilentlyContinue
'''

def win_path(p: Path) -> str:
    out = subprocess.run(["wslpath", "-w", str(p)], capture_output=True, text=True)
    return out.stdout.strip() or str(p)

def arm_block(seconds):
    doms = domains()
    if not doms:
        print("blocklist.txt is empty — running the clock without blocking.")
        return False
    STATE.mkdir(exist_ok=True)
    if STOPFLAG.exists(): STOPFLAG.unlink()
    script = HELPER.format(flag=win_path(STOPFLAG), block=hosts_block(doms).strip(),
                           mark_a=MARK_A, mark_b=MARK_B, secs=int(seconds))
    sp = STATE / "helper.ps1"
    sp.write_text(script)
    cmd = ("Start-Process powershell -Verb RunAs -WindowStyle Hidden "
           "-ArgumentList '-ExecutionPolicy','Bypass','-File','%s'" % win_path(sp))
    r = subprocess.run(["powershell.exe", "-NoProfile", "-Command", cmd],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("could not elevate:", (r.stderr or "").strip()[:200])
        return False
    print("blocked %d domains (approve the prompt if you have not already)" % len(doms))
    return True

def release_block():
    STATE.mkdir(exist_ok=True)
    STOPFLAG.write_text("stop")

# ---------- commands ----------
def cmd_start(a):
    if LIVE.exists() and load(LIVE, {}).get("start"):
        print("a session is already running — `focus stop` first"); return 1
    secs = a.minutes * 60
    blocked = arm_block(secs + 5)
    live = {"id": uuid.uuid4().hex[:10], "task": a.task, "course": a.course or "",
            "start": now(), "dur": secs, "est": a.est, "blocked": blocked}
    save(LIVE, live)
    print("\n  %s%s\n  %d minutes. Ctrl-C leaves the block up; `focus stop` ends it.\n"
          % (a.task, (" · " + a.course) if a.course else "", a.minutes))
    try:
        while True:
            left = live["start"] + secs - now()
            if left <= 0: break
            if STOPFLAG.exists(): break
            m, s = divmod(int(left), 60)
            print("\r  %02d:%02d remaining " % (m, s), end="", flush=True)
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n  (clock detached; the block still lifts on time)")
        return 0
    print("\r" + " " * 30 + "\r", end="")
    finish("done", "")
    return 0

def finish(how, reason):
    live = load(LIVE, None)
    if not live: return
    worked = min(now() - live["start"], live["dur"])
    rec = {"id": live["id"], "task": live["task"], "course": live["course"],
           "at": live["start"] * 1000, "planned": round(live["dur"] / 60),
           "actual": max(0, round(worked / 60)), "est": live["est"],
           "ended": how, "reason": reason, "leaves": 0, "awaySec": 0, "src": "laptop"}
    ss = load(SESSIONS, [])
    ss.append(rec); save(SESSIONS, ss)
    if LIVE.exists(): LIVE.unlink()
    release_block()
    print("  logged %d min on %s" % (rec["actual"], rec["task"]))

def cmd_stop(a):
    live = load(LIVE, None)
    if not live:
        release_block(); print("nothing running (unblocked anyway)"); return 0
    finish("bail", a.reason or "other")
    return 0

def cmd_status(a):
    live = load(LIVE, None)
    if not live: print("idle"); return 0
    left = live["start"] + live["dur"] - now()
    print("%s — %d:%02d left%s" % (live["task"], max(0, int(left)) // 60,
          max(0, int(left)) % 60, " (blocking)" if live.get("blocked") else ""))
    return 0

def cmd_stats(a):
    ss = load(SESSIONS, [])
    if not ss: print("no sessions yet"); return 0
    tot = sum(s["actual"] for s in ss)
    bail = [s for s in ss if s["ended"] == "bail" and s.get("reason") != "early"]
    print("%d sessions, %d minutes, %d ended early" % (len(ss), tot, len(bail)))
    per = {}
    for s in ss:
        d = dt.datetime.fromtimestamp(s["at"] / 1000).strftime("%Y-%m-%d")
        per[d] = per.get(d, 0) + s["actual"]
    for d in sorted(per)[-14:]:
        print("  %s  %4d min  %s" % (d, per[d], "#" * min(40, per[d] // 5)))
    why = {}
    for s in bail: why[s.get("reason", "?")] = why.get(s.get("reason", "?"), 0) + 1
    if why:
        print("\n  ended early because:")
        for r, n in sorted(why.items(), key=lambda x: -x[1]): print("    %-12s %d" % (r, n))
    return 0

# ---------- the phone-facing server ----------
def cmd_serve(a):
    import http.server, socketserver, socket
    class H(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *ar, **kw): super().__init__(*ar, directory=str(HOME), **kw)
        def _json(self, code, obj):
            b = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(b)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers(); self.wfile.write(b)
        def do_OPTIONS(self):
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
            self.end_headers()
        def do_GET(self):
            if self.path.startswith("/api/sessions"):
                return self._json(200, {"sessions": load(SESSIONS, [])})
            return super().do_GET()
        def do_POST(self):
            if not self.path.startswith("/api/sessions"): return self._json(404, {"error": "no"})
            n = int(self.headers.get("Content-Length") or 0)
            if n > 4_000_000: return self._json(413, {"error": "too big"})
            try: body = json.loads(self.rfile.read(n) or b"{}")
            except Exception: return self._json(400, {"error": "bad json"})
            incoming = body.get("sessions") or []
            have = load(SESSIONS, [])
            seen = {s.get("id") for s in have}
            added = [s for s in incoming if isinstance(s, dict) and s.get("id") and s["id"] not in seen]
            if added:
                have.extend(added); have.sort(key=lambda s: s.get("at", 0)); save(SESSIONS, have)
            return self._json(200, {"added": len(added), "total": len(have)})
        def log_message(self, *ar): pass
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try: s.connect(("8.8.8.8", 80)); ip = s.getsockname()[0]
    except Exception: ip = "127.0.0.1"
    finally: s.close()
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("0.0.0.0", a.port), H) as srv:
        print("app      http://%s:%d/" % (ip, a.port))
        print("sync url http://%s:%d   <- paste into the phone's Stats tab" % (ip, a.port))
        print("Ctrl-C to stop.")
        try: srv.serve_forever()
        except KeyboardInterrupt: print()
    return 0

def main():
    p = argparse.ArgumentParser(prog="focus", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("start"); a.add_argument("task"); a.add_argument("minutes", type=int)
    a.add_argument("--course", default=""); a.add_argument("--est", type=int, default=0)
    a.set_defaults(fn=cmd_start)
    b = sub.add_parser("stop"); b.add_argument("--reason", default="other"); b.set_defaults(fn=cmd_stop)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    sub.add_parser("stats").set_defaults(fn=cmd_stats)
    c = sub.add_parser("serve"); c.add_argument("--port", type=int, default=8777); c.set_defaults(fn=cmd_serve)
    args = p.parse_args()
    sys.exit(args.fn(args))

if __name__ == "__main__":
    main()
