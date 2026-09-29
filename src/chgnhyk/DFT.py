import math 

class Cmplx:
    def __init__(self, a, b):
        self.re = a
        self.im = b
        pass

    def add(self, c):
        self.re += c.re
        self.im += c.im
    
    def mult(self, c):
        _re = self.re * c.re - self.im * c.im
        _im = self.re * c.im + self.im * c.re
        return Cmplx(_re, _im)

def DFT(x:iter, w, h, compress=0):

    X = []
    N = len(x)
    for i in range(N):
        x[i] = Cmplx(x[i][0]-w*0.5,x[i][1]-h*0.5)

    for k in range(N):
        _sum = Cmplx(0, 0)
        for n in range (N):
            phi = (math.pi * 2 * k * n) / N
            c = Cmplx(math.cos(phi), -math.sin(phi))
            _sum.add(x[n].mult(c))
        _sum.re = _sum.re / N
        _sum.im = _sum.im / N

        #freq = k
        freq = k if k <= N//2 else k - N
        amp = math.sqrt(_sum.re * _sum.re + _sum.im * _sum.im)
        phase = math.atan2(_sum.im, _sum.re)

        X.append({
            "re": _sum.re,
            "im": _sum.im,
            "freq": freq,
            "amp": amp,
            "phase": phase
        })

    if compress > 0 and compress < len(x):
        X.sort(key=lambda c: c["amp"], reverse=True)
        X = X[:compress]

    return X

def MixF(X1, X2, t):
    X = []
    for i in range(len(X1)):
        re1 = X1[i]["re"]
        im1 = X1[i]["im"]

        re2 = X2[i]["re"]
        im2 = X2[i]["im"]

        re = (1.0-t)*re1 + t*re2
        im = (1.0-t)*im1 + t*im2
        X.append({
            "re": re,
            "im": im,
            "freq": X1[i]["freq"]
        })
    return X

def MixSortedF(X1, X2, t):
    X = []

    # Build lookup tables by frequency
    A = {c["freq"]: c for c in X1}
    B = {c["freq"]: c for c in X2}

    # Union of all frequencies
    freqs = set(A.keys()) | set(B.keys())

    for k in freqs:
        c1 = A.get(k)
        c2 = B.get(k)

        # Zero-fill if missing
        re1 = c1["re"] if c1 else 0.0
        im1 = c1["im"] if c1 else 0.0

        re2 = c2["re"] if c2 else 0.0
        im2 = c2["im"] if c2 else 0.0

        # Linear interpolation
        re = (1.0 - t) * re1 + t * re2
        im = (1.0 - t) * im1 + t * im2

        X.append({
            "re": re,
            "im": im,
            "freq": k
        })

    return X

def epiCycle(x, y, timer, rotation, fourier:iter):
    _x = x
    _y = y
    for i in range(len(fourier)):
        re = fourier[i]["re"]
        im = fourier[i]["im"]
        freq = fourier[i]["freq"] #i if i <= len(fourier)//2 else i - len(fourier)
        radius = math.sqrt(re * re + im * im)
        phase = math.atan2(im, re)
        _x += radius * math.cos(freq * timer + phase + rotation)
        _y += radius * math.sin(freq * timer + phase + rotation)

    return (_x,_y)