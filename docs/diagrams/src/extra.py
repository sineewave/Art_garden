import sys,math,random,colorsys
sys.path.insert(0,sys.argv[1]); from common import *
OUT=sys.argv[2]
BG='#05070B'; W_='#EEF3FA'; MU='#8A95A5'; DIMC='#2A3240'
CYN='#5EC8FF'; BLU='#4C7DFF'; TEAL='#3FE0C0'; VIO='#9B7BFF'; GRY='#8A93A0'; GOLD='#FFD27A'; ROSE='#D98CA8'; MINT='#5EE0B5'
def new():
    g=SVG(bg=BG)
    g.a('<defs><filter id="gl" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
        '<filter id="gl2" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="9"/></filter></defs>')
    return g
def T(g,x,y,t,size=14,c=W_,**k): g.text(x,y,t,size,c,fam=k.pop('fam','Inter'),**k)
def header(g,title,sub,n):
    T(g,80,92,title,46,W_,fam='Inter Display',weight=700,ls=-1); T(g,82,124,sub,17,MU)
    T(g,1840,92,f'ATTENTION GARDEN · {n}',12,MU,anchor='end',ls=3)
def hsl(h,s,l):
    r,g_,b=colorsys.hls_to_rgb(h/360,l,s); return '#%02x%02x%02x'%(int(r*255),int(g_*255),int(b*255))
def panel(g,x,y,w,h,c):
    g.rect(x,y,w,h,c,sw=1.4,rx=20,fill='#080B11'); g.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="20" fill="none" stroke="{c}" stroke-width="6" opacity=".14" filter="url(#gl2)"/>')

# ============ F6 · spreading vs breeding ============
g=new(); random.seed(5)
header(g,'Spreading and breeding','How I came to see generated images: not only passed along, but reproducing','05')
# left panel: recommendation
L=(80,190,700,700); panel(g,*L,GRY)
T(g,L[0]+30,L[1]+44,'RECOMMENDATION FEED',13,GRY,weight=700,ls=2)
T(g,L[0]+30,L[1]+76,'One item, copied and pushed',24,W_,fam='Inter Display',weight=700)
ox,oy=L[0]+140,L[1]+400; c0=PALS[1]
g.rect(ox-26,oy-26,52,52,fill=c0); g.a(f'<rect x="{ox-32}" y="{oy-32}" width="64" height="64" fill="none" stroke="{W_}" stroke-width="1.6" filter="url(#gl)"/>')
lvl=[(ox,oy)]
for gen,(n,dx) in enumerate(((3,150),(6,140),(10,130))):
    nxt=[]
    for k in range(n):
        y=oy+(k-(n-1)/2)*(560/(n+1)); x=ox+dx*(gen+1)
        p=lvl[min(len(lvl)-1,int(k*len(lvl)/n))]
        g.path(f'M{p[0]+30},{p[1]} C{(p[0]+x)/2},{p[1]} {(p[0]+x)/2},{y} {x-20},{y}',GRY,1.2,op=.6)
        s=40-gen*7; g.rect(x-s/2,y-s/2,s,s,fill=c0,op=.95-gen*.15); nxt.append((x,y))
    lvl=nxt
T(g,L[0]+30,L[1]+L[3]-60,'the same image, more places',16,W_,weight=600)
T(g,L[0]+30,L[1]+L[3]-36,'selects · copies · spreads',14,MU)
# right panel: generative
R=(840,190,1000,700); panel(g,*R,TEAL)
T(g,R[0]+30,R[1]+44,'GENERATIVE PLATFORM',13,TEAL,weight=700,ls=2)
T(g,R[0]+30,R[1]+76,'A prompt is a seed',24,W_,fam='Inter Display',weight=700)
sx,sy=R[0]+90,R[1]+380
g.rect(sx-46,sy-22,92,44,TEAL,sw=1.8,rx=22,fill=BG); T(g,sx,sy+6,'prompt',15,TEAL,anchor='middle',weight=700,fam='JetBrains Mono')
g.a(f'<rect x="{sx-46}" y="{sy-22}" width="92" height="44" rx="22" fill="none" stroke="{TEAL}" stroke-width="6" opacity=".25" filter="url(#gl2)"/>')
gens=[4,7,11,15]; prev=[(sx+46,sy,200)]
target=330  # hue every family converges to
for gi,n in enumerate(gens):
    x=R[0]+260+gi*190; cur=[]
    for k in range(n):
        y=sy+(k-(n-1)/2)*(430/(n+1))
        p=prev[min(len(prev)-1,int(k*len(prev)/n))]
        hue0=(k*360/n+gi*20)%360
        mix=[0.0,.45,.75,.92][gi]
        dh=((target-hue0+540)%360)-180; hue=(hue0+dh*mix)%360
        col=hsl(hue,.62-.1*mix,.6)
        g.path(f'M{p[0]+8},{p[1]} C{(p[0]+x)/2},{p[1]} {(p[0]+x)/2},{y} {x-14},{y}',col,1.1,op=.55)
        s=[30,26,22,18][gi]; g.rect(x-s/2,y-s/2,s,s,fill=col,op=.95)
        cur.append((x+s/2,y,hue))
    prev=cur
    T(g,x,R[1]+130,f'round {gi+1}',12,MU,anchor='middle',fam='JetBrains Mono')
# family halo
g.ell(R[0]+830,sy,62,232,0,ROSE,1.6,dash='4 6')
T(g,R[0]+905,sy+6,'a family',15,ROSE,anchor='start',weight=700)
g.arrowdef('ar',TEAL)
g.path(f'M{R[0]+260},{R[1]+150} L{R[0]+830},{R[1]+150}',TEAL,1.4,marker='ar')
T(g,R[0]+30,R[1]+R[3]-60,'images that make more images, looking more and more alike',16,W_,weight=600)
T(g,R[0]+30,R[1]+R[3]-36,'reused · tweaked · run again · each round shapes the next',14,MU)
T(g,80,960,'Conceptual diagram.',12,MU,fam='JetBrains Mono')
g.save(OUT+'/F6_breeding.svg')

# ============ F7 · cost ============
g=new()
header(g,'What breeding costs','Every generated image draws on electricity and water','06')
# left: per inference
P=(80,190,860,700); panel(g,*P,GOLD)
T(g,P[0]+30,P[1]+44,'ONE GENERATION',13,GOLD,weight=700,ls=2)
T(g,P[0]+30,P[1]+76,'Energy per inference',24,W_,fam='Inter Display',weight=700)
bars=[('Text generation, mean',0.047,'0.047 Wh',GRY),('Image generation, mean',2.9,'2.9 Wh',GOLD),('Most energy-hungry image model',11.49,'11.49 Wh',ROSE)]
bx0,bw=P[0]+40,700
for k,(n,v,lab,c) in enumerate(bars):
    y=P[1]+170+k*130
    T(g,bx0,y,n,16,W_,weight=600)
    w=max(6,bw*v/11.49)
    g.a(f'<rect x="{bx0}" y="{y+16}" width="{w:.1f}" height="34" rx="6" fill="{c}" opacity=".9" filter="url(#gl)"/>')
    T(g,bx0+w+14,y+40,lab,22,c,fam='Inter Display',weight=700)
T(g,P[0]+40,P[1]+600,'≈ 60×',64,GOLD,fam='Inter Display',weight=700)
T(g,P[0]+260,P[1]+566,'an average image versus',16,W_); T(g,P[0]+260,P[1]+590,'an average text generation',16,W_)
T(g,P[0]+40,P[1]+672,'Luccioni, Jernite, Strubell · FAccT 2024',12,MU,fam='JetBrains Mono')
# right: data centres
Q=(1000,190,840,700); panel(g,*Q,VIO)
T(g,Q[0]+30,Q[1]+44,'ALL DATA CENTRES',13,VIO,weight=700,ls=2)
T(g,Q[0]+30,Q[1]+76,'Electricity per year',24,W_,fam='Inter Display',weight=700)
base=Q[1]+600; sc=400/945
for k,(yr,v,proj) in enumerate(((2024,415,False),(2030,945,True))):
    x=Q[0]+160+k*300; h=v*sc
    if proj:
        g.rect(x,base-h,150,h,VIO,sw=2,rx=8,dash='8 6',fill='none')
        g.a(f'<rect x="{x}" y="{base-h:.1f}" width="150" height="{h:.1f}" rx="8" fill="{VIO}" opacity=".12"/>')
    else:
        g.a(f'<rect x="{x}" y="{base-h:.1f}" width="150" height="{h:.1f}" rx="8" fill="{VIO}" opacity=".85" filter="url(#gl)"/>')
    T(g,x+75,base-h-18,f'{v} TWh',26,W_ if not proj else VIO,anchor='middle',fam='Inter Display',weight=700)
    T(g,x+75,base+30,str(yr)+(' · projected' if proj else ''),15,MU,anchor='middle')
g.line(Q[0]+120,base,Q[0]+660,base,DIMC,1.4)
T(g,Q[0]+40,Q[1]+672,'International Energy Agency · Energy and AI, 2025',12,MU,fam='JetBrains Mono')
T(g,Q[0]+640,Q[1]+380,'more than',16,MU); T(g,Q[0]+640,Q[1]+412,'doubled',30,VIO,fam='Inter Display',weight=700)
T(g,80,960,'Published estimates, not measurements of this installation. Data centres also use water for cooling (Li et al., 2025).',12,MU,fam='JetBrains Mono')
g.save(OUT+'/F7_cost.svg')
