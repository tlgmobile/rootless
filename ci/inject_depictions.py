#!/usr/bin/env python3
# Inyecta los campos de depiction (apuntando a las depictions que genera Silica) en
# cada stanza del Packages que produjo dpkg-scanpackages sobre el pool. Solo para
# paquetes que tienen depiction native generada. Borra cualquier Depiction upstream.
import sys, os

pkgfile, depdir, host = sys.argv[1], sys.argv[2], sys.argv[3]
have = {f[:-5] for f in os.listdir(depdir) if f.endswith(".json")}  # bundle_ids con depiction
DEP_FIELDS = ("Depiction:", "SileoDepiction:", "ModernDepiction:", "Icon:")

def process(stanza):
    if not stanza:
        return []
    pkg = next((l.split(":", 1)[1].strip() for l in stanza if l.startswith("Package:")), None)
    stanza = [l for l in stanza if not l.startswith(DEP_FIELDS)]  # quita depiction upstream
    if pkg in have:
        stanza += [
            f"Depiction: https://{host}/depiction/web/{pkg}.html",
            f"SileoDepiction: https://{host}/depiction/native/{pkg}.json",
            f"ModernDepiction: https://{host}/depiction/native/{pkg}.json",
            f"Icon: https://{host}/assets/{pkg}/icon.png",
        ]
    return stanza

out, cur = [], []
for line in open(pkgfile).read().split("\n"):
    if line.strip() == "":
        s = process(cur)
        if s:
            out += s + [""]
        cur = []
    else:
        cur.append(line)
s = process(cur)
if s:
    out += s + [""]
open(pkgfile, "w").write("\n".join(out).rstrip("\n") + "\n")
print(f"depictions inyectadas en {len(have)} paquete(s):", ", ".join(sorted(have)))
