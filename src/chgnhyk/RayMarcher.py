import math
from typing import Callable

def reflect(I, N):
    # I and N are 3-tuples or lists: (x, y, z)
    
    # dot product
    IN_dt = I[0]*N[0] + I[1]*N[1] + I[2]*N[2]
    
    # reflection vector
    V = [
        I[0] - 2 * IN_dt * N[0],
        I[1] - 2 * IN_dt * N[1],
        I[2] - 2 * IN_dt * N[2],
    ]
    
    # normalize (optional but usually desired)
    vl = math.sqrt(V[0]*V[0] + V[1]*V[1] + V[2]*V[2])
    if vl != 0:
        V[0] /= vl
        V[1] /= vl
        V[2] /= vl
    
    return V

class RayMarcher:
    def __init__(self, ray_scene: Callable[[float, float, float], float], max_steps:int = 100, min_dist:float = 1, max_dist:float = 1e4, should_reflect:bool = True, max_bounce:int = 4):
        self.map_fn = ray_scene

        self.sx = 0
        self.sy = 0
        self.sz = 0

        self.osx = 0
        self.osy = 0
        self.osz = 0

        self.dx = 0
        self.dy = 0
        self.dz = 0

        self.nx = 0
        self.ny = 0
        self.nz = 0

        self.MX_STP = max_steps
        self.MIN_DST = min_dist
        self.MX_DST = max_dist
        self.MX_BOUNCE = max_bounce

        self.DST = 0.0
        self.count = 0
        self.bounce_count = 0
        self.hit = False
        self.finished = False
        self.should_reflect = should_reflect

        self.bounce_points = []

        self.walk_cnt = 0
        self.walk_cnts = []
        self.points = []

    def setMapFunc(self, ray_scene: Callable[[float, float, float], float]):
        self.map_fn = ray_scene

    def setPos(self, pos:tuple):
        self.sx = pos[0]
        self.sy = pos[1]
        self.sz = pos[2]
        self.osx = pos[0]
        self.osy = pos[1]
        self.osz = pos[2]
        self.points.append((self.sx, self.sy, self.sz))

    def setDir(self, dir:tuple):
        
        dirx, diry, dirz = dir[0]-self.osx, dir[1]-self.osy, dir[2]-self.osz
        dirl = math.sqrt(dirx*dirx+diry*diry+dirz*dirz)
        dirx, diry, dirz = dirx/dirl, diry/dirl, dirz/dirl
        self.dx = dirx
        self.dy = diry
        self.dz = dirz

    def reset(self):
        self.points = []
        self.DST = 0.0
        self.count = 0
        self.bounce_count = 0
        self.finished = False

        self.walk_cnt = 0
        self.walk_cnts = []

    def calcNorm(self, _x, _y, _z):
        eps = self.MIN_DST
        return [
            self.map_fn(_x+eps, _y, _z, self)-self.map_fn(_x-eps, _y, _z, self),
            self.map_fn(_x, _y+eps, _z, self)-self.map_fn(_x, _y-eps, _z, self),
            self.map_fn(_x, _y, _z+eps, self)-self.map_fn(_x, _y, _z-eps, self),
        ]

    def _march(self):
        dst = self.map_fn(self.sx, self.sy, self.sz, self)
        
        if self.should_reflect is False:
            if self.DST > self.MX_DST or self.count >= self.MX_STP or dst < self.MIN_DST:
                self.finished = True
                return
        else:
            if dst < self.MIN_DST:
                self.hit = True

            if self.hit:
                self.walk_cnts.append(self.walk_cnt)
                self.walk_cnt = 0
                self.bounce_count += 1
                if self.bounce_count >= self.MX_BOUNCE:
                    self.finished = True
                    #return
                if self.count >= self.MX_STP:
                    self.finished = True
                    #return

                n = self.calcNorm(self.sx, self.sy, self.sz)
                nl = math.sqrt(n[0]*n[0]+n[1]*n[1]+n[2]*n[2])
                if nl > 0.0001:
                    n[0] /= nl
                    n[1] /= nl
                    n[2] /= nl

                self.nx = n[0]
                self.ny = n[1]
                self.nz = n[2]

                ref = reflect((self.dx,self.dy,self.dz), n)

                self.dx = ref[0]
                self.dy = ref[1]
                self.dz = ref[2]

                self.bounce_points.append((self.sx, self.sy, self.sz))

                self.sx += self.dx
                self.sy += self.dy
                self.sz += self.dz

                self.hit = False

                
                


        self.sx += self.dx * dst
        self.sy += self.dy * dst
        self.sz += self.dz * dst

        self.points.append((self.sx,self.sy,self.sz))

        self.DST += dst

        self.count += 1
        self.walk_cnt += 1

        # print(f"Step {self.count}: dist={dst}, pos=({self.sx},{self.sy})")

    def getPoints(self, only_xy = False, fill = False):
        data = []
        for i in range(self.MX_STP):
            if i < len(self.points):
                if only_xy:
                    data.append((self.points[i][0], self.points[i][1]))
                else:
                    data.append(self.points[i])
            else:
                if fill:
                    if only_xy:
                        data.append((0,0))
                    else:
                        data.append((0,0,0))

        if fill == False:
            return data
        else: 
            return (data, len(self.points))
    
    def getDir(self):
        return (self.dx,self.dy,self.dz)