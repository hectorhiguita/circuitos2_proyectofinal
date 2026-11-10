#!/usr/bin/env bash
# Gerbers + taladros (JLCPCB), BOM, esquema PDF y renders 3D.   Uso: ./fabricar.sh
set -euo pipefail
cd "$(dirname "$0")"
P=medidor_ppg
rm -rf fab && mkdir -p fab/gerbers img
kicad-cli pcb export gerbers --layers F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts \
  --subtract-soldermask --no-x2 --use-drill-file-origin -o fab/gerbers/ $P.kicad_pcb >/dev/null
kicad-cli pcb export drill --format excellon --drill-origin absolute --excellon-units mm \
  --excellon-separate-th --generate-map --map-format gerberx2 -o fab/gerbers/ $P.kicad_pcb >/dev/null
(cd fab/gerbers && zip -q ../${P}_gerbers_JLCPCB.zip *)
kicad-cli sch export bom --fields 'Reference,Value,Footprint,${QUANTITY}' --labels 'Ref,Valor,Huella,Cant' \
  --group-by Value,Footprint --sort-field Reference --exclude-dnp -o fab/${P}_BOM.csv $P.kicad_sch >/dev/null
kicad-cli sch export pdf -o fab/${P}_esquema.pdf $P.kicad_sch >/dev/null
kicad-cli pcb export pdf --layers F.Cu,F.SilkS,Edge.Cuts --mode-single -o fab/${P}_montaje_superior.pdf $P.kicad_pcb >/dev/null
kicad-cli pcb render --side top --quality high -w 1800 --height 1200 -o img/pcb_3d_superior.png $P.kicad_pcb >/dev/null
kicad-cli pcb render --side bottom --quality high -w 1800 --height 1200 -o img/pcb_3d_inferior.png $P.kicad_pcb >/dev/null
kicad-cli pcb render --side top --rotate '-35,0,25' --perspective --quality high -w 1800 --height 1200 \
  -o img/pcb_3d_perspectiva.png $P.kicad_pcb >/dev/null
kicad-cli pcb export step --subst-models --force -o fab/${P}.step $P.kicad_pcb >/dev/null 2>&1 || true
kicad-cli pcb drc --severity-error --schematic-parity -o fab/drc.rpt $P.kicad_pcb | grep Found
ls -la fab img
