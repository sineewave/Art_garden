import math, random, json
SPECIES=[('十字菀','CROSSVANE',0,8),('铃钟兰','BELLNET',1,3),('穗序草','SPIKELET',2,6),('伞形藻','UMBRELLE',3,5),('杯盏郁','TULIPA',4,3),
('蝶尾菊','PAPILIO',5,2),('流苏柳','FRINGEA',6,7),('墨点兰','INKSPOT',7,9),('叠塔花','STACKPILE',8,4),('辐星菊','RADIANT',9,10),
('重瓣芍','LAYERCUP',10,7),('管风铃','TUBEBELL',11,5),('荚果草','PODDER',12,5),('方格花','CHECKER',13,5)]
PALS=['#D96C4A','#5D8FB8','#7FA35B','#4FA096','#8F7BB5','#D97E9C','#D9A23F','#6E6E64','#4E5DA8','#C9C133','#3E7D5A','#E08A3C','#A44E7E','#3FA3C4']
def bucket(p): return p%8
class SVG:
    def __init__(s,W=1920,H=1080,bg='#0C0E10'):
        s.o=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><rect width="{W}" height="{H}" fill="{bg}"/>']; s.W,s.H=W,H
    def a(s,x): s.o.append(x)
    def line(s,x1,y1,x2,y2,c,w=1,dash=None,op=1):
        d=f' stroke-dasharray="{dash}"' if dash else ''
        s.a(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{c}" stroke-width="{w}" opacity="{op}"{d}/>')
    def text(s,x,y,t,size=12,c='#fff',anchor='start',fam='JetBrains Mono',weight=400,ls=0,op=1,rot=None):
        r=f' transform="rotate({rot} {x:.1f} {y:.1f})"' if rot is not None else ''
        t=str(t).replace('&amp;','&').replace('&','&amp;')
        s.a(f'<text x="{x:.1f}" y="{y:.1f}" font-family="{fam}" font-size="{size}" fill="{c}" text-anchor="{anchor}" font-weight="{weight}" letter-spacing="{ls}" opacity="{op}"{r}>{t}</text>')
    def circ(s,cx,cy,r,c,w=1,fill='none',dash=None,op=1):
        d=f' stroke-dasharray="{dash}"' if dash else ''
        s.a(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" stroke="{c}" stroke-width="{w}" fill="{fill}" opacity="{op}"{d}/>')
    def ell(s,cx,cy,rx,ry,rot,c,w=1,fill='none',op=1,dash=None):
        d=f' stroke-dasharray="{dash}"' if dash else ''
        s.a(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" transform="rotate({rot:.1f} {cx:.1f} {cy:.1f})" stroke="{c}" stroke-width="{w}" fill="{fill}" opacity="{op}"{d}/>')
    def rect(s,x,y,w,h,c='none',fill='none',sw=1,op=1,rx=0,dash=None):
        d=f' stroke-dasharray="{dash}"' if dash else ''
        s.a(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" stroke="{c}" stroke-width="{sw}" fill="{fill}" opacity="{op}"{d}/>')
    def path(s,d,c,w=1,fill='none',op=1,dash=None,marker=None):
        dd=f' stroke-dasharray="{dash}"' if dash else ''
        m=f' marker-end="url(#{marker})"' if marker else ''
        s.a(f'<path d="{d}" stroke="{c}" stroke-width="{w}" fill="{fill}" opacity="{op}"{dd}{m}/>')
    def arrowdef(s,id,c):
        s.a(f'<defs><marker id="{id}" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="{c}"/></marker></defs>')
    def save(s,f): s.o.append('</svg>'); open(f,'w').write('\n'.join(s.o))
def head_glyph(g,cx,cy,r,petals,c,w=1,op=1,fill='none'):
    for k in range(petals):
        an=2*math.pi*k/petals-math.pi/2
        g.ell(cx+math.cos(an)*r*.55,cy+math.sin(an)*r*.55,r*.46,r*.17,math.degrees(an),c,w,fill=fill,op=op)
    g.circ(cx,cy,r*.24,c,w,op=op)
