---
name: asset-decompose
description: Break a digital or art source file into its component assets (layers, text, images, vectors, palettes, fonts, audio) and record each in assets/assets.yaml with provenance and usage rights. Use as the first step of any art, design or media project, or when new source files arrive.
argument-hint: "<source file(s)>"
---

# Asset decomposition

Sources: $ARGUMENTS (default: art/media files in `inbox/`).

Never modify a source. Work on copies.

## 1. Fingerprint
sha256 each source; record name, format, dimensions/duration, color profile, and the tool that opened it.

## 2. Extract
Pick the tool by format and record `tool@version`:
- PSD/PSB: psd-tools via the layer script (layers, groups, text layers, blend/opacity/bbox as tags):
  ```
  python3 -I ${CLAUDE_PLUGIN_ROOT}/scripts/psd_layers.py <file.psd> --manifest assets/assets.yaml --export [--owner X --license Y]
  ```
  Run it without `--manifest` first to preview the YAML. Without psd-tools it exits 2 and says how to install (`pip install psd-tools`; `--export` also needs Pillow). Check masks and adjustment layers by hand; they're listed, not exported.
- SVG/AI/PDF: vector paths per group, embedded images, text runs (PyMuPDF, Inkscape CLI)
- Figma: the official Figma plugin (`claude plugin install figma@claude-plugins-official`). It brings the Figma MCP (components, styles, variables, asset export) and its skills. Load its `figma-use` / `figma-design-to-code` skill before calling its tools. Read-only for decomposition: don't edit the Figma file. Record `figma-mcp@<version>` and the file key and node id in `source`.
- Raster: palette extraction; segmentation only if asked:
  ```
  python3 -I ${CLAUDE_PLUGIN_ROOT}/scripts/palette.py <image> -k 6 [--method kmeans|mediancut] --manifest assets/assets.yaml
  ```
  It prints hex, share, a role (background, text, accent, primary, secondary, support) and WCAG contrast against the background, and writes `assets/palette/<id>.json`. Roles are a heuristic first read; say so. It needs Pillow to read the image (exits 2 with an install hint otherwise); the clustering is pure Python.
- Video/audio: ffmpeg (keyframes, tracks, stems if available)
- Fonts: names and licenses only; never redistribute font files

Export to `assets/<type>/<id>.<ext>`, lossless and at native resolution.

## 3. Manifest `assets/assets.yaml`
```yaml
- id: A-<sha8>-<n>          # stable; later work references this
  type: layer|text|image|vector|palette|font|audio|video|other
  name: <layer or element name>
  source: knowledge/raw/<sha8>_<file>#<layer path or page/time>
  path: assets/<type>/<id>.<ext>
  provenance: {extracted_by: <tool@version>, on: <date>, from_sha256: <hash>}
  rights: {owner: <who>, license: <license|client-owned|unknown>, notes: <restrictions>}
  variants: []               # derived files: {id, path, change, made_by}
  tags: []
```
Unknown rights are `unknown`, never assumed. Append; don't renumber existing IDs.

## 4. Finish
1. Check: every exported file is listed, every entry's path exists, counts match the source (layers, pages, tracks).
2. Run `verify` with those checks as criteria (`rubrics/asset-package.yaml` if present). As a subagent, return `verify: pending`.
3. Append a `task` event with `intent` (what the assets are for), `situation` (source, client, deadline) and `meta` (`kind_of_thing: asset decomposition`, tool problems, formats to handle better next time).
