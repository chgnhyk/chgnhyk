from svgpathtools import svg2paths
import numpy as np
import io

def getUniformPath(_path, _step:float = 2.0):
    paths, _ = svg2paths(_path)

    points = []
    step = _step

    xmin = ymin = float("inf")
    xmax = ymax = float("-inf")

    for path in paths:
        bxmin, bxmax, bymin, bymax = path.bbox()
        xmin = min(xmin, bxmin)
        xmax = max(xmax, bxmax)
        ymin = min(ymin, bymin)
        ymax = max(ymax, bymax)

        length = path.length()
        n = int(length / step)
        for i in range(n):
            p = path.point(i / n)
            points.append((p.real, p.imag))
    width = xmax - xmin
    height = ymax - ymin
    #print(width, height, xmin, ymin)
    return {
        "points": points,
        "width": width,
        "height": height
    }

def getUniformLengthPath(svg_path, target_points=600, should_normalize=False, is_string_data=False):
    if is_string_data == True:
        f = io.StringIO(svg_path)
        paths, _ = svg2paths(f)
    else:
        paths, _ = svg2paths(svg_path)

    points = []

    xmin = ymin = float("inf")
    xmax = ymax = float("-inf")

    # --- bbox ---
    for path in paths:
        bxmin, bxmax, bymin, bymax = path.bbox()
        xmin = min(xmin, bxmin)
        xmax = max(xmax, bxmax)
        ymin = min(ymin, bymin)
        ymax = max(ymax, bymax)

    # --- total length ---
    total_length = sum(p.length() for p in paths)
    #print(total_length)
    step = total_length / target_points  # 👈 this is the key

    # --- uniform arc-length sampling ---
    for path in paths:
        length = path.length()
        n = max(1, int(length / step))

        for i in range(n):
            s = i * step
            t = path.ilength(s)  # convert arc length → t
            p = path.point(t)
            points.append((p.real, p.imag))

    # --- enforce exact count ---
    points = points[:target_points]

    width = xmax - xmin
    height = ymax - ymin

    mx_sz = max(width, height)

    if should_normalize:
        for i in range(len(points)):
            points[i] = ((points[i][0]-xmin)/mx_sz, (points[i][1]-ymin)/mx_sz)
        return {
            "points": points,
            "width": width/mx_sz,
            "height": height/mx_sz
        }
    else:
        return {
            "points": points,
            "width": width,
            "height": height
        }

def svgPath(lst:iter):
    svg_str = "<path d='"

    for idx, itm in enumerate(lst):
        if idx == 0:
            svg_str += f"M {itm[0]} {itm[1]}" 
        else:
            svg_str += f" L {itm[0]} {itm[1]}" 
    svg_str += "' stroke-width='0.5' stroke='black' fill='transparent'/>"

    return svg_str

