#!/usr/bin/env python3
"""Build the Excalidraw stencil scene from the vendored Flight icons.

Derive, don't fork: `hashicorp-stencil.excalidraw` is generated from `icons/`, so the
stencil and the icon set cannot drift. Re-run after changing `SECTIONS` or refreshing
`icons/` (the refresh command is recorded in references/design-system.md).

    python3 build_stencil.py

A .excalidraw scene is used rather than a .excalidrawlib because the library format
carries no `files` map -- see references/design-system.md, "Why a scene and not a library".
"""

import base64
import hashlib
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).parent
ICONS = HERE / "icons"
OUT = HERE / "hashicorp-stencil.excalidraw"

# Helios product colours, recorded so the build fails if Flight ships a different hex.
# Source: https://helios.hashicorp.design/foundations/colors
HELIOS_PRODUCT_HEX = {
    "terraform": "#7b42bc",
    "vault": "#ffcf25",
    "vault-radar": "#ffcf25",
    "vault-secrets": "#ffcf25",
    "consul": "#e03875",
    "nomad": "#06d092",
    "boundary": "#f24c53",
    "packer": "#02a8ef",
    "waypoint": "#14c6cb",
    "vagrant": "#1868f2",
    "hcp": "#000000",
}

# Helios foreground-strong: what a mono icon resolves to on a light canvas.
MONO_HEX = "#0c0c0e"

SECTIONS = [
    ("HashiCorp products", [
        "terraform-color-24", "vault-color-24", "vault-radar-color-24",
        "vault-secrets-color-24", "consul-color-24", "nomad-color-24",
        "boundary-color-24", "packer-color-24", "waypoint-color-24",
        "vagrant-color-24", "hcp-color-24",
    ]),
    ("Clouds and platforms", [
        "aws-color-24", "azure-color-24", "gcp-color-24", "kubernetes-color-24",
        "docker-color-24", "github-color-24", "gitlab-color-24", "helm-color-24",
    ]),
    ("Infrastructure", [
        "server-24", "server-cluster-24", "network-24", "network-alt-24",
        "load-balancer-24", "connection-gateway-24", "node-24", "database-24",
        "queue-24", "api-24", "module-24", "layers-24", "box-24",
        "globe-24", "globe-private-24", "entry-point-24", "exit-point-24",
    ]),
    ("Security and identity", [
        "lock-24", "key-24", "keychain-24", "certificate-24", "token-24",
        "shield-24", "identity-service-24", "identity-user-24",
        "user-24", "users-24", "org-24",
    ]),
    ("State and signals", [
        "check-circle-24", "alert-triangle-24", "activity-24", "monitor-24",
        "clock-24", "sync-24", "repeat-24",
    ]),
]

# Layout grid, in Excalidraw canvas units.
ICON = 48
COL = 132
ROW = 104
PER_ROW = 8
SECTION_GAP = 72
LABEL_SIZE = 12
HEADING_SIZE = 20
LINE_HEIGHT = 1.25


def stable_int(*parts):
    """A deterministic stand-in for Excalidraw's random seed/nonce.

    Excalidraw only needs these to be integers that differ between elements; deriving
    them from the element's identity keeps rebuilds byte-identical, so a regenerated
    stencil shows an empty diff unless the icon set actually changed.
    """
    h = hashlib.sha1("|".join(parts).encode()).hexdigest()
    return int(h[:8], 16)


def base(kind, eid, x, y, w, h, seed_parts):
    return {
        "id": eid,
        "type": kind,
        "x": x,
        "y": y,
        "width": w,
        "height": h,
        "angle": 0,
        "strokeColor": "transparent",
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 1,
        "strokeStyle": "solid",
        "roughness": 0,
        "opacity": 100,
        "groupIds": [],
        "frameId": None,
        "roundness": None,
        "seed": stable_int("seed", *seed_parts),
        "version": 1,
        "versionNonce": stable_int("nonce", *seed_parts),
        "index": None,
        "isDeleted": False,
        "boundElements": None,
        "updated": 1,
        "link": None,
        "locked": False,
    }


def text_element(eid, x, y, content, size, colour, seed_parts):
    # Excalidraw recomputes text metrics on load, but a plausible box keeps the
    # stencil laid out correctly in previews that render the JSON as-is.
    width = max(1.0, len(content) * size * 0.55)
    height = size * LINE_HEIGHT
    el = base("text", eid, x - width / 2, y, width, height, seed_parts)
    el.update({
        "strokeColor": colour,
        "fontSize": size,
        "fontFamily": 2,  # Helvetica -- Inter is not among Excalidraw's fonts
        "text": content,
        "originalText": content,
        "textAlign": "center",
        "verticalAlign": "top",
        "containerId": None,
        "lineHeight": LINE_HEIGHT,
        "autoResize": True,
    })
    return el


def load_icon(name):
    """Return (dataURL, fileId) for an icon, pinning its colour to Helios."""
    path = ICONS / f"{name}.svg"
    if not path.exists():
        sys.exit(f"missing icon: {path}")
    svg = path.read_text()

    product = name[: -len("-color-24")] if name.endswith("-color-24") else None
    if product in HELIOS_PRODUCT_HEX:
        expected = HELIOS_PRODUCT_HEX[product]
        found = {h.lower() for h in re.findall(r"#[0-9a-fA-F]{6}", svg)}
        if found and expected not in found:
            sys.exit(
                f"{name}: Flight ships {sorted(found)}, Helios records {expected}. "
                "Reconcile against https://helios.hashicorp.design/foundations/colors "
                "before rebuilding."
            )
        # hcp-color carries no explicit hex; it inherits, so pin it.
        svg = svg.replace("currentColor", expected)
    else:
        svg = svg.replace("currentColor", MONO_HEX)

    raw = svg.encode()
    file_id = hashlib.sha1(raw).hexdigest()
    data_url = "data:image/svg+xml;base64," + base64.b64encode(raw).decode()
    return data_url, file_id


def main():
    elements, files = [], {}
    y = 0

    for section, names in SECTIONS:
        elements.append(
            text_element(f"h-{section}", (PER_ROW * COL) / 2, y, section,
                         HEADING_SIZE, MONO_HEX, ("heading", section))
        )
        y += HEADING_SIZE * LINE_HEIGHT + 24

        for i, name in enumerate(names):
            col, row = i % PER_ROW, i // PER_ROW
            cx = col * COL + COL / 2
            iy = y + row * ROW

            data_url, file_id = load_icon(name)
            files[file_id] = {
                "mimeType": "image/svg+xml",
                "id": file_id,
                "dataURL": data_url,
                "created": 1,
                "lastRetrieved": 1,
            }

            img = base("image", f"i-{name}", cx - ICON / 2, iy, ICON, ICON, ("image", name))
            img.update({"fileId": file_id, "status": "saved", "scale": [1, 1], "crop": None})
            elements.append(img)
            elements.append(
                text_element(f"t-{name}", cx, iy + ICON + 10,
                             name.replace("-color-24", "").replace("-24", ""),
                             LABEL_SIZE, MONO_HEX, ("label", name))
            )

        rows = (len(names) + PER_ROW - 1) // PER_ROW
        y += rows * ROW + SECTION_GAP

    scene = {
        "type": "excalidraw",
        "version": 2,
        "source": "hashicorp-diagram-excalidraw",
        "elements": elements,
        "appState": {"gridSize": None, "viewBackgroundColor": "#ffffff"},
        "files": files,
    }
    OUT.write_text(json.dumps(scene, indent=2) + "\n")

    icons = sum(len(n) for _, n in SECTIONS)
    print(f"{OUT.name}: {icons} icons, {len(files)} files, {OUT.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
