# Carcasa y pinza (OpenSCAD)

Caja 85.4 × 63.8 × 36.1 mm. Largo con la pinza: 131 mm. Medidas tomadas de `../02_pcb` (PCB 80 × 52).

```
 tapa  : OLED (ventana) · rejilla del buzzer · botón BOOT
 ───── : PCB principal (LM324, SuperMini en zócalo)        <- 4 tornillos M3
 piso  : LiPo 68×34×6 a lo largo (lado -Y) | MT3608 + TP4056 en fila (lado +Y)
 pared trasera: USB-C "PROG" (arriba) y "CARGA" (abajo) + ventana de LEDs (lado +Y)
 frente: pinza con bisagra M3; LED IR arriba, fotodiodo abajo, enfrentados
```

## Piezas (`stl/`)
| Pieza | Archivo | Color | Orientación |
|---|---|---|---|
| Base | `base.stl` | Gris/negro | Como sale |
| Tapa | `tapa.stl` | Gris | Cara superior en la cama |
| Mandíbula superior | `mandibula.stl` | **Negro** (bloquea la luz) | Invertida, como sale |
| Puerta de batería | `puerta.stl` | Cualquiera | Cara exterior en la cama |
| Botón BOOT | `boton.stl` | Cualquiera | Como sale |

Impresión: capa 0.2 mm, relleno 20 %, 3 perímetros, PLA o PETG. Sin soportes.
**La base y la mandíbula en negro**: la luz de afuera da falsos pulsos.

## Tornillería
- 4 × M3×23 (o M3×25) cabeza allen + 4 insertos M3 termofijados (o autorroscante, `use_inserts=false`)
- 1 × M3×30 + tuerca M3 (eje de la bisagra)
- 2 × M3×6 autorroscantes (puerta de batería)
- 1 liga o banda elástica (cierra la pinza)
- 4 × M2×4 (OLED a la tapa)

## Armado
1. Pega la LiPo en su hueco con cinta doble faz. Pasa los cables por el agujero del techo.
2. Pon el TP4056 en su marco con el USB-C contra la pared trasera. Pon el MT3608 en el suyo.
3. Suelda los cables de la batería, el interruptor y los módulos al conector J5 (tabla en `../02_pcb/README.md`).
4. Mete el LED IR en la mandíbula superior y el fotodiodo en la inferior. Pasa los cables por los canales hasta J1.
5. Atornilla la OLED a la tapa y suelda sus 4 cables a J4.
6. Pon la PCB sobre los postes. Cierra la tapa con los 4 M3.
7. Arma la bisagra con el M3×30 y pon la liga.

## Cambiar medidas
Todo está en la parte de parámetros de `ppg_carcasa.scad`. Exportar:
```bash
openscad -D 'part="base"' -o stl/base.stl ppg_carcasa.scad      # base | tapa | mandibula | puerta | boton
openscad -D 'part="exploded"' -o img/exploded.png ppg_carcasa.scad
```
Medir antes de imprimir: el TP4056 (`tp_dim`), el MT3608 (`mt_dim`), la LiPo (`batt_*`) y la posición de los LEDs del TP4056 (`tp_led_from_usb`).
