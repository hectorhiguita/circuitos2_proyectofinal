// =====================================================================
//  Medidor de ritmo cardiaco PPG — Carcasa + pinza de dedo (OpenSCAD)
//  Proyecto final Circuitos Eléctricos II — ITM
//
//  Uso:  openscad -D 'part="base"' -o base.stl ppg_carcasa.scad
//  part = "assembly" | "exploded" | "open" | "base" | "tapa"
//         | "mandibula" | "puerta" | "boton" | "check_open"
//
//  Sistema de coordenadas (vista "de uso"):
//    X = largo (la pinza está en X<0, el USB-C en X = BL)
//    Y = ancho (centrado), Z = alto (Z=0 apoyo en la mesa)
//  Las piezas exportadas ya salen orientadas para imprimir sin soportes.
// =====================================================================

part = "assembly";

/* [Calidad] */
$fn = 48;

/* [Tolerancias] */
tol      = 0.25;   // holgura general de encaje (0.2–0.3)
tol_hole = 0.2;    // holgura adicional en agujeros

/* [PCB principal (THT 1.6 mm)] */
pcb_l       = 80;    // largo (X)  = 02_pcb (80 x 52)
pcb_w       = 52;    // ancho (Y)
pcb_t       = 1.6;
pcb_hole_in = 4.0;   // centro de agujero M3 desde cada esquina
pcb_clr     = 0.5;   // holgura PCB-pared
pcb_notch   = [0.01, 0.01]; // sin muesca (el sensor entra por J1 en el borde frontal)
lead_clr    = 2.4;   // espacio bajo PCB para patas THT (sobre el techo del portapilas)
comp_h      = 16;    // altura libre sobre la PCB (SuperMini en zócalo 8.5 mm + USB-C)

/* [Carcasa] */
wall    = 2.2;
floor_t = 3.0;       // piso (incluye rebaje de 1.6 para la puerta)
lid_t   = 2.0;
lip_h   = 2.0;       // labio de centrado de la tapa
lip_t   = 1.2;
rc      = 4;         // radio de esquinas exteriores

/* [Tornillos de cierre M3 (tapa->PCB->poste base)] */
use_inserts = true;  // true: inserto termofijado M3; false: autorroscante
ins_d     = 4.0;     // agujero para inserto M3x5.7 (D ext. ~4.6)
ins_depth = 6.5;
self_tap_d = 2.6;    // M3 autorroscante en PLA/PETG
so_d      = 7.0;     // diámetro postes base
col_d     = 7.6;     // diámetro columnas tapa
m3_clear  = 3.4;
m3_head_d = 6.0;     // contrataladro cabeza allen M3 (Ø5.5)
m3_head_h = 3.0;

/* [Batería LiPo 1S BL-3.7V-1000-25C (68 x 34 x 6), a lo largo, contra la pared -Y] */
batt_l = 68; batt_w = 34; batt_h = 6;    // [X, Y, Z]
batt_clr = 0.6;
bc_wall = 1.6; bc_roof = 1.6;
bc_x0 = 8;           // borde frontal exterior del compartimiento (desde X=0)

/* [Módulos en el piso, junto a la batería] */
tp_dim = [26, 17, 1.6];   // TP4056 CAR-LIPO-USB04 (DW01 + 8205A), 26 x 17. USB-C hacia la pared trasera
tp_usb = [9.0, 3.3];      // conector USB-C [ancho Y, alto Z] sobre la placa del módulo
tp_led_from_usb = 11;     // distancia LEDs (rojo/azul) desde el borde USB (verificar)
mt_dim = [36, 17, 1.6];   // MT3608
mod_so = 1.0;             // altura de los marcos de apoyo
frame_t = 1.2; frame_h = 2.0;
door_t = 1.6;
door_screw_d = 2.5;  // piloto M3x6 autorroscante (o M2.5x6)

/* [ESP32-C3 SuperMini] */
esp_l = 22.52; esp_w = 18; esp_t = 1.0;
esp_so = 8.5;        // SuperMini en zócalo hembra 2.54 (altura del zócalo)
esp_y = -8;          // centro del SuperMini (KiCad y = 34 -> Y = 26 - 34)
usb_w = 9.0; usb_h = 3.2;
usb_cut = [11.5, 7.0];   // recorte en pared trasera (Y x Z), deja entrar el sobremolde del cable
boot_from_usb = 4.0; // distancia del botón BOOT al borde USB de la SuperMini (verificar)
boot_dy = -5.5;      // desplazamiento Y del BOOT respecto al centro de la SuperMini (verificar)
btn_h = 1.5;

/* [Pantalla TFT 1.3" ST7789 240x240 (módulo GMT130-V1.0) — MEDIR y ajustar] */
oled_pcb = [27.8, 39.2];     // [ancho Y, largo X] del módulo
oled_hole_pitch = [23.2, 34.0]; // [Y, X] entre agujeros de esquina (M2)
oled_va = [23.4, 23.4];      // área visible [ancho, alto]
oled_va_off = 4.0;           // desplazamiento del área visible hacia el borde de pines (+X)
oled_glass_t = 2.2;          // espesor vidrio + marco (separación PCB-tapa)
oled_cx = 30;                // centro del módulo en X
win_margin = 0.8;

/* [Buzzer activo 12 mm] */
buz_d = 12; buz_h = 9.5;
buz_pos = [wall + pcb_clr + 65.5, 26 - 9];   // KiCad (65.5, 9)

/* [Interruptor SS12D00 (pared lateral +Y, bajo la PCB)] */
sw_body = [8.9, 4.6, 4.8];   // pocket [X, prof Y, Z]
sw_slot = [6.0, 3.0];        // ranura del actuador [X, Z]
sw_x = 9.5; sw_z = 7;   // pared +Y, delante del MT3608

/* [Pinza de dedo] */
CL = 42;          // largo de la pinza (X)
CW = 30;          // ancho mandíbula inferior
LJ_H = 18;        // alto mandíbula inferior (parte de la base)
UJ_H = 20;        // alto mandíbula superior
sad_r = 11;       // radio del canal para el dedo
sad_d = 4.5;      // profundidad del canal en cada mandíbula
x_stop = -16;     // tope de la punta del dedo
x_s = -25;        // posición X del eje LED/fotodiodo
shroud = 2.0;     // tubo de sombra sobre el sensor
led_d = 5.8 + 0.3;   // LED 5 mm (pestaña 5.8) + holgura
led_len = 8.6;
pd_type = "5mm";  // "5mm" o "bpw34"
bpw34 = [5.4, 4.3, 1.2];
ch_diag = 4.5;    // diagonal del canal de cables (perfil rombo, sin soportes)
pd_ch_z = 5.5;    // altura del canal del fotodiodo
led_ch_z = 34;    // altura del canal del LED
x_p = -7;         // eje de bisagra
z_p = LJ_H + 5;
hinge_r = 4.5;
ch_t = 4.5;       // espesor de las orejas de bisagra
ch_l = 13;        // largo de las orejas
hinge_d = 3.3;    // eje tornillo M3
open_max = 35;    // apertura máxima prevista (grados)
sk_t = 2.0;       // faldón lateral antiluz
sk_h = 5.0;
band_x = [-30, -37]; // ranuras para banda elástica
band_w = 3.5; band_dp = 1.5;

// ------------------------- derivados ---------------------------------
in_l = pcb_l + 2*pcb_clr;
mod_strip = 17 + 2*1.2 + 0.6 + 1.0;      // franja +Y para TP4056 y MT3608
in_w = max(pcb_w + 2*pcb_clr, batt_w + 2*batt_clr + 2*1.6 + mod_strip);
BL = in_l + 2*wall;
BW = in_w + 2*wall;
bc_h = max(batt_h + 1.0, 9.5);       // altura mínima para los módulos de la franja
roof_top = floor_t + bc_h + bc_roof;
pcb_z = roof_top + lead_clr;          // cara inferior PCB
pcb_top = pcb_z + pcb_t;
lid_under = pcb_top + comp_h;
BH = lid_under + lid_t;
pcb_x0 = wall + pcb_clr;
holes = [for (hx=[pcb_x0+pcb_hole_in, pcb_x0+pcb_l-pcb_hole_in])
         for (hy=[-(pcb_w/2-pcb_hole_in), pcb_w/2-pcb_hole_in]) [hx,hy]];
bc_l = batt_l + 2*batt_clr + 2*bc_wall;
tp_x1 = BL - wall;                                  // borde USB del TP4056 contra la pared trasera
tp_pos = [tp_x1 - tp_dim[0], in_w/2 - frame_t - 0.4 - tp_dim[1]];   // esquina [X, Y] (pegado a la pared +Y)
tp_usb_z = floor_t + mod_so + tp_dim[2] + tp_usb[1]/2;
mt_pos = [tp_pos[0] - mt_dim[0] - 2*frame_t - 1.5, tp_pos[1]];   // detrás del TP4056, misma franja
bc_w = batt_w + 2*batt_clr + 2*bc_wall;
bc_yc = -in_w/2 + bc_w/2;                          // compartimiento pegado a la pared -Y
door_screws = [[bc_x0 - 3, bc_yc], [bc_x0 + bc_l + 2.4, bc_yc]];
esp_x1 = pcb_x0 + pcb_l + 0.8;        // borde USB (sobresale 0.8)
esp_z = pcb_top + esp_so;
usb_z = esp_z + esp_t + usb_h/2;
boot_pos = [esp_x1 - boot_from_usb, esp_y + boot_dy];
uj_top = LJ_H + UJ_H;
kw = CW - 2*ch_t - 2*0.4;             // ancho del nudillo
uj_ow = CW + 2*(0.4 + sk_t);          // ancho exterior mandíbula sup.
z_sad_lo = LJ_H + (sad_r - sad_d);    // eje canal inferior
z_sad_up = LJ_H - (sad_r - sad_d);    // eje canal superior
pd_top = LJ_H - sad_d - shroud;
pd_step = pd_top - led_len;
led_step = LJ_H + sad_d + shroud + led_len;

echo(str("Caja exterior: ", BL, " x ", BW, " x ", BH, " mm; total con pinza: ", BL+CL+4, " mm"));
echo(str("PCB cara inferior Z=", pcb_z, "  USB-C centro Z=", usb_z));
echo(str("Tornillo cierre: M3x", ceil((BH - m3_head_h) - (pcb_z - ins_depth + 1))));

// ------------------------- utilidades --------------------------------
module rbox(l, w, h, r) {
    hull() for (x=[r, l-r], y=[-w/2+r, w/2-r]) translate([x,y,0]) cylinder(r=r, h=h);
}
module teardrop2d(d) { hull() { circle(d=d); translate([0, d/2*1.414]) square(0.01, center=true); } }
// agujero horizontal a lo largo de Y, punta hacia +Z (up) o -Z
module teardropY(d, len, up=true) {
    rotate([90,0,0]) linear_extrude(len, center=true) mirror([0, up?0:1]) teardrop2d(d);
}
// canal rombo a lo largo de X desde x0 a x1
module diamondX(x0, x1, y, z, diag) {
    translate([x0, y, z]) rotate([0,90,0]) rotate([0,0,45])
        linear_extrude(x1-x0) square(diag/1.414, center=true);
}
module cylX(x0, x1, y, z, r) { translate([x0,y,z]) rotate([0,90,0]) cylinder(r=r, h=x1-x0); }

// ============================== BASE =================================
module door2d(grow=0) {
    offset(delta=grow) union() {
        translate([bc_x0, bc_yc - bc_w/2]) square([bc_l, bc_w]);
        for (sc=door_screws) hull() {
            translate(sc) circle(r=4.5);
            translate([sc[0] > bc_x0 ? bc_x0 + bc_l - 1 : bc_x0, sc[1] - 4.5]) square([1, 9]);
        }
    }
}

module lower_jaw_solid() {
    // bloque con esquinas frontales redondeadas, se funde con la pared frontal
    hull() {
        for (y=[-CW/2+3, CW/2-3]) translate([-CL+3, y, 0]) cylinder(r=3, h=LJ_H);
        translate([0, -CW/2, 0]) cube([wall*0.5, CW, LJ_H]);
    }
    // orejas de bisagra
    for (s=[-1,1]) hull() {
        translate([-ch_l, s>0 ? CW/2-ch_t : -CW/2, 0]) cube([ch_l + wall*0.5, ch_t, LJ_H]);
        translate([x_p, s>0 ? CW/2-ch_t : -CW/2, z_p]) rotate([-90,0,0]) cylinder(r=hinge_r, h=ch_t);
        translate([0, s>0 ? CW/2-ch_t : -CW/2, 0]) cube([wall*0.5, ch_t, z_p]);
    }
}

module lower_jaw_cuts() {
    // canal del dedo con tope elíptico
    cylX(-CL-5, x_stop, 0, z_sad_lo, sad_r);
    translate([x_stop, 0, z_sad_lo]) scale([0.5,1,1]) sphere(r=sad_r);
    // abocinado de entrada
    translate([-CL-0.01, 0, z_sad_lo]) rotate([0,90,0]) cylinder(r1=sad_r+2, r2=sad_r, h=3);
    // fotodiodo con tubo de sombra
    if (pd_type == "bpw34") {
        translate([x_s, 0, pd_top - bpw34[2]/2 - 0.5])
            linear_extrude(LJ_H) square([bpw34[0]+0.4, bpw34[1]+0.4], center=true);
        translate([x_s, 0, pd_ch_z]) cylinder(d=3, h=LJ_H);
    } else {
        translate([x_s, 0, pd_step]) cylinder(d=led_d, h=LJ_H);
    }
    // canal de cables hacia el interior
    diamondX(x_s, wall + 1, 0, pd_ch_z, ch_diag);
    // eje de bisagra + alojamiento de tuerca M3 en la oreja -Y
    translate([x_p, 0, z_p]) teardropY(hinge_d, CW + 10, up=true);
    translate([x_p, -CW/2 - 0.01, z_p]) rotate([-90,0,0]) rotate([0,0,30]) cylinder(d=6.7, h=2.6, $fn=6);
    // ranuras de banda elástica (lados + fondo)
    for (gx=band_x) {
        translate([gx-band_w/2, -CW/2-1, -1]) cube([band_w, CW+2, band_dp+1]);
        for (s=[-1,1]) translate([gx-band_w/2, s>0 ? CW/2-band_dp : -CW/2-1, -1]) cube([band_w, band_dp+1, LJ_H+1]);
    }
}

module base() {
    difference() {
        union() {
            // casco
            difference() {
                rbox(BL, BW, lid_under, rc);
                translate([wall, 0, floor_t]) rbox(in_l, in_w, lid_under, rc-wall);
            }
            // postes de PCB unidos a las esquinas
            for (h=holes) hull() {
                translate([h[0], h[1], floor_t-0.01]) cylinder(d=so_d, h=pcb_z-floor_t+0.01);
                translate([h[0] < BL/2 ? wall-0.01 : BL-wall-1+0.01,
                           h[1] < 0 ? -in_w/2-0.01 : in_w/2-1+0.01, floor_t-0.01])
                    cube([1, 1, pcb_z-floor_t+0.01]);
            }
            // compartimiento de pilas (techo = puente, sin soportes)
            translate([bc_x0, bc_yc - bc_w/2, floor_t-0.01]) difference() {
                cube([bc_l, bc_w, bc_h + bc_roof]);
                translate([bc_wall, bc_wall, -1]) cube([bc_l-2*bc_wall, bc_w-2*bc_wall, bc_h+1]);
            }
            // torretas de tornillos de la puerta
            for (s=door_screws) translate([s[0], s[1], floor_t-0.01]) cylinder(d=6.5, h=6);
            // marco del interruptor (pared +Y)
            translate([sw_x - sw_body[0]/2 - 1.2, in_w/2 - sw_body[1], floor_t-0.01])
                cube([sw_body[0] + 2.4, sw_body[1] + 0.01, sw_z + sw_body[2]/2 + 1.2 - floor_t]);
            lower_jaw_solid();
            // marcos de apoyo: TP4056 (contra pared trasera y -Y) y MT3608
            for (m=[[tp_pos, tp_dim], [mt_pos, mt_dim]]) translate([m[0][0], m[0][1], floor_t - 0.01])
                difference() {
                    translate([-frame_t-0.3, -frame_t-0.3, 0]) cube([m[1][0] + 2*frame_t + 0.6, m[1][1] + 2*frame_t + 0.6, mod_so + frame_h]);
                    translate([-0.3, -0.3, mod_so]) cube([m[1][0] + 0.6, m[1][1] + 0.6, 10]);
                    translate([3, 3, -1]) cube([m[1][0] - 6, m[1][1] - 6, 10]);     // ventana (componentes de abajo)
                    translate([m[1][0] - 1, -5, mod_so]) cube([10, m[1][1] + 10, 10]); // extremo USB abierto
                }
        }
        // --- recortes ---
        // insertos / autorroscante en postes
        for (h=holes) {
            translate([h[0], h[1], pcb_z - ins_depth]) cylinder(d=use_inserts ? ins_d : self_tap_d, h=ins_depth+1);
            translate([h[0], h[1], pcb_z - ins_depth - 4]) cylinder(d=self_tap_d, h=5);
        }
        // puerta de pilas: rebaje + abertura
        translate([0,0,-1]) linear_extrude(door_t + 1) door2d(0.3);
        translate([bc_x0 + bc_wall, bc_yc - bc_w/2 + bc_wall, -1]) cube([bc_l-2*bc_wall, bc_w-2*bc_wall, floor_t+2]);
        for (s=door_screws) translate([s[0], s[1], 0]) cylinder(d=door_screw_d, h=floor_t + 5.5);
        // muesca para abrir la puerta con uña
        translate([bc_x0 + bc_l/2 - 5, bc_yc + bc_w/2 - 0.2, -1]) cube([10, 2.5, door_t + 1]);  // muesca para la uña (lado +Y)
        // paso de cables del portapilas por el techo
        translate([bc_x0 + bc_l - bc_wall - 5, bc_yc + bc_w/2 - bc_wall - 4, roof_top - 5]) cylinder(d=5, h=10);
        // USB-C (pared trasera)
        hull() for (y=[-1,1], z=[-1,1])
            translate([BL - wall - 1, esp_y + y*(usb_cut[0]/2-1.5), usb_z + z*(usb_cut[1]/2-1.5)])
                rotate([0,90,0]) cylinder(r=1.5, h=wall+2);
        // USB-C del TP4056 (CARGA), nivel del piso
        hull() for (y=[-1,1], z=[-1,1])
            translate([BL - wall - 1, tp_pos[1] + tp_dim[1]/2 + y*(usb_cut[0]/2-1.5), tp_usb_z + z*(usb_cut[1]/2-1.5)])
                rotate([0,90,0]) cylinder(r=1.5, h=wall+2);
        // ventana para ver los LEDs de carga (pared -Y, a la altura del módulo)
        translate([tp_x1 - tp_led_from_usb - 3, in_w/2 - 1, floor_t + mod_so + tp_dim[2]])
            cube([6, wall + 2.5, 2.5]);
        // rótulos en relieve hundido sobre cada USB-C
        for (t=[["PROG", esp_y, usb_z + usb_cut[1]/2 + 2.6], ["CARGA", tp_pos[1] + tp_dim[1]/2, tp_usb_z + usb_cut[1]/2 + 2.6]])
            translate([BL - 0.5, t[1], t[2]]) rotate([90, 0, 90])
                linear_extrude(1) text(t[0], size=3, halign="center", valign="center", font="Liberation Sans:style=Bold");
        // interruptor: ranura del actuador + bolsillo
        translate([sw_x - sw_slot[0]/2, in_w/2 - 1, sw_z - sw_slot[1]/2]) cube([sw_slot[0], wall+2, sw_slot[1]]);
        translate([sw_x - sw_body[0]/2, in_w/2 - sw_body[1] - 1, sw_z - sw_body[2]/2]) cube([sw_body[0], sw_body[1] + 1.01, sw_body[2]]);
        // paso del cable del LED por la pared frontal
        diamondX(-1, wall + 1, 0, led_ch_z, ch_diag + 0.5);
        lower_jaw_cuts();
    }
}

// ======================== MANDÍBULA SUPERIOR =========================
// Geometría en posición de uso (cerrada). Exportación: invertida.
module upper_jaw() {
    difference() {
        union() {
            // cuerpo principal con faldones
            hull() {
                for (y=[-uj_ow/2+3, uj_ow/2-3]) translate([-CL+3, y, LJ_H - sk_h]) cylinder(r=3, h=UJ_H + sk_h);
                translate([-ch_l-1.4-1, -uj_ow/2, LJ_H - sk_h]) cube([1, uj_ow, UJ_H + sk_h]);
            }
            translate([-ch_l-1.4-1, -CW/2, LJ_H]) cube([1.01, CW, UJ_H]);
            // sobre las orejas: ancho completo
            translate([-ch_l-0.4-1.01, -CW/2, z_p + hinge_r + 1]) cube([x_p + ch_l + 0.4 + 1.01, CW, uj_top - z_p - hinge_r - 1]);
            // nudillo
            translate([-ch_l-0.4-1.01, -kw/2, LJ_H]) cube([x_p + ch_l + 0.4 + 1.01, kw, UJ_H]);
            translate([x_p, 0, z_p]) rotate([90,0,0]) cylinder(r=hinge_r, h=kw, center=true);
            // pestaña frontal para levantar
            hull() for (y=[-CW/2+5, CW/2-5]) translate([-CL-3, y, uj_top-3]) cylinder(r=2, h=3);
        }
        // hueco para la mandíbula inferior bajo los faldones
        translate([-CL-10, -CW/2-0.4, LJ_H - sk_h - 1]) cube([CL+10, CW+0.8, sk_h + 1]);
        // canal del dedo
        cylX(-CL-10, x_stop, 0, z_sad_up, sad_r);
        translate([x_stop, 0, z_sad_up]) scale([0.5,1,1]) sphere(r=sad_r);
        translate([-CL-0.01, 0, z_sad_up]) rotate([0,90,0]) cylinder(r1=sad_r+2, r2=sad_r, h=3);
        // LED IR con tubo de sombra
        translate([x_s, 0, LJ_H-1]) cylinder(d=led_d, h=led_step - LJ_H + 1);
        diamondX(x_s, 5, 0, led_ch_z, ch_diag);
        // eje
        translate([x_p, 0, z_p]) teardropY(hinge_d, CW + 10, up=false);
        // chaflán trasero para que gire sin chocar con la pared frontal
        for (a=[0:5:open_max]) translate([x_p,0,z_p]) rotate([0,-a,0]) translate([-x_p,0,-z_p])
            translate([-0.8, -50, z_p]) cube([50, 100, 50]);
        // ranuras de banda elástica (arriba + lados)
        for (gx=band_x) {
            translate([gx-band_w/2, -uj_ow/2-1, uj_top-band_dp]) cube([band_w, uj_ow+2, 5]);
            for (s=[-1,1]) translate([gx-band_w/2, s>0 ? uj_ow/2-band_dp : -uj_ow/2-1, LJ_H-sk_h-1]) cube([band_w, band_dp+1, UJ_H+sk_h+2]);
        }
    }
}

// ============================== TAPA =================================
module oled_holes() {
    for (sx=[-1,1], sy=[-1,1])
        translate([oled_cx + sx*oled_hole_pitch[1]/2, sy*oled_hole_pitch[0]/2]) children();
}
module lid() {
    win = [oled_va[1] + 2*win_margin, oled_va[0] + 2*win_margin];   // [X, Y]
    wc = [oled_cx + oled_va_off, 0];
    difference() {
        union() {
            translate([0,0,lid_under]) rbox(BL, BW, lid_t, rc);
            // labio de centrado
            translate([0,0,lid_under - lip_h]) difference() {
                translate([wall+tol, 0, 0]) rbox(in_l-2*tol, in_w-2*tol, lip_h+0.01, rc-wall);
                translate([wall+tol+lip_t, 0, -1]) rbox(in_l-2*tol-2*lip_t, in_w-2*tol-2*lip_t, lip_h+2, rc-wall);
            }
            // columnas que prensan la PCB
            for (h=holes) translate([h[0], h[1], pcb_top + 0.2]) cylinder(d=col_d, h=lid_under - pcb_top - 0.19);
            // soportes OLED
            oled_holes() translate([0,0,lid_under - oled_glass_t]) cylinder(d=4.5, h=oled_glass_t + 0.01);
            // guía del pulsador BOOT
            translate([boot_pos[0], boot_pos[1], lid_under - 4]) cylinder(d=7.5, h=4.01);
        }
        for (h=holes) {
            translate([h[0], h[1], 0]) cylinder(d=m3_clear, h=100);
            translate([h[0], h[1], BH - m3_head_h]) cylinder(d=m3_head_d, h=10);
        }
        // ventana OLED con bisel exterior
        translate([wc[0], wc[1], lid_under - 1]) linear_extrude(lid_t + 2) square(win, center=true);
        translate([wc[0], wc[1], BH - 1.0]) linear_extrude(1.01, scale=[(win[0]+2)/win[0], (win[1]+2)/win[1]]) square(win, center=true);
        // pilotos M2 OLED
        oled_holes() translate([0,0,lid_under - oled_glass_t - 1]) cylinder(d=1.7, h=oled_glass_t + 1 + lid_t - 0.4);
        // rejilla del buzzer
        for (dx=[-4:2.6:4], dy=[-4:2.6:4]) if (dx*dx+dy*dy <= 25)
            translate([buz_pos[0]+dx, buz_pos[1]+dy, lid_under-1]) cylinder(d=1.6, h=lid_t+2, $fn=16);
        // pulsador BOOT
        translate([boot_pos[0], boot_pos[1], lid_under - 5]) cylinder(d=4.2, h=10);
        // cable del LED
        diamondX(-1, wall + 1, 0, led_ch_z, ch_diag + 0.5);
    }
}

// ========================== PUERTA PILAS =============================
module door() {
    difference() {
        linear_extrude(door_t) door2d(0);
        for (s=door_screws) translate([s[0], s[1], -0.01]) {
            cylinder(d=m3_clear, h=5);
            cylinder(d1=6.2, d2=m3_clear, h=1.4);   // avellanado (tornillo cabeza plana)
        }
    }
}

// ========================== PULSADOR BOOT ============================
plg_len = (BH + 1.5) - (esp_z + esp_t + btn_h);
module plunger() {
    cylinder(d=6.5, h=1.2);
    cylinder(d=3.8, h=plg_len - 0.6);
    translate([0,0,plg_len-0.6]) cylinder(d1=3.8, d2=2.8, h=0.6);
}

// ======================= MODELOS DE REFERENCIA =======================
module dummies(show_finger=true) {
    // PCB
    color("darkgreen") translate([pcb_x0, -pcb_w/2, pcb_z]) difference() {
        cube([pcb_l, pcb_w, pcb_t]);
        for (h=holes) translate([h[0]-pcb_x0, h[1]+pcb_w/2, -1]) cylinder(d=3.2, h=5);
        translate([-1, pcb_w/2-pcb_notch[1]/2, -1]) cube([pcb_notch[0]+1, pcb_notch[1], 5]);
    }
    // ESP32-C3 SuperMini
    color("royalblue") translate([esp_x1 - 0.8 - esp_l, esp_y - esp_w/2, esp_z]) cube([esp_l, esp_w, esp_t]);
    color("silver") translate([esp_x1 - 7.3, esp_y - usb_w/2, esp_z + esp_t]) cube([7.3, usb_w, usb_h]);
    color("black") for (dy=[-7.62, 7.62]) translate([esp_x1 - 0.8 - esp_l + 1.5, esp_y + dy - 1.27, pcb_top]) cube([20.3, 2.54, esp_so]);
    color("white") translate([boot_pos[0], boot_pos[1], esp_z + esp_t]) cylinder(d=2.5, h=btn_h);
    // LM324 DIP-14
    color("#222") translate([20, -12, pcb_top]) cube([19.3, 6.4, 3.5]);
    // buzzer
    color("#111") translate([buz_pos[0], buz_pos[1], pcb_top]) cylinder(d=buz_d, h=buz_h);
    // electrolíticos
    color("#333") for (p=[[44,12],[44,-2]]) translate([p[0],p[1],pcb_top]) cylinder(d=6.3, h=11);
    // OLED
    color("#1a3a6a") translate([oled_cx - oled_pcb[1]/2, -oled_pcb[0]/2, lid_under - oled_glass_t - 1.2]) cube([oled_pcb[1], oled_pcb[0], 1.2]);
    color("#050505") translate([oled_cx - 19.3/2 + oled_va_off, -26.7/2, lid_under - oled_glass_t]) cube([19.3, 26.7, oled_glass_t]);
    color("cyan") translate([oled_cx + oled_va_off - oled_va[1]/2, -oled_va[0]/2, lid_under - 0.05]) cube([oled_va[1], oled_va[0], 0.05]);
    // LiPo 103450
    color("#c0c0c0") translate([bc_x0 + bc_wall + batt_clr, bc_yc - batt_w/2, floor_t + 0.3]) cube([batt_l, batt_w, batt_h]);
    // TP4056 y MT3608
    color("#1565c0") translate([tp_pos[0], tp_pos[1], floor_t + mod_so]) cube(tp_dim);
    color("silver") translate([tp_x1 - 7.3, tp_pos[1] + tp_dim[1]/2 - tp_usb[0]/2, floor_t + mod_so + tp_dim[2]]) cube([7.3, tp_usb[0], tp_usb[1]]);
    color("#0d47a1") translate([mt_pos[0], mt_pos[1], floor_t + mod_so]) cube(mt_dim);
    color("#222") translate([mt_pos[0] + 14, mt_pos[1] + 5, floor_t + mod_so + mt_dim[2]]) cube([7, 7, 4]);
    // interruptor
    color("#ddd") translate([sw_x - 4.35, in_w/2 - 4.4, sw_z - 2.35]) cube([8.7, 4.4, 4.7]);
    color("black") translate([sw_x - 0.75, in_w/2, sw_z - 0.75]) cube([1.5, 4, 1.5]);
    // LED IR y fotodiodo
    color("#8a2be2", 0.8) translate([x_s, 0, LJ_H + sad_d + shroud]) { cylinder(d=5, h=led_len - 2.5); translate([0,0,led_len-1]) cylinder(d=5.8, h=1); }
    color("#222") translate([x_s, 0, pd_step]) { cylinder(d=5, h=led_len - 2.5); cylinder(d=5.8, h=1); translate([0,0,led_len-2.5]) sphere(d=5); }
    color("#8a2be2") translate([x_s, 0, LJ_H + sad_d + shroud]) sphere(d=5);
    if (show_finger) color("#e0a080", 0.55) hull() {
        translate([-CL-25, 0, LJ_H]) rotate([0,90,0]) scale([0.8,1,1]) cylinder(d=17, h=10);
        translate([x_stop + 1, 0, LJ_H]) scale([0.5,0.9,0.75]) sphere(d=17);
    }
}

// ============================ SALIDAS ================================
c_body = "#3a3a3a";  c_lid = "#5a5a5a";  c_clip = "#151515";

module assembled(open_a=0, show_finger=true) {
    color(c_body) base();
    color(c_lid) lid();
    color(c_clip) translate([x_p,0,z_p]) rotate([0,open_a,0]) translate([-x_p,0,-z_p]) upper_jaw();
    color("#777") door();
    color("orange") translate([boot_pos[0], boot_pos[1], esp_z + esp_t + btn_h]) plunger();
    dummies(show_finger);
}

module exploded() {
    e = 1.0;
    color(c_body) base();
    color(c_lid) translate([0,0,45*e]) lid();
    color(c_clip) translate([-15*e,0,25*e]) upper_jaw();
    color("#777") translate([0,0,-25*e]) door();
    color("orange") translate([boot_pos[0], boot_pos[1], esp_z + esp_t + btn_h + 30*e]) plunger();
    translate([0,0,18*e]) dummies(false);
}

if (part == "assembly") assembled(0, true);
else if (part == "open") assembled(22, false);
else if (part == "exploded") exploded();
else if (part == "base") base();
else if (part == "tapa") translate([0,0,BH]) rotate([180,0,0]) lid();               // cara superior sobre la cama
else if (part == "mandibula") translate([0,0,uj_top]) rotate([180,0,0]) upper_jaw(); // invertida
else if (part == "puerta") translate([0,0,door_t]) rotate([180,0,0]) door();        // cara exterior sobre la cama
else if (part == "boton") plunger();
else if (part == "check_open") {
    // interferencia mandíbula-base a varias aperturas (debe quedar vacío)
    for (a=[0, 10, 20, 30]) intersection() {
        base();
        translate([x_p,0,z_p]) rotate([0,a,0]) translate([-x_p,0,-z_p]) upper_jaw();
    }
}
else if (part == "check_lid") intersection() { base(); lid(); }
