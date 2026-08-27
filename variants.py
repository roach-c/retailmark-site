#!/usr/bin/env python3
"""
variants.py — put every palette live at its own URL, so a choice can be made by
clicking through the real site instead of squinting at screenshots.

    DROPLET=142.93.63.177 python3 variants.py            build and deploy all
    DROPLET=142.93.63.177 python3 variants.py clay navy  just these
    python3 variants.py --local                          build only, no deploy

Each palette is built in its own temp copy of the site, so the working tree is
never touched and a failed build cannot leave the repo half-recoloured. Each
one lands on retailmark-<palette>.tetheredcrew.com.

ORIGIN is rewritten per variant. Without that every variant's link-preview card
would point at the main preview host, so texting three options would show the
same picture three times.
"""

import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TC = os.path.abspath(os.path.join(HERE, "..", "tethered-crew"))
DROPLET = os.environ.get("DROPLET", "")

sys.path.insert(0, HERE)
from palette import PALETTES                                  # noqa: E402

SKIP = {".git", "__pycache__", "node_modules", "submissions.json", "server.log"}


def build(name, workdir):
    """A full site build in a throwaway directory."""
    shutil.copytree(HERE, workdir,
                    ignore=shutil.ignore_patterns(*SKIP), dirs_exist_ok=True)
    host = f"https://retailmark-{name}.tetheredcrew.com"

    chrome = os.path.join(workdir, "chrome.py")
    s = open(chrome).read()
    s = s.replace('ORIGIN = "https://retailmark.tetheredcrew.com"',
                  f'ORIGIN = "{host}"')
    open(chrome, "w").write(s)

    for cmd in (["palette.py", name], ["ogimage.py"], ["blog.py"],
                ["chrome.py"], ["sitemap.py"]):
        r = subprocess.run([sys.executable] + cmd, cwd=workdir,
                           capture_output=True, text=True)
        if r.returncode:
            raise SystemExit(f"{name}: {cmd[0]} failed\n{r.stdout}{r.stderr}")
    return host


if __name__ == "__main__":
    wanted = [a for a in sys.argv[1:] if not a.startswith("--")] or list(PALETTES)
    local = "--local" in sys.argv
    unknown = [w for w in wanted if w not in PALETTES]
    if unknown:
        raise SystemExit(f"unknown palette(s): {', '.join(unknown)}")
    if not local and not DROPLET:
        raise SystemExit("set DROPLET=<ip>, or pass --local to build without deploying")

    for name in wanted:
        work = tempfile.mkdtemp(prefix=f"rm-{name}-")
        try:
            host = build(name, work)
            print(f"  built {name}")
            if local:
                print(f"    {work}")
                continue
            r = subprocess.run(
                ["./deploy/preview.sh", f"retailmark-{name}", work],
                cwd=TC, env={**os.environ, "DROPLET": DROPLET},
                capture_output=True, text=True)
            print("\n".join("    " + l for l in (r.stdout + r.stderr).strip().split("\n")[-3:]))
        finally:
            if not local:
                shutil.rmtree(work, ignore_errors=True)

    if not local:
        print("\n  Send these:")
        for name in wanted:
            print(f"    {PALETTES[name]['note'].split(' — ')[0]:12} "
                  f"https://retailmark-{name}.tetheredcrew.com")
