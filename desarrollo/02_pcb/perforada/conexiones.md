# Conexiones en baquela (lado soldadura)

Baquela universal 9 × 7 cm (35 × 27 agujeros). Ocupa 33 columnas × 18 filas.
Columnas = letras (izquierda a derecha visto desde los componentes), filas = números.
Cada línea = un cable aislado (wire-wrap o UTP) entre dos agujeros. GND, +5V y +3V3: cable más grueso.
Total: **102 conexiones**. Marca cada casilla al soldarla.

Desvío máximo pin-agujero: 0.12 mm (JST de 2.50 mm de paso; entra sin problema).

## +3V3  (6 pines)
- [ ] J2.3 (AE11)  →  J4.2 (Z8)
- [ ] J4.2 (Z8)  →  R15.1 (S4)
- [ ] R15.1 (S4)  →  C12.1 (O16)
- [ ] C12.1 (O16)  →  D2.1 (E14)
- [ ] D2.1 (E14)  →  R17.1 (F12)

## +5V  (9 pines)
- [ ] U1.4 (P9)  →  D1.1 (S16)
- [ ] D1.1 (S16)  →  C11.1 (V17)
- [ ] D1.1 (S16)  →  D4.1 (H16)
- [ ] D4.1 (H16)  →  C10.1 (H14)
- [ ] C10.1 (H14)  →  J1.3 (D9)
- [ ] J1.3 (D9)  →  R1.1 (F3)
- [ ] U1.4 (P9)  →  BZ1.1 (Z4)
- [ ] BZ1.1 (Z4)  →  J2.1 (AG11)

## GND  (24 pines)
- [ ] U1.11 (S9)  →  C2.2 (W9)
- [ ] C2.2 (W9)  →  J4.1 (Y8)
- [ ] C2.2 (W9)  →  C15.2 (V12)
- [ ] C15.2 (V12)  →  D3.2 (W14)
- [ ] D3.2 (W14)  →  C7.2 (U14)
- [ ] D3.2 (W14)  →  C11.2 (W17)
- [ ] D3.2 (W14)  →  TP7.1 (Y13)
- [ ] C2.2 (W9)  →  R16.2 (W3)
- [ ] C7.2 (U14)  →  C12.2 (Q16)
- [ ] C12.2 (Q16)  →  R14.2 (P18)
- [ ] R16.2 (W3)  →  J5.8 (R2)
- [ ] J5.8 (R2)  →  J5.6 (P2)
- [ ] J5.6 (P2)  →  J5.5 (O2)
- [ ] R14.2 (P18)  →  Q1.1 (K17)
- [ ] Q1.1 (K17)  →  C17.2 (G17)
- [ ] Q1.1 (K17)  →  C10.2 (J14)
- [ ] C10.2 (J14)  →  R18.2 (N12)
- [ ] R18.2 (N12)  →  C14.2 (K9)
- [ ] C14.2 (K9)  →  C16.2 (H10)
- [ ] C16.2 (H10)  →  C13.2 (H5)
- [ ] C13.2 (H5)  →  R2.2 (I1)
- [ ] C16.2 (H10)  →  J1.2 (D8)
- [ ] TP7.1 (Y13)  →  J2.2 (AF11)

## +5V_B  (2 pines)
- [ ] J5.7 (Q2)  →  D1.2 (T16)

## ADC  (5 pines)
- [ ] J2.7 (AA11)  →  D3.1 (V14)
- [ ] D3.1 (V14)  →  C7.1 (S14)
- [ ] C7.1 (S14)  →  D2.2 (F14)
- [ ] D2.2 (F14)  →  R10.2 (D13)

## BAT  (2 pines)
- [ ] J5.1 (K2)  →  J5.2 (L2)

## BUF  (4 pines)
- [ ] U1.1 (P6)  →  U1.2 (P7)
- [ ] U1.2 (P7)  →  U1.5 (P10)
- [ ] U1.2 (P7)  →  TP2.1 (W7)

## BUZ  (2 pines)
- [ ] J3.6 (AB17)  →  R12.1 (C15)

## BZK  (3 pines)
- [ ] Q1.3 (M17)  →  D4.2 (I16)
- [ ] Q1.3 (M17)  →  BZ1.2 (AC4)

## INV1  (4 pines)
- [ ] U1.6 (P11)  →  C5.2 (K7)
- [ ] C5.2 (K7)  →  R5.2 (K5)
- [ ] R5.2 (K5)  →  R4.1 (V5)

## INV2  (5 pines)
- [ ] U1.13 (S7)  →  C9.2 (R14)
- [ ] C9.2 (R14)  →  RV1.2 (M14)
- [ ] RV1.2 (M14)  →  RV1.3 (L14)
- [ ] RV1.3 (L14)  →  R8.1 (A11)

## LED_A  (2 pines)
- [ ] J1.1 (D7)  →  R1.2 (G3)

## N1  (3 pines)
- [ ] U1.3 (P8)  →  R3.1 (P4)
- [ ] R3.1 (P4)  →  C1.2 (N5)

## N2  (3 pines)
- [ ] U1.12 (S8)  →  R11.1 (M10)
- [ ] R11.1 (M10)  →  C8.2 (K11)

## P6  (5 pines)
- [ ] U1.14 (S6)  →  TP5.1 (X11)
- [ ] U1.14 (S6)  →  C9.1 (P14)
- [ ] C9.1 (P14)  →  R9.1 (I18)
- [ ] R9.1 (I18)  →  R10.1 (C13)

## PRE  (5 pines)
- [ ] U1.7 (P12)  →  R6.1 (U7)
- [ ] R6.1 (U7)  →  TP3.1 (T2)
- [ ] U1.7 (P12)  →  C5.1 (I7)
- [ ] C5.1 (I7)  →  R5.1 (J5)

## QB  (2 pines)
- [ ] Q1.2 (L17)  →  R12.2 (D15)

## SENS  (4 pines)
- [ ] J1.4 (D10)  →  TP1.1 (I3)
- [ ] TP1.1 (I3)  →  R2.1 (H1)
- [ ] TP1.1 (I3)  →  C1.1 (L5)

## SKA  (3 pines)
- [ ] R6.2 (V7)  →  R7.1 (M8)
- [ ] R7.1 (M8)  →  C3.1 (F8)

## SKB  (3 pines)
- [ ] U1.10 (S10)  →  C2.1 (U9)
- [ ] U1.10 (S10)  →  R7.2 (N8)

## SKO  (5 pines)
- [ ] U1.8 (S12)  →  U1.9 (S11)
- [ ] U1.9 (S11)  →  C8.1 (I11)
- [ ] C8.1 (I11)  →  C3.2 (H8)
- [ ] U1.9 (S11)  →  TP4.1 (V1)

## TFT_BLK  (2 pines)
- [ ] J2.5 (AC11)  →  J4.7 (AE8)

## TFT_DC  (2 pines)
- [ ] J3.3 (AE17)  →  J4.6 (AD8)

## TFT_RES  (2 pines)
- [ ] J3.1 (AG17)  →  J4.5 (AC8)

## TFT_SCK  (2 pines)
- [ ] J2.4 (AD11)  →  J4.3 (AA8)

## TFT_SDA  (2 pines)
- [ ] J3.2 (AF17)  →  J4.4 (AB8)

## VBAT_S  (4 pines)
- [ ] J2.8 (Z11)  →  R14.1 (O18)
- [ ] R14.1 (O18)  →  C17.1 (E17)
- [ ] C17.1 (E17)  →  R13.2 (D17)

## VREF1  (7 pines)
- [ ] R15.2 (T4)  →  R3.2 (Q4)
- [ ] R15.2 (T4)  →  R16.1 (V3)
- [ ] R16.1 (V3)  →  R4.2 (W5)
- [ ] R4.2 (W5)  →  TP6.1 (X4)
- [ ] R3.2 (Q4)  →  C13.1 (G5)
- [ ] C13.1 (G5)  →  C14.1 (I9)

## VREF2  (6 pines)
- [ ] R17.2 (G12)  →  C16.1 (F10)
- [ ] C16.1 (F10)  →  R8.2 (B11)
- [ ] R17.2 (G12)  →  R18.1 (M12)
- [ ] R18.1 (M12)  →  R11.2 (N10)
- [ ] R18.1 (M12)  →  C15.1 (U12)

## VSW  (3 pines)
- [ ] J5.3 (M2)  →  J5.4 (N2)
- [ ] J5.3 (M2)  →  R13.1 (C17)

## X9  (2 pines)
- [ ] RV1.1 (N14)  →  R9.2 (J18)

