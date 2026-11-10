"""Netlist del Medidor PPG (fuente única para el esquema y la PCB).

Valores = ../01_analogico/ppg.cir y ../SPEC.md.  Todo THT (soldadura a mano).
Cada componente: ref, (lib, símbolo), valor, footprint, nets {pin: red}, sección, unidades (op-amps).
"""

R_V = "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P2.54mm_Vertical"
C_DISC = "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm"
C_FILM = "Capacitor_THT:C_Rect_L7.2mm_W5.5mm_P5.00mm_FKS2_FKP2_MKS2_MKP2"
C_EL = "Capacitor_THT:CP_Radial_D6.3mm_P2.50mm"
D_V = "Diode_THT:D_DO-35_SOD27_P2.54mm_Vertical_CathodeUp"
D41_V = "Diode_THT:D_DO-41_SOD81_P2.54mm_Vertical_AnodeUp"
TRIM = "Potentiometer_THT:Potentiometer_Bourns_3296W_Vertical"
DIP14 = "Package_DIP:DIP-14_W7.62mm_Socket"
TO92 = "Package_TO_SOT_THT:TO-92_Inline_Wide"
BUZ = "Buzzer_Beeper:Buzzer_12x9.5RM7.6"
JST4 = "Connector_JST:JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical"
H4 = "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical"
H7 = "Connector_PinHeader_2.54mm:PinHeader_1x07_P2.54mm_Vertical"
H8 = "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical"
S8 = "Connector_PinSocket_2.54mm:PinSocket_1x08_P2.54mm_Vertical"
TP = "TestPoint:TestPoint_THTPad_D1.5mm_Drill0.7mm"
MH = "MountingHole:MountingHole_3.2mm_M3_Pad"

R = ("Device", "R")
C = ("Device", "C")
CP = ("Device", "C_Polarized")

COMPONENTES = []


def c(ref, sym, val, fp, nets, sec, nc=(), lcsc=""):
    bom = not (ref.startswith("TP") or ref.startswith("H"))
    COMPONENTES.append(dict(ref=ref, lib=sym[0], name=sym[1], val=val, fp=fp, nets=nets,
                            sec=sec, nc=list(nc), lcsc=lcsc, bom=bom))


# ---------------------------------------------------------------- 1 sensor óptico
S = "1 Sensor óptico (pinza)"
c("J1", ("Connector_Generic", "Conn_01x04"), "SENSOR", JST4,
  {"1": "LED_A", "2": "GND", "3": "+5V", "4": "SENS"}, S)       # 1 LED IR ánodo, 2 LED cátodo, 3 PD cátodo, 4 PD ánodo
c("R1", R, "220", R_V, {"1": "+5V", "2": "LED_A"}, S)
c("R2", R, "47k", R_V, {"1": "SENS", "2": "GND"}, S)
# ---------------------------------------------------------------- 2 acople AC + referencias
S = "2 Acople AC y referencias 1.32 V"
c("C1", C, "1uF film", C_FILM, {"1": "SENS", "2": "N1"}, S)
c("R3", R, "470k", R_V, {"1": "N1", "2": "VREF1"}, S)
c("R15", R, "3.3k", R_V, {"1": "+3V3", "2": "VREF1"}, S)
c("R16", R, "2.2k", R_V, {"1": "VREF1", "2": "GND"}, S)
c("C13", CP, "100uF", C_EL, {"1": "VREF1", "2": "GND"}, S)
c("C14", C, "100nF", C_DISC, {"1": "VREF1", "2": "GND"}, S)
c("R17", R, "3.3k", R_V, {"1": "+3V3", "2": "VREF2"}, S)
c("R18", R, "2.2k", R_V, {"1": "VREF2", "2": "GND"}, S)
c("C15", CP, "100uF", C_EL, {"1": "VREF2", "2": "GND"}, S)
c("C16", C, "100nF", C_DISC, {"1": "VREF2", "2": "GND"}, S)
# ---------------------------------------------------------------- 3-6 LM324 (4 unidades + alimentación)
S = "3-6 Buffer, preamp, Sallen-Key, final (LM324)"
c("U1", ("Amplifier_Operational", "LM324"), "LM324N", DIP14,
  {"1": "BUF", "2": "BUF", "3": "N1",          # U1A buffer
   "5": "BUF", "6": "INV1", "7": "PRE",        # U1B preamp
   "10": "SKB", "9": "SKO", "8": "SKO",        # U1C Sallen-Key
   "12": "N2", "13": "INV2", "14": "P6",       # U1D final -> Punto 6
   "4": "+5V", "11": "GND"}, S)
c("R4", R, "10k", R_V, {"1": "INV1", "2": "VREF1"}, S)
c("R5", R, "300k", R_V, {"1": "PRE", "2": "INV1"}, S)
c("C5", C, "47nF", C_DISC, {"1": "PRE", "2": "INV1"}, S)
c("R6", R, "47k", R_V, {"1": "PRE", "2": "SKA"}, S)
c("R7", R, "47k", R_V, {"1": "SKA", "2": "SKB"}, S)
c("C3", C, "1uF film", C_FILM, {"1": "SKA", "2": "SKO"}, S)
c("C2", C, "470nF film", C_FILM, {"1": "SKB", "2": "GND"}, S)
c("C8", C, "1uF film", C_FILM, {"1": "SKO", "2": "N2"}, S)
c("R11", R, "470k", R_V, {"1": "N2", "2": "VREF2"}, S)
c("R8", R, "10k", R_V, {"1": "INV2", "2": "VREF2"}, S)
c("R9", R, "10k", R_V, {"1": "P6", "2": "X9"}, S)
c("RV1", ("Device", "R_Potentiometer_Trim"), "200k", TRIM, {"1": "X9", "2": "INV2", "3": "INV2"}, S)
c("C9", C, "10nF", C_DISC, {"1": "P6", "2": "INV2"}, S)
c("C10", C, "100nF", C_DISC, {"1": "+5V", "2": "GND"}, S)
# ---------------------------------------------------------------- protección ADC
S = "7 Protección ADC (Punto 6 -> GPIO1)"
c("R10", R, "4.7k", R_V, {"1": "P6", "2": "ADC"}, S)
c("C7", C, "100nF", C_DISC, {"1": "ADC", "2": "GND"}, S)
c("D2", ("Device", "D_Schottky"), "BAT85", D_V, {"1": "+3V3", "2": "ADC"}, S)
c("D3", ("Device", "D_Schottky"), "BAT85", D_V, {"1": "ADC", "2": "GND"}, S)
# ---------------------------------------------------------------- MCU, OLED, buzzer
S = "8 ESP32-C3 SuperMini, TFT 1.3 y buzzer"
# SuperMini, USB hacia el borde trasero. Fila 1: 5V,GND,3V3,IO4,IO3,IO2,IO1,IO0. Fila 2: IO5..IO10,IO20,IO21
c("J2", ("Connector_Generic", "Conn_01x08"), "C3_5V-IO0", S8,
  {"1": "+5V", "2": "GND", "3": "+3V3", "4": "TFT_SCK", "5": "TFT_BLK", "7": "ADC", "8": "VBAT_S"}, S, nc=["6"])  # 4=IO4 5=IO3 7=IO1 8=IO0
c("J3", ("Connector_Generic", "Conn_01x08"), "C3_IO5-IO21", S8,
  {"1": "TFT_RES", "2": "TFT_SDA", "3": "TFT_DC", "6": "BUZ"}, S, nc=["4", "5", "7", "8"])  # 1=IO5 2=IO6 3=IO7 6=IO10
c("J4", ("Connector_Generic", "Conn_01x07"), "TFT 1.3 ST7789", H7,   # orden del módulo GMT130
  {"1": "GND", "2": "+3V3", "3": "TFT_SCK", "4": "TFT_SDA", "5": "TFT_RES", "6": "TFT_DC", "7": "TFT_BLK"}, S)
c("R12", R, "1k", R_V, {"1": "BUZ", "2": "QB"}, S)
c("Q1", ("Transistor_BJT", "2N3904"), "2N3904", TO92, {"1": "GND", "2": "QB", "3": "BZK"}, S)
c("BZ1", ("Device", "Buzzer"), "Buzzer 5V", BUZ, {"1": "+5V", "2": "BZK"}, S)
c("D4", ("Device", "D"), "1N4148", D_V, {"1": "+5V", "2": "BZK"}, S)
c("C12", C, "100nF", C_DISC, {"1": "+3V3", "2": "GND"}, S)
# ---------------------------------------------------------------- energía (módulos en el piso de la caja)
S = "9 Energía: LiPo -> TP4056 -> interruptor -> MT3608 5V"
c("J5", ("Connector_Generic", "Conn_01x08"), "ENERGIA", H8,
  {"1": "BAT", "2": "BAT", "3": "VSW", "4": "VSW", "5": "GND", "6": "GND", "7": "+5V_B", "8": "GND"}, S)
# 1 TP4056 OUT+ | 2 interruptor A | 3 interruptor B | 4 MT3608 IN+ | 5 TP4056 OUT- | 6 MT3608 IN- | 7 MT3608 OUT+ | 8 MT3608 OUT-
c("D1", ("Device", "D_Schottky"), "1N5819", D41_V, {"1": "+5V", "2": "+5V_B"}, S)
c("C11", CP, "100uF", C_EL, {"1": "+5V", "2": "GND"}, S)
c("R13", R, "100k", R_V, {"1": "VSW", "2": "VBAT_S"}, S)
c("R14", R, "100k", R_V, {"1": "VBAT_S", "2": "GND"}, S)
c("C17", C, "100nF", C_DISC, {"1": "VBAT_S", "2": "GND"}, S)
# ---------------------------------------------------------------- puntos de prueba (validación por etapas)
S = "10 Puntos de prueba (osciloscopio)"
for ref, net in [("TP1", "SENS"), ("TP2", "BUF"), ("TP3", "PRE"), ("TP4", "SKO"), ("TP5", "P6"),
                 ("TP6", "VREF1"), ("TP7", "GND")]:
    c(ref, ("Connector", "TestPoint"), net, TP, {"1": net}, S)
for i in range(1, 5):
    c(f"H{i}", ("Mechanical", "MountingHole_Pad"), "M3", MH, {"1": "GND"}, S)

POTENCIA = {"GND", "+5V", "+3V3"}


def red_pcb(n):
    """Nombre de red como lo genera KiCad desde el esquema: etiquetas locales -> "/NOMBRE"."""
    return n if n in POTENCIA else "/" + n
