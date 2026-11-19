import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
fig,ax=plt.subplots(figsize=(13,8)); ax.set_xlim(0,130); ax.set_ylim(0,80); ax.axis("off")
def box(x,y,w,h,t,c):
    ax.add_patch(Rectangle((x,y),w,h,fc=c,ec="k",lw=1.5)); ax.text(x+w/2,y+h+1.2,t,ha="center",weight="bold",fontsize=10)
def pins(x,y,names,side,dy=4.2):
    for i,n in enumerate(names):
        ax.text(x+(1.2 if side=="L" else -1.2),y-i*dy,n,ha="left" if side=="L" else "right",va="center",fontsize=8)
box(5,38,24,34,"MAX30102 (J1)","#ffe0e0"); pins(5,69,["VIN","SCL","SDA","INT","IRD (NC)","RD (NC)","GND"],"L")
box(50,22,30,50,"ESP32-C3 SuperMini","#e0ecff")
L=["3V3","IO1 SCL","IO0 SDA","IO2 INT","GND"]; 
pins(50,66,L,"L")
R=["IO4 SCK","IO6 MOSI","IO5 RES","IO7 DC","IO3 BLK","IO10 BUZ","IO20 ADC","5V"]; pins(80,68,R,"R",5.5)
box(103,40,24,32,"TFT ST7789 (J4)","#e6ffe0"); pins(103,68,["SCK","SDA","RES","DC","BLK","3V3","GND"],"L",4)
# I2C
for i,(a,b,c) in enumerate([(69,66,"#f57c00"),(65,61.8,"#00acc1"),(60.8,57.6,"#f57c00"),(56.6,53.4,"#7cb342")]):
    pass
ax.plot([29,50],[69,66],color="#f57c00",lw=2); ax.text(38,69.5,"3V3",fontsize=8,color="#f57c00")
ax.plot([29,50],[65,61.8],color="#00acc1",lw=2); ax.text(38,64.5,"SCL",fontsize=8,color="#00acc1")
ax.plot([29,50],[61,57.6],color="#ff8f00",lw=2); ax.text(38,60,"SDA",fontsize=8)
ax.plot([29,50],[57,53.4],color="#7cb342",lw=2); ax.text(38,56,"INT",fontsize=8,color="#7cb342")
ax.plot([29,50],[45,49.2],color="k",lw=2); ax.text(38,45,"GND",fontsize=8)
for k,(y0,y1,c) in enumerate([(68,68,"#8e24aa"),(62.5,64,"#1e88e5"),(57,60,"#43a047"),(51.5,56,"#3949ab"),(46,52,"#546e7a")]):
    ax.plot([80,103],[y0,y1],color=c,lw=1.8)
ax.text(92,37,"TFT 3V3 y GND: del riel 3V3 / GND",fontsize=8,ha="center")
ax.text(40,76,"Pull-ups 4.7k a 3V3 en SDA, SCL, INT (R1-R3); C1 100nF",fontsize=8)
box(5,4,30,14,"Buzzer: R4 1k -> Q1 2N3904 -> BZ1 + D1","#fff5d6")
ax.plot([80,84,84,20,20],[40.5,40.5,21,21,18],color="#3949ab",lw=1.8); ax.text(50,22,"BUZ (IO10)",fontsize=8,color="#3949ab")
box(70,4,55,14,"Energia: LiPo -> TP4056 -> interruptor -> MT3608 5V -> 1N5819","#f3e5f5")
ax.text(72,6.5,"Divisor 100k/100k de VSW -> IO20 (medir bateria)",fontsize=8)
ax.set_title("Medidor PPG con MAX30102 - diagrama de conexiones",weight="bold")
fig.savefig("img/diagrama_max30102.png",dpi=160,bbox_inches="tight")
