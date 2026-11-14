import sys,math,random
sys.path.insert(0,sys.argv[1]); from common import *
OUT=sys.argv[2]
BG='#05070B'; W_='#EEF3FA'; MU='#8A95A5'; DIMC='#2A3240'
EARLY='#5EE0B5'; CYN='#5EC8FF'; BLU='#4C7DFF'; TEAL='#3FE0C0'; VIO='#9B7BFF'; GRY='#8A93A0'; GOLD='#FFD27A'; ROSE='#D98CA8'
g=SVG(bg=BG)
g.a('<defs><filter id="gl" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
    '<filter id="gl2" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="9"/></filter></defs>')
for c,i in ((GOLD,'g'),(CYN,'c'),(W_,'w'),(TEAL,'t'),(VIO,'v'),(GRY,'y')):
    g.a(f'<defs><marker id="m{i}" markerWidth="10" markerHeight="10" refX="7" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="{c}"/></marker></defs>')
def T(x,y,t,size=14,c=W_,**k): g.text(x,y,t,size,c,fam=k.pop('fam','Inter'),**k)
def arrow(d,c,m,w=2.2,dash=None,glow=True):
    dd=f' stroke-dasharray="{dash}"' if dash else ''
    g.a(f'<path d="{d}" fill="none" stroke="{c}" stroke-width="{w}"{dd} marker-end="url(#{m})"' + (' filter="url(#gl)"' if glow else '') + '/>')
def rosette(cx,cy,r,n,c,w=1.6,sq=1,op=1,dash=None):
    d=f' stroke-dasharray="{dash}"' if dash else ''
    g.a(f'<g transform="translate({cx:.1f},{cy:.1f}) scale(1,{sq})" filter="url(#gl)" opacity="{op}">')
    for k in range(n): g.a(f'<ellipse cx="{r*.55:.1f}" cy="0" rx="{r*.47:.1f}" ry="{r*.2:.1f}" transform="rotate({360*k/n:.1f})" fill="none" stroke="{c}" stroke-width="{w}"{d}/>')
    g.a(f'<circle r="{r*.18:.1f}" fill="{c}"/></g>')
def bubble(cx,cy,r,c=GOLD,w=2.4):
    pts=[]
    for i in range(0,361,4):
        t=math.radians(i); rr=r*(1+.06*math.sin(2*t+.3)+.045*math.sin(3*t+1.2)+.03*math.sin(5*t+2.1))
        pts.append(f'{cx+rr*math.cos(t):.1f},{cy+rr*math.sin(t):.1f}')
    g.a(f'<path d="M{" L".join(pts)} Z" fill="none" stroke="{c}" stroke-width="{w}" filter="url(#gl)"/>')
def screen(x,y,w,h,c,num,name):
    g.rect(x,y,w,h,c,sw=1.6,rx=18,fill='#080B11')
    g.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="none" stroke="{c}" stroke-width="6" opacity=".18" filter="url(#gl2)"/>')
    T(x+22,y+34,num,13,c,weight=700,ls=2); T(x+22,y+64,name,26,W_,fam='Inter Display',weight=700)
random.seed(12)
T(80,92,'How the installation works',46,W_,fam='Inter Display',weight=700,ls=-1)
T(82,124,'Input, three screens, output',17,MU)
# ---------------- screens
SY,SH=330,470
SW=486; GAP=71; S1=(260,SY,SW,SH); S2=(260+SW+GAP,SY,SW,SH); S3=(260+2*(SW+GAP),SY,SW,SH)
screen(*S1,GOLD,'SCREEN 1','Feed'); screen(*S2,TEAL,'SCREEN 2','Garden'); screen(*S3,VIO,'SCREEN 3','Roots')
# --- feed contents
x0,y0,w,h=S1
tiles=[]
for k in range(46):
    tx=x0+40+random.uniform(0,w-80); ty=y0+100+random.uniform(0,h-150)
    s=random.choice([14,16,18,22,26]); c=random.choice(PALS); op=random.uniform(.35,.9)
    tiles.append((tx,ty,s))
    g.rect(tx-s/2,ty-s/2,s,s,fill=c,op=op)
for k in range(10):
    a_,b_=random.sample(tiles,2); g.line(a_[0],a_[1],b_[0],b_[1],CYN,.8,op=.25)
fx,fy=x0+180,y0+260
for k,(dx,dy) in enumerate(((-22,-6),(10,-18),(18,14))): g.rect(fx+dx-12,fy+dy-12,24,24,fill=PALS[k+1],op=1)
bubble(fx,fy,58)
# one breeding tile with children
bx_,by_=x0+340,y0+190
g.rect(bx_-15,by_-15,30,30,fill=PALS[5]); 
for k,(dx,dy) in enumerate(((50,-30),(60,20),(30,46))):
    g.line(bx_,by_,bx_+dx,by_+dy,PALS[5],1.2,op=.7); g.rect(bx_+dx-9,by_+dy-9,18,18,fill=PALS[5],op=.75)
T(bx_-8,by_-30,'breeds',13,PALS[5],weight=700)
# migrating tile at right edge
mx,my=x0+w-60,y0+320
g.rect(mx-14,my-14,28,28,fill=PALS[3]); g.a(f'<rect x="{mx-20}" y="{my-20}" width="40" height="40" fill="none" stroke="{TEAL}" stroke-width="2" filter="url(#gl)"/>')
g.line(mx+22,my,x0+w-4,my,TEAL,2)
# fading tiles
for k in range(6): g.rect(x0+60+k*30,y0+h-40,12,12,fill=GRY,op=.5-k*.07)
# --- garden contents
x0,y0,w,h=S2; G=y0+h-70
g.line(x0+20,G,x0+w-20,G,'#3A4350',2)
kx_=w/520
plants=[(x0+70*kx_,120,8,CYN,1),(x0+150*kx_,150,10,BLU,1),(x0+235*kx_,90,6,PALS[6],1),(x0+300*kx_,175,12,TEAL,1),(x0+345*kx_,140,12,TEAL,1),(x0+390*kx_,160,12,TEAL,1),(x0+440*kx_,95,6,GRY,0)]
for px,ph,pet,c,alive in plants:
    dash=None if alive else '4 4'
    g.a('<g filter="url(#gl)">'); g.path(f'M{px},{G} Q{px+6},{G-ph*.5} {px+(3 if alive else 26)},{G-ph}',c,2,dash=dash); g.a('</g>')
    rosette(px+(3 if alive else 26),G-ph-14,18+ph*.08,pet,c,dash=dash,op=1 if alive else .7)
# trend clump
g.ell(x0+345*kx_,G-150,88,58,0,TEAL,1.4,dash='3 5')
T(x0+345*kx_,G-222,'trend',14,TEAL,anchor='middle',weight=700)
for k in range(6): g.circ(x0+290*kx_+k*20,G-4,2.5,TEAL,0,fill=TEAL)
T(x0+462*kx_,G-130,'dormant',13,GRY,anchor='middle',weight=700)
bubble(x0+150*kx_,G-164,46)
# --- roots contents
x0,y0,w,h=S3
layers=[('capture',CYN),('transport','#8FB8F0'),('ranking',VIO),('inference','#C7A2FF'),('power',GOLD)]
ly=[y0+120+k*62 for k in range(5)]
nodes=[]
for k,(n,c) in enumerate(layers):
    cnt=[6,5,4,3,2][k]; row=[]
    for j in range(cnt):
        nx=x0+50+(w-100)*(j+.5)/cnt; row.append(nx); g.circ(nx,ly[k],7 if k<4 else 10,c,1.6,fill='#080B11')
    T(x0+w-20,ly[k]-14,n,12,c,anchor='end',weight=700,ls=1); nodes.append(row)
for k in range(4):
    for a_ in nodes[k]:
        for b_ in nodes[k+1]:
            g.line(a_,ly[k]+7,b_,ly[k+1]-7,DIMC,1)
path=[nodes[0][1],nodes[1][1],nodes[2][2],nodes[3][1],nodes[4][0]]
d='M'+' L'.join(f'{px:.1f},{ly[k]:.1f}' for k,px in enumerate(path))
g.a(f'<path d="{d}" fill="none" stroke="{GOLD}" stroke-width="3" filter="url(#gl)"/>')
for k,px in enumerate(path): g.circ(px,ly[k],5,GOLD,0,fill=GOLD)
# ---------------- links between screens
arrow(f'M{S1[0]+S1[2]+6},{SY+320} C{S1[0]+S1[2]+50},{SY+320} {S2[0]-50},{SY+320} {S2[0]-8},{SY+320}',TEAL,'mt',w=2.6,glow=False)
T((S1[0]+S1[2]+S2[0])/2,SY+300,'migrates',15,TEAL,anchor='middle',weight=700)
T((S1[0]+S1[2]+S2[0])/2,SY+346,'at 42',13,MU,anchor='middle')
arrow(f'M{S2[0]+S2[2]+6},{SY+320} C{S2[0]+S2[2]+40},{SY+320} {S3[0]-40},{SY+320} {S3[0]-8},{SY+320}',VIO,'mv',w=2.6,glow=False)
T((S2[0]+S2[2]+S3[0])/2,SY+300,'roots',15,VIO,anchor='middle',weight=700)
# ---------------- INPUT (top)
T(80,196,'INPUT',13,MU,weight=700,ls=3)
# civitai data source
g.rect(80,SY+60,130,250,'#3A4350',sw=1.4,rx=14,fill='#080B11')
for i in range(6):
    for j in range(3): g.rect(96+j*36,SY+80+i*36,30,30,fill=random.choice(PALS),op=.85)
T(80,SY+346,'Civitai',16,W_,weight=700); T(80,SY+368,'real images,',13,MU); T(80,SY+386,'real likes',13,MU)
arrow(f'M214,{SY+180} L{S1[0]-8},{SY+180}',W_,'mw',w=1.8,glow=False)
# input buses
BY1,BY2=262,292
vx,vy=330,205
bubble(vx,vy,30); g.circ(vx,vy,5,GOLD,0,fill=GOLD)
T(vx+46,vy-4,'Visitor',22,GOLD,fam='Inter Display',weight=700); T(vx+46,vy+18,'looking = feeding · attention is limited',14,MU)
ax_,ay_=1130,205
g.circ(ax_,ay_,26,CYN,2,dash='5 4'); g.circ(ax_,ay_,5,CYN,0,fill=CYN)
T(ax_+42,ay_-4,'Algorithm',22,CYN,fam='Inter Display',weight=700); T(ax_+42,ay_+18,'looks when nobody has for 60 s · ×0.12',14,MU)
g.line(vx,vy+32,vx,BY1,GOLD,2.2); g.line(vx,BY1,S3[0]+S3[2]*.5,BY1,GOLD,2.2)
for tx_ in (S1[0]+S1[2]*.5,S2[0]+S2[2]*.5,S3[0]+S3[2]*.5):
    g.circ(tx_,BY1,4,GOLD,0,fill=GOLD); arrow(f'M{tx_},{BY1} L{tx_},{SY-6}',GOLD,'mg',w=2.2,glow=False)
g.line(ax_,ay_+28,ax_,BY2,CYN,1.8,dash='6 5'); g.line(S1[0]+S1[2]*.5+40,BY2,ax_,BY2,CYN,1.8,dash='6 5')
for tx_ in (S1[0]+S1[2]*.5+40,S2[0]+S2[2]*.5+40):
    g.circ(tx_,BY2,4,CYN,0,fill=CYN); arrow(f'M{tx_},{BY2} L{tx_},{SY-6}',CYN,'mc',w=1.8,dash='6 5',glow=False)
# ---------------- OUTPUT (bottom)
OY=SY+SH+56
T(80,OY+10,'OUTPUT',13,MU,weight=700,ls=3)
def out(x,y,c,title,sub):
    T(x,y+40,title,18,c,fam='Inter Display',weight=700); T(x,y+62,sub,13,MU)
# feed -> debris
for k in range(10): g.rect(S1[0]+20+random.uniform(0,60),OY+10+random.uniform(0,30),7,7,fill=GRY,op=random.uniform(.4,.9))
arrow(f'M{S1[0]+90},{SY+SH+6} L{S1[0]+90},{OY}',GRY,'my',w=1.8,glow=False)
out(S1[0]+110,OY,GRY,'Debris','what nobody looked at')
# garden -> seeds loop & file card
arrow(f'M{S2[0]+120},{SY+SH+6} L{S2[0]+120},{OY}',TEAL,'mt',w=1.8,glow=False)
for k in range(5): g.circ(S2[0]+40+k*14,OY+30,3,TEAL,0,fill=TEAL)
out(S2[0]+140,OY,TEAL,'Seeds','new plants nearby')
g.rect(S2[0]+300,OY+18,34,44,TEAL,sw=1.6,rx=4)
for k in range(3): g.line(S2[0]+307,OY+30+k*10,S2[0]+327,OY+30+k*10,TEAL,1.4)
out(S2[0]+348,OY,W_,'File','model · likes · energy')
# roots -> hum + numbers
arrow(f'M{S3[0]+80},{SY+SH+6} L{S3[0]+80},{OY}',GOLD,'mg',w=1.8,glow=False)
pts=[f'{S3[0]+20+i*3:.1f},{OY+30+10*math.sin(i*.6)*math.exp(-((i-20)/14)**2):.1f}' for i in range(41)]
g.a(f'<path d="M{" L".join(pts)}" fill="none" stroke="{GOLD}" stroke-width="2" filter="url(#gl)"/>')
out(S3[0]+160,OY,GOLD,'Hum + cost','Wh · CO₂ · water, cited')
g.save(OUT+'/F5_system.svg')
