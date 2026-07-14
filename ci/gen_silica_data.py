#!/usr/bin/env python3
# Version CI de gen_silica_data: rutas por variable de entorno (para el runner de GitHub).
# Pre-genera Silica/Packages/<pkg>/{deb, silica_data/index.json} leyendo el control del
# .deb latest de debs/. Evita los input() de Silica.
import os, json, shutil, subprocess

SILICA = os.environ.get("SILICA_DIR", "Silica")
POOL   = os.environ.get("POOL_DIR", "debs")
_LIST  = os.environ.get("TOOLKIT_FILE", "ci/toolkit.txt")
HOST   = os.environ.get("HOST", "tlgmobile.github.io/rootless")

CATALOG = [l.strip() for l in open(_LIST)
           if l.strip() and not l.lstrip().startswith("#")]

def ctl(deb, field):
    return subprocess.run(["dpkg-deb", "-f", deb, field],
                          capture_output=True, text=True).stdout.strip()

def newer(a, b):  # a > b ?
    return subprocess.run(["dpkg", "--compare-versions", a, "gt", b]).returncode == 0

# Indexa el pool por paquete -> [(version, path)]
debs = {}
for f in os.listdir(POOL):
    if f.endswith(".deb"):
        p = os.path.join(POOL, f)
        debs.setdefault(ctl(p, "Package"), []).append((ctl(p, "Version"), p))

# Limpia Packages/ para que no queden folders stale.
shutil.rmtree(os.path.join(SILICA, "Packages"), ignore_errors=True)
os.makedirs(os.path.join(SILICA, "Packages"), exist_ok=True)

for pkg in CATALOG:
    cands = debs.get(pkg, [])
    if not cands:
        print("MISSING en pool:", pkg); continue
    ver, path = cands[0]
    for v, p in cands[1:]:
        if newer(v, ver): ver, path = v, p
    folder = os.path.join(SILICA, "Packages", pkg)
    sd = os.path.join(folder, "silica_data")
    shutil.rmtree(folder, ignore_errors=True)
    os.makedirs(sd)
    shutil.copy(path, os.path.join(folder, os.path.basename(path)))
    author = (ctl(path, "Author") or ctl(path, "Maintainer") or "Unknown").split("<")[0].strip()
    idx = {
        "bundle_id": pkg,
        "name": ctl(path, "Name") or pkg,
        "version": ver,
        "tagline": ctl(path, "Description") or "iOS tool",
        "homepage": ctl(path, "Homepage") or ("https://" + HOST),
        "developer": {"name": author, "email": ""},
        "maintainer": {"name": "TLG", "email": "tlgmobile@users.noreply.github.com"},
        "section": ctl(path, "Section") or "Packages",
        "works_min": "14.0",
        "works_max": "17.0",
        "featured": "true",
    }
    dep = ctl(path, "Depends")
    if dep:
        idx["dependencies"] = dep
    with open(os.path.join(sd, "index.json"), "w") as fh:
        json.dump(idx, fh, indent=2)
    print("OK", pkg, ver)
