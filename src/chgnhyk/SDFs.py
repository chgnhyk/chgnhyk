import math

def clamp(v:float, a:float, b:float):
    return min(max(v,a),b)

def smoothstep(edge0:float, edge1:float, v:float):
    t = clamp((v - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3. - 2. * t)

def step(edge:float, v:float):
    if v < edge:
        return 0.
    else:
        return 1.

def mix(a:float, b:float, v:float):
    # v = clamp(v,0.0,1.0)
    return a*(1.0-v)+b*v

def dot2(a:tuple[float, float], b:tuple[float, float]):
    return a[0]*b[0]+a[1]*b[1]

def sign(v:float):
    if v >= .0:
        return 1.
    else:
        return -1.

def cross3(a: tuple[float, float, float], b: tuple[float, float, float]):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0]
    ) 

def sdCone(p:tuple[float, float, float], c:tuple[float, float], h:float):

    qx, qy = (h*c[0]/c[1],-1.0)
        
    wx, wy = (math.sqrt(p[0]*p[0]+p[2]*p[2]), p[1])
    wh = clamp( dot2((wx, wy),(qx, qy))/dot2((qx, qy),(qx, qy)), 0.0, 1.0 )
    ax, ay = (wx - qx * wh, wy - qy * wh)
    bh = clamp( wx/qx, 0.0, 1.0 )
    bx, by = wx - qx * bh, wx - qy
    k = sign( qy )
    d = min(dot2((ax,ay), (ax,ay)), dot2((bx,by), (bx,by)))
    s = max( k*(wx*qy-wy*qx), k*(wy-qy) )
    return math.sqrt(d)*sign(s)


def sdCapsule(p:tuple[float, float, float], a:tuple[float, float, float], b:tuple[float, float, float], r:float):
    pax, pay, paz = p[0]-a[0], p[1]-a[1], p[2]-a[2] 
    bax, bay, baz = b[0]-a[0], b[1]-a[1], b[2]-a[2]
    h = clamp((pax*bax+pay*bay+paz*baz) / (bax*bax+bay*bay+baz*baz), 0., 1.)
    px, py, pz = pax-bax*h, pay-bay*h, paz-baz*h
    return math.sqrt(px*px+py*py+pz*pz) - r


def sdCappedCylinder(p:tuple[float, float, float],  h:float, r:float):
    dx = abs(math.sqrt(p[0]*p[0]+p[2]*p[2])) - r
    dy = abs(p[1]) - h
    clmp_dx = max(0, dx)
    clmp_dy = max(0, dy)
    return min(max(dx, dy),0.0) + math.sqrt(clmp_dx*clmp_dx+clmp_dy*clmp_dy)

def sdCappedCone(p:tuple[float, float, float], h:float, r1:float, r2:float):
    qx, qy = (math.sqrt(p[0]*p[0]+p[2]*p[2]), p[1])
    k1x, k1y = (r2, h)
    k2x, k2y = (r2-r1, 2.0*h)
    car = r2
    if qy < 0.0:
        car = r1
    cax, cay = (qx-min(qx,car), abs(qy)-h)
    k1qx, k1qy = (k1x-qx, k1y-qy)
    cbr = clamp((k1qx*k2x+k1qy*k2y)/(k2x*k2x+k2y*k2y),0.0,1.0)
    cbx, cby = (qx-k1x+k2x*cbr, qy-k1y+k2y*cbr)
    s = 1.0
    if cbx < 0.0 and cay < 0.0:
        s = -1.0
    return s*math.sqrt(min(cax*cax+cay*cay, cbx*cbx+cby*cby))

def sdEllipsoid(p:tuple[float, float, float], r:tuple[float, float, float]):
    k0x, k0y, k0z = p[0]/r[0], p[1]/r[1], p[2]/r[2]
    k1x, k1y, k1z = p[0]/r[0]*r[0], p[1]/r[1]*r[1], p[2]/r[2]*r[2]
    k0 = math.sqrt(k0x*k0x+k0y*k0y+k0z*k0z)
    k1 = math.sqrt(k1x*k1x+k1y*k1y+k1z*k1z)
    return k0*(k0-1.0)/k1

def sdBox(p:tuple[float, float, float], sz:tuple[float, float, float]):
    px, py, pz = p[0], p[1], p[2]
    qx, qy, qz = (abs(px) - sz[0], abs(py) - sz[1], abs(pz) - sz[2])
    ax, ay, az = (max(qx, 0.0), max(qy, 0.0), max(qz, 0.0))
    b = min(max(qx, max(qy, qz)), 0.0)
    dst = math.sqrt(ax*ax+ay*ay+az*az) + b
    return dst

def sdSphere(p:tuple[float, float, float], r:float):
    return math.dist(p,(0,0,0))-r

def sdCircle(p:tuple[float, float], r:float):
    return math.dist(p,(0,0))-r

#     vec2 dir = normalize(ba);
#     float l = dot(pa, dir);
#     float bal = length(ba);
#     vec2 h = l * dir + a;
#     float dst = length(h-p)-w;
#     // dst = max(dst,-l-w);
#     // dst = max(dst,l-bal-w);
#     dst = max(dst,-l);
#     dst = max(dst,l-bal);
    
#     return dst;
# }
def sdLine(p:tuple[float, float], a:tuple[float, float], b:tuple[float, float], w:float):
    pa = p[0]-a[0], p[1]-a[1]
    ba = b[0]-a[0], b[1]-a[1]
    bal = math.sqrt(ba[0]*ba[0]+ba[1]*ba[1])
    if bal <= 0.0001:
        dir = 0, 0
    else:
        dir = ba[0]/bal, ba[1]/bal
    l = dot2(pa, dir)
    h = a[0]+l*dir[0], a[1]+l*dir[1]
    hp = p[0]-h[0], p[1]-h[1]
    dst = math.sqrt(hp[0]*hp[0]+hp[1]*hp[1])-w
    dst = max(dst, -l)
    dst = max(dst,l-bal)
    return dst


def opSmoothSubtraction(d1:float, d2:float, k:float):
    h = clamp(0.5-0.5*(d2+d1)/k,0.0,1.0)
    return mix(d2,-d1,h)+k*h*(1.0-h)

def smin(a:float, b:float, k:float):
    h = max(k-abs(a-b),0.0)/k
    return min(a,b)-h*h*k*(1.0/4.0)

def rotate(p:tuple, a:float):
    return p[0]*math.cos(a)-p[1]*math.sin(a), p[0]*math.sin(a)+p[1]*math.cos(a)