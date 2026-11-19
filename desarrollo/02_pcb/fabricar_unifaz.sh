#!/usr/bin/env bash
# PCB UNIFAZ: gerbers (cobre en B.Cu), mapa de puentes (F.Cu), BOM, montaje y renders.
set -euo pipefail
cd "$(dirname "$0")"
P=medidor_ppg_unifaz
rm -rf fab_unifaz && mkdir -p fab_unifaz/gerbers img
# Gerbers: incluye B.Cu (cobre), F.Cu (puentes de alambre), mascaras, serigrafia, borde
kicad-cli pcb export gerbers --layers B.Cu,F.Cu,B.Paste,B.SilkS,F.SilkS,B.Mask,Edge.Cuts \
  --subtract-soldermask --no-x2 --use-drill-file-origin -o fab_unifaz/gerbers/ $P.kicad_pcb >/dev/null
kicad-cli pcb export drill --format excellon --drill-origin absolute --excellon-units mm \
  --excellon-separate-th --generate-map --map-format gerberx2 -o fab_unifaz/gerbers/ $P.kicad_pcb >/dev/null
(cd fab_unifaz/gerbers && zip -q ../${P}_gerbers.zip *)
# BOM (misma fuente)
kicad-cli sch export bom --fields 'Reference,Value,Footprint,${QUANTITY}' --labels 'Ref,Valor,Huella,Cant' \
  --group-by Value,Footprint --sort-field Reference --exclude-dnp -o fab_unifaz/${P}_BOM.csv medidor_ppg.kicad_sch >/dev/null
# Mapa de PUENTES (solo F.Cu + serigrafia + borde): lo que soldar por arriba
kicad-cli pcb export pdf --layers F.Cu,F.SilkS,Edge.Cuts --mode-single -o fab_unifaz/${P}_mapa_puentes.pdf $P.kicad_pcb >/dev/null
# Cobre (cara de abajo, vista desde abajo = como se graba)
kicad-cli pcb export pdf --layers B.Cu,Edge.Cuts --mode-single --black-and-white -o fab_unifaz/${P}_cobre_inferior.pdf $P.kicad_pcb >/dev/null
# Montaje (piezas vistas desde arriba)
kicad-cli pcb export pdf --layers F.SilkS,F.Fab,Edge.Cuts --mode-single -o fab_unifaz/${P}_montaje_superior.pdf $P.kicad_pcb >/dev/null
# Renders
kicad-cli pcb render --side top --quality high -w 1600 --height 1100 -o img/unifaz_3d_superior.png $P.kicad_pcb >/dev/null
kicad-cli pcb render --side bottom --quality high -w 1600 --height 1100 -o img/unifaz_3d_inferior.png $P.kicad_pcb >/dev/null
kicad-cli pcb drc --severity-error -o fab_unifaz/drc.rpt $P.kicad_pcb | grep Found || true
ls fab_unifaz
