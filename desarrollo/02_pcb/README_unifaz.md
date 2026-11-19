# PCB UNIFAZ (1 capa) — Medidor PPG

Para proveedor local que solo hace **unifaz** (una cara de cobre) con antisolder y máscara.

- **Cobre:** todo en la cara de **abajo** (B.Cu).
- **Puentes de alambre:** **40 cablecitos** soldados por la cara de **arriba** (donde van las piezas). Sin ellos el circuito no es unifaz.
- Placa 80 × 52 mm. DRC: 0 errores, 0 pendientes.

## Archivos (carpeta `fab_unifaz/`)
| Archivo | Para qué |
|---|---|
| `medidor_ppg_unifaz_gerbers.zip` | Mándalo al proveedor. Trae el cobre (B.Cu), máscara, antisolder y borde |
| `medidor_ppg_unifaz_cobre_inferior.pdf` | El cobre visto desde abajo (como se graba). Para revisar |
| `medidor_ppg_unifaz_mapa_puentes.pdf` | Dónde van los 40 puentes de alambre (cara de arriba) |
| `medidor_ppg_unifaz_montaje_superior.pdf` | Dónde va cada pieza |
| `medidor_ppg_unifaz_BOM.csv` | Lista de piezas |
| `../perforada/puentes_unifaz.md` | Los 40 puentes, uno por uno, con casilla para marcar |

## Qué entregar al proveedor
Dale el **`medidor_ppg_unifaz_gerbers.zip`**. Dile:
- 1 cara de cobre, FR-4, 1.6 mm.
- Con antisolder (máscara) y serigrafía, como él ofrece.
- Ancho de pista 0.4 mm, separación 0.3 mm (confírmale que su proceso lo aguanta).

## Armado
1. Suelda primero las piezas (mira `montaje_superior.pdf`).
2. Suelda los **40 puentes** por la cara de arriba. Usa `puentes_unifaz.md`: cada fila dice de qué pin a qué pin, con una casilla para marcar. Ej.: `ADC: R10.2 → J2.7`.
   - Usa alambre fino aislado (wire-wrap) para que no se toquen entre ellos.
3. Prueba por etapas con el osciloscopio (TP1–TP7), igual que en el README principal.

## Nota honesta
Este circuito tiene un op-amp y 57 piezas: en 1 cara **no** se puede sin puentes. 40 puentes es bastante. Si prefieres no soldar tantos:
- **Baquela perforada** (`perforada/`): ~99 cables, pero sin mandar a fabricar.
- **Doble faz** en otro taller de Medellín (Colcircuitos u otros): 0 puentes, lo más limpio.

Los archivos de **doble faz** originales siguen intactos: `medidor_ppg.kicad_pcb` y `fab/`.
