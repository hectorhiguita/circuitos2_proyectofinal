"""Netlist del Medidor de pulso con MAX30102 (fuente única para el esquema y la PCB).

Diseño DIGITAL: el MAX30102 trae LEDs + fotodiodo + AFE + ADC adentro y entrega el
dato por I2C. NO lleva op-amp ni filtros externos (ver ../01_analogico/README.md).

Bus I2C del sensor: SDA=GPIO0, SCL=GPIO1, INT=GPIO2 (movido para no chocar con la TFT).
TFT ST7789 1.3" por SPI: SCK=GPIO4, MOSI/SDA=GPIO6, DC=GPIO7, RES=GPIO5, BLK=GPIO3.

Cada componente: ref, (lib, símbolo), valor, footprint, nets {pin: red}, sección.
Todo THT (soldadura a mano en baquela perforada o PCB doble faz).
"""

R_V = "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P2.54mm_Vertical"
C_DISC = "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm"
C_EL = "Capacitor_THT:CP_Radial_D6.3mm_P2.50mm"
D_V = "Diode_THT:D_DO-35_SOD27_P2.54mm_Vertical_CathodeUp"
D41_V = "Diode_THT:D_DO-41_SOD81_P2.54mm_Vertical_AnodeUp"
TO92 = "Package_TO_SOT_THT:TO-92_Inline_Wide"
BUZ = "Buzzer_Beeper:Buzzer_12x9.5RM7.6"
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


# ---------------------------------------------------------------- 1 Sensor MAX30102 (módulo GY, 7 pines)
S = "1 Sensor MAX30102 (modulo I2C)"
# Orden del módulo GY-MAX30102: VIN, SCL, SDA, INT, IRD, RD, GND. IRD y RD van al aire (NC).
c("J1", ("Connector_Generic", "Conn_01x07"), "MAX30102", H7,
  {"1": "+3V3", "2": "SCL", "3": "SDA", "4": "INT", "7": "GND"}, S, nc=["5", "6"])
c("R1", R, "4.7k", R_V, {"1": "+3V3", "2": "SDA"}, S)   # pull-up I2C (si el módulo no lo trae)
c("R2", R, "4.7k", R_V, {"1": "+3V3", "2": "SCL"}, S)   # pull-up I2C
c("R3", R, "4.7k", R_V, {"1": "+3V3", "2": "INT"}, S)   # pull-up INT (open-drain)
c("C1", C, "100nF", C_DISC, {"1": "+3V3", "2": "GND"}, S)  # desacople del sensor

# ---------------------------------------------------------------- 2 ESP32-C3 SuperMini
S = "2 ESP32-C3 SuperMini"
# SuperMini, USB hacia el borde trasero. Fila 1: 5V,GND,3V3,IO4,IO3,IO2,IO1,IO0. Fila 2: IO5..IO10,IO20,IO21
c("J2", ("Connector_Generic", "Conn_01x08"), "C3_5V-IO0", S8,
  {"1": "+5V", "2": "GND", "3": "+3V3", "4": "TFT_SCK", "5": "TFT_BLK", "6": "INT", "7": "SCL", "8": "SDA"}, S)
# 4=IO4(SCK) 5=IO3(BLK) 6=IO2(INT) 7=IO1(SCL) 8=IO0(SDA)
c("J3", ("Connector_Generic", "Conn_01x08"), "C3_IO5-IO21", S8,
  {"1": "TFT_RES", "2": "TFT_SDA", "3": "TFT_DC", "6": "BUZ", "7": "VBAT_S"}, S, nc=["4", "5", "8"])
# 1=IO5(RES) 2=IO6(MOSI) 3=IO7(DC) 6=IO10(BUZ) 7=IO20(ADC batería)
c("C2", C, "100nF", C_DISC, {"1": "+3V3", "2": "GND"}, S)   # desacople MCU

# ---------------------------------------------------------------- 3 Pantalla TFT 1.3" ST7789 (SPI)
S = "3 Pantalla TFT 1.3 ST7789 (SPI)"
c("J4", ("Connector_Generic", "Conn_01x07"), "TFT 1.3 ST7789", H7,   # orden del módulo GMT130
  {"1": "GND", "2": "+3V3", "3": "TFT_SCK", "4": "TFT_SDA", "5": "TFT_RES", "6": "TFT_DC", "7": "TFT_BLK"}, S)

# ---------------------------------------------------------------- 4 Buzzer
S = "4 Buzzer piezoelectrico"
c("R4", R, "1k", R_V, {"1": "BUZ", "2": "QB"}, S)
c("Q1", ("Transistor_BJT", "2N3904"), "2N3904", TO92, {"1": "GND", "2": "QB", "3": "BZK"}, S)
c("BZ1", ("Device", "Buzzer"), "Buzzer 5V", BUZ, {"1": "+5V", "2": "BZK"}, S)
c("D1", ("Device", "D"), "1N4148", D_V, {"1": "+5V", "2": "BZK"}, S)   # flyback del buzzer

# ---------------------------------------------------------------- 5 Energía: LiPo -> TP4056 -> interruptor -> MT3608 5V
S = "5 Energia: LiPo -> TP4056 -> interruptor -> MT3608 5V"
c("J5", ("Connector_Generic", "Conn_01x08"), "ENERGIA", H8,
  {"1": "BAT", "2": "BAT", "3": "VSW", "4": "VSW", "5": "GND", "6": "GND", "7": "+5V_B", "8": "GND"}, S)
# 1 TP4056 OUT+ | 2 interruptor A | 3 interruptor B | 4 MT3608 IN+ | 5 TP4056 OUT- | 6 MT3608 IN- | 7 MT3608 OUT+ | 8 MT3608 OUT-
c("D2", ("Device", "D_Schottky"), "1N5819", D41_V, {"1": "+5V", "2": "+5V_B"}, S)
c("C3", CP, "100uF", C_EL, {"1": "+5V", "2": "GND"}, S)
c("R5", R, "100k", R_V, {"1": "VSW", "2": "VBAT_S"}, S)   # divisor medida de batería /2
c("R6", R, "100k", R_V, {"1": "VBAT_S", "2": "GND"}, S)
c("C4", C, "100nF", C_DISC, {"1": "VBAT_S", "2": "GND"}, S)

# ---------------------------------------------------------------- 6 Puntos de prueba y agujeros
S = "6 Puntos de prueba y montaje"
for ref, net in [("TP1", "+3V3"), ("TP2", "SDA"), ("TP3", "SCL"), ("TP4", "GND")]:
    c(ref, ("Connector", "TestPoint"), net, TP, {"1": net}, S)
for i in range(1, 5):
    c(f"H{i}", ("Mechanical", "MountingHole_Pad"), "M3", MH, {"1": "GND"}, S)

POTENCIA = {"GND", "+5V", "+3V3"}


def red_pcb(n):
    """Nombre de red como lo genera KiCad desde el esquema: etiquetas locales -> "/NOMBRE"."""
    return n if n in POTENCIA else "/" + n
