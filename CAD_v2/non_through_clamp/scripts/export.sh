#!/usr/bin/env bash
# One-shot export: part STLs + assembly/exploded PNGs for non-through clamp.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCAD="$ROOT/kolbe_non_through.scad"
STL="$ROOT/stls"
RND="$ROOT/renders"
mkdir -p "$STL" "$RND"

if [[ ! -x /usr/bin/openscad ]] && ! command -v openscad >/dev/null; then
  echo "openscad not found" >&2
  exit 1
fi
OSC="$(command -v openscad || echo /usr/bin/openscad)"

parts=(
  front_endplate
  rear_endplate
  frame
  electrode_tab
  electrode_plain
  locator_pin
)

echo "== STL parts =="
for p in "${parts[@]}"; do
  echo "  $p"
  "$OSC" -o "$STL/${p}.stl" -D "part=\"${p}\"" "$SCAD"
done

echo "== PNG renders =="
# OpenSCAD 2021: --render requires a value (CGAL). Fallback to preview if render fails.
render_png() {
  local out="$1" part="$2"
  if "$OSC" -o "$out" \
      --imgsize=1600,1200 --colorscheme=DeepOcean \
      --projection=p --autocenter --viewall \
      --render=CGAL \
      -D "part=\"${part}\"" "$SCAD"; then
    return 0
  fi
  echo "WARN: CGAL render failed for $part — preview fallback" >&2
  "$OSC" -o "$out" \
      --imgsize=1600,1200 --colorscheme=DeepOcean \
      --projection=p --autocenter --viewall \
      --preview=throwntogether \
      -D "part=\"${part}\"" "$SCAD"
}

render_png "$RND/assembly.png" assembly
render_png "$RND/exploded.png" exploded

"$OSC" -o "$RND/assembly_preview.png" \
  --imgsize=1200,900 --colorscheme=DeepOcean \
  --projection=p --autocenter --viewall \
  -D 'part="assembly"' "$SCAD" || true

"$OSC" -o "$RND/exploded_preview.png" \
  --imgsize=1200,900 --colorscheme=DeepOcean \
  --projection=p --autocenter --viewall \
  -D 'part="exploded"' "$SCAD" || true

echo "== done =="
ls -la "$STL" "$RND"
