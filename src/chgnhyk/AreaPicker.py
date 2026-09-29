import math
import random

class AreaCell:
    def __init__(self, x, y, idx):
        self.filled = False
        self.x = x
        self.y = y
        self.idx = idx
        #seed(0)
        pass

class AreaPicker:
    def __init__(self, w:int, h:int, seed:int=0):
        self.reset(w, h, seed)
        self.min_w = 0
        

    def reset(self, w:int, h:int, seed:int=0):
        self.rects = []
        self.depleted = False
        self.seed = seed
        random.seed(self.seed)
        self.setGrid(w, h)
        

    def setGrid(self, w:int, h:int):
        self.gw = w
        self.gh = h
        self.cells = []
        self.pool = []
        for x in range(self.gw):
            for y in range(self.gh):
                idx = x + y * self.gw
                self.cells.append(AreaCell(x, y, idx))
                self.pool.append(idx)

    def pickArea(self):
        if len(self.pool) == 0:
            self.depleted = True
            return
        
        pck_idx = random.randint(0, len(self.pool)-1)
        pck_idx = self.pool[pck_idx]

        pck_y_idx = math.floor(pck_idx/self.gw)
        pck_x_idx = pck_idx % self.gw

        x_dir = -1 if random.random() > 0.5 else 1
        y_dir = -1 if random.random() > 0.5 else 1
        avail_w = 0
        avail_h = self.gh

        x = pck_x_idx
        while 0 <= x < self.gw:
            xidx = x + pck_y_idx * self.gw
            col_avail_h = 0
            y = pck_y_idx
            while 0 <= y < self.gh:
                yidx = x + y * self.gw
                if self.cells[yidx].filled:
                    break
                col_avail_h += 1
                y += y_dir
            
            avail_h = min(avail_h, col_avail_h)
            if self.cells[xidx].filled:
                break
            avail_w += 1
            x += x_dir 

        # TODO --> need to think about this
        # if avail_w < self.min_w and avail_h < self.min_w:
        #     self.cells[pck_idx].filled = True
        #     if pck_idx in self.pool:
        #         self.pool.remove(pck_idx)
        #     return
        
        if avail_w > self.min_w:
            rw = random.randint(self.min_w, avail_w-1)
        else:
            rw = max(0, min(self.min_w, avail_w-1))

        if avail_h > self.min_w:
            rh = random.randint(self.min_w, avail_h-1)
        else:
            rh = max(0, min(self.min_w, avail_h-1))

        x_strt =  pck_x_idx if (x_dir == 1) else pck_x_idx-rw
        x_end = pck_x_idx+rw if (x_dir == 1) else  pck_x_idx
        y_strt = pck_y_idx if (y_dir == 1) else pck_y_idx-rh
        y_end = pck_y_idx+rh if (y_dir == 1) else pck_y_idx

        #print(x_strt, x_end, y_strt, y_end, x_dir, y_dir)

        for x in range(x_strt, x_end+1, 1):
            for y in range(y_strt, y_end+1, 1):
                idx = x + y * self.gw
                
                self.cells[idx].filled = True
                if idx in self.pool:
                    self.pool.remove(idx)
                    
        self.rects.append({
            "x": x_strt, 
            "y": y_strt, 
            "w": abs(x_end-x_strt)+1, 
            "h": abs(y_end-y_strt)+1
        })

        if len(self.pool) == 0:
            self.depleted = True
            
        