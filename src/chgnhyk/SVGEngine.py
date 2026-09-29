from typing import Callable

def Line(x1, y1, x2, y2):
    return f"""<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="black" stroke-width="0.5"/>"""

def Rect(x, y, w, h, r, g, b):
    return f"""<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="rgb({r},{g},{b})"/>"""

def svgPath(lst:iter):
    svg_str = "<path d='"

    for idx, itm in enumerate(lst):
        if idx == 0:
            svg_str += f"M {itm[0]} {itm[1]}" 
        else:
            svg_str += f" L {itm[0]} {itm[1]}" 
    svg_str += "' stroke-width='0.5' stroke='black' fill='transparent'/>"

    return svg_str

def svgLines(lst:iter, width=1, color='black'):
    svg_str = "<path d='"

    for idx, itm in enumerate(lst):
        svg_str += f"M {itm[0]} {itm[1]}" 
        svg_str += f" L {itm[2]} {itm[3]}" 
    svg_str += f"' stroke-width='{width}' stroke='{color}' fill='transparent'/>"

    return svg_str


class SVGEngine:
    def __init__(self, size=(500,500), unit='mm'):
        self.size = size
        self.body = ""
        self.header = f"""<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="{self.size[0]}{unit}" height="{self.size[1]}{unit}" viewBox="0 0 {self.size[0]} {self.size[1]}">"""
        self.footer = "</svg>"

        self.data = []

    def add_path(self):
        pass

    def add_lines(self, data, stroke_width=1, color='black'):
        self.body += svgLines(data, stroke_width, color)
    
    def get_svg_str(self):
        return self.header + self.body + self.footer
    
    def save_svg(self, path):
        with open(str(path), "w", encoding="utf-8") as f:
            f.write(self.get_svg_str())