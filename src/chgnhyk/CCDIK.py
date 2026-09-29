import math

def clamp(x, min_val, max_val):
    return max(min(x, max_val), min_val)

def rotate(x,y,a):
    return (math.cos(a)*x-math.sin(a)*y, math.sin(a)*x+math.cos(a)*y)

def fract(x):
    return x-math.floor(x)

def smoothstep(mi, mx, v):
    x = max(0, min(1, (v-mi)/(mx-mi)))
    return x*x*(3 - 2*x)

def normalize(x, y):
    vl = math.sqrt(x*x+y*y)
    if vl < 1e-6:
        return (0.0, 0.0)
    else:
        return (x/vl, y/vl)

def get_dist(x1,y1,x2,y2):
    dx = x2-x1
    dy = y2-y1
    return math.sqrt(dx*dx+dy*dy)

def get_angle(v1:tuple,v2:tuple):
    dot = v1[0]*v2[0]+v1[1]*v2[1]
    crss = v1[0]*v2[1]-v1[1]*v2[0]
    
    dot = clamp(dot, -1.0, 1.0)

    if abs(dot - 1.0) < 1e-6 and abs(crss) < 1e-6:
        return 0.0
    else:
        angle = math.atan2(crss,dot)
        return angle

class Arm2D:
    def __init__(self, num, l, ease = 1.0, angle = 0.0):
        self.L = l
        self.angles = []
        self.positions = []
        self.sx = 0
        self.sy = 0

        self.ease = ease

        self.num = num
        for i in range(self.num):
            if i == 0:
                self.angles.append(math.pi * 0.5 + angle)
            else:
                self.angles.append(0.0)
            self.positions.append((0.0,0.0))


    def get_arm_pos(self):
        data = []
        data = self.positions.copy()
        self.update_arms()
        data.append((self.ex,self.ey))
        # print(len(data))
        return data
    
    def update_arms(self):
        _sx = self.sx
        _sy = self.sy
        _a = 0
        for i in range(self.num):
            _a += self.angles[i]            
            self.positions[i] = (_sx,_sy)
            _sx = _sx + math.cos(_a) * self.L
            _sy = _sy + math.sin(_a) * self.L

        self.ex = _sx
        self.ey = _sy
    
    def set_target(self, tx, ty):
        self.update_arms()

        for i in range(self.num-1,-1,-1):
            jx = self.positions[i][0]
            jy = self.positions[i][1]

            jd = normalize(self.ex-jx, self.ey-jy)
            d = normalize(tx-jx, ty-jy)

            angle = get_angle(jd, d)
            self.angles[i] += angle * self.ease

            self.update_arms()