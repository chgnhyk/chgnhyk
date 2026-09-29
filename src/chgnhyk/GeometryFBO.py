import math
import numpy as np
from .utils import FakeUniform
from PIL import Image
import moderngl
from typing import Union, Callable
import trimesh
from pyrr import Matrix44

try:
    import cv2
except ImportError:
    cv2 = None

def to_clip_space(pos:tuple, w=1, h=1):
    x, y = pos
    cx = x/w
    cy = y/h
    cy = 1 - cy
    cx = cx*2 - 1
    cy = cy*2 - 1
    return (cx, cy)

def size_to_clip_space(size:Union[tuple, float], w=1, h=1):
    if isinstance(size, tuple):
        return (2*size[0]/w, 2*size[1]/h)
    else:
        return 2*size/w
    
def build_thick_line(a, b, thickness, id, size=(1,1), capped=True):
    dir = (b[0] - a[0], b[1] - a[1])
    dirl = math.sqrt(dir[0]*dir[0]+dir[1]*dir[1])
    dirl = max(dirl,0.001)
    dir = (dir[0]/dirl,dir[1]/dirl)
    normal = np.array([-dir[1], dir[0]])
    offset = normal * (thickness / 2)

    if capped:
        a = a[0]-dir[0] * (thickness / 2), a[1]-dir[1] * (thickness / 2)
        b = b[0]+dir[0] * (thickness / 2), b[1]+dir[1] * (thickness / 2)
        dir = (b[0] - a[0], b[1] - a[1])
        dirl = math.sqrt(dir[0]*dir[0]+dir[1]*dir[1])
        
    a1 = a + offset
    a2 = a - offset
    b1 = b + offset
    b2 = b - offset

    a1 = to_clip_space(a1, size[0], size[1])
    a2 = to_clip_space(a2, size[0], size[1])

    b1 = to_clip_space(b1, size[0], size[1])
    b2 = to_clip_space(b2, size[0], size[1])

    lt = (0.0,0.0)
    lb = (0.0,1.0)
    rt = (1.0,0.0)
    rb = (1.0,1.0)

    ratio = (dirl, thickness)

    return np.array([
        [*a1, *lb, id, *ratio], 
        [*b1, *rb, id, *ratio],
        [*b2, *rt, id, *ratio],
        [*a1, *lb, id, *ratio],
        [*b2, *rt, id, *ratio],
        [*a2, *lt, id, *ratio],
    ], dtype='f4')

def build_thick_point(a:tuple, thickness:tuple, id:float):
    offset = (thickness[0]/2, thickness[1]/2)

    a1 = (a[0]-offset[0],a[1]+offset[1]) 
    a2 = (a[0]-offset[0],a[1]-offset[1]) 
    b1 = (a[0]+offset[0],a[1]+offset[1]) 
    b2 = (a[0]+offset[0],a[1]-offset[1]) 

    lt = (0.0,0.0)
    lb = (0.0,1.0)
    rt = (1.0,0.0)
    rb = (1.0,1.0)

    ratio = (thickness[0], thickness[1])

    return np.array([
        [*a1, *lb, id, *ratio], 
        [*b1, *rb, id, *ratio],
        [*b2, *rt, id, *ratio],
        [*a1, *lb, id, *ratio],
        [*b2, *rt, id, *ratio],
        [*a2, *lt, id, *ratio],
    ], dtype='f4')

def create_line_data(data:iter, id:int=0, w:float=2, size:tuple=(1.,1.)):
    lines = []
    for i in range(0, len(data)-1, 2):
        a = data[i]
        b = data[i+1]
        lines.append([a,b])
        
    line_data = []
    for idx, (line_start, line_end) in enumerate(lines):
        # line_data.append(build_thick_line(
        #     to_clip_space(line_start, size[0], size[1]), 
        #     to_clip_space(line_end, size[0], size[1]), 
        #     size_to_clip_space(w, size[0], size[1]), id)
        lw = w
        lid = id
        if "stroke_width" in line_start:
            lw = line_start["stroke_width"]
        if "id" in line_start:
            lid = line_start["id"]
        line_data.append(build_thick_line(
            line_start["pos"], line_end["pos"], lw, lid, size
        ))
    return line_data

def create_pnt_data(data:iter, size:tuple=(1.,1.)):
    pnt_data = []
    for (idx, pnt) in enumerate(data):
        pnt_data.append(build_thick_point(
            to_clip_space(pnt["pos"], size[0], size[1]), 
            size_to_clip_space(pnt["size"], size[0], size[1]), 
            pnt["id"]))
    return pnt_data

class Geom2DFBO:

    vert_shader = '''
    #version 330

    in vec2 in_vrt;
    in vec2 in_uv;
    in float id;
    in vec2 ratio;

    out vec2 UV;
    out float ID;
    out vec2 RATIO;
    out vec2 POS;

    void main() {
        ID = id;
        RATIO = ratio;
        UV = in_uv;
        POS = in_vrt;
        gl_Position = vec4(in_vrt, 0.0, 1.0);
    }
    '''

    def __init__(self, ctx:moderngl.Context, size:tuple, max_num:int, shader:str, vertex_shader:str=""):
        self.ctx = ctx
        self.size = size
        if vertex_shader != "":
            self.vert_shader = vertex_shader
        self.prog = self.ctx.program(
            vertex_shader=self.vert_shader,
            fragment_shader=shader,
        )
        self.texture = self.ctx.texture(self.size, components=4, dtype="f4")
        self.fbo = self.ctx.framebuffer(self.texture)
        self.set_uniform("resolution", self.size)

        self.vbo = self.ctx.buffer(reserve=(max_num*6)*7*4)
        self.vao = self.ctx.simple_vertex_array(self.prog, self.vbo, "in_vrt", "in_uv", "id", "ratio")

        self.bck_col = (0, 0, 0)

        self.data = None
        self.line_w = None
        self.mode = "points"
        self.textures = {}
        self.texture_uniforms = {}

        self.blend_func = None

    def setBlendFunc(self, func:Callable):
        self.blend_func = func

    
    
    def release_all(self):
        for (name, texture) in self.textures.items():
            self.textures[name].release()
        self.texture.release()

    def set_uniform(self, name, value):
        uniform = self.prog.get(name, FakeUniform())
        uniform.value = value
    
    def set_texture_uniform_from_path(self, path, name, id, reload=True):
        im = Image.open(path)
        im_WIDTH, im_HEIGHT, im_DATA = im.size[0], im.size[1], im.convert(
            'RGBA').tobytes("raw", "RGBA", 0, -1)
        path_texture = self.ctx.texture(
            (im.size[0], im.size[1]), components=4, data=im_DATA)
        self.set_texture_uniform(path_texture, name, id, reload)

    def set_texture_uniform_from_pil(self, pil_img:Image, name, id, reload=True):
        im_WIDTH, im_HEIGHT, im_DATA = pil_img.size[0], pil_img.size[1], pil_img.convert(
            'RGBA').tobytes("raw", "RGBA", 0, -1)
        pil_texture = self.ctx.texture(
            (pil_img.size[0], pil_img.size[1]), components=4, data=im_DATA)
        self.set_texture_uniform(pil_texture, name, id, reload)

    def set_texture_uniform_from_cv2(self, cv2img, name, id, reload=True):
        if cv2 is None:
            raise ImportError(
                "OpenCV is required for this feature. "
                "Install it with: pip install chgnhyk[opencv]"
            )
        correct_img = cv2.cvtColor(cv2img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(correct_img)
        im_WIDTH, im_HEIGHT, im_DATA = pil_img.size[0], pil_img.size[1], pil_img.convert(
            'RGBA').tobytes("raw", "RGBA", 0, -1)
        cv_texture = self.ctx.texture(
            (im_WIDTH, im_HEIGHT), components=4, data=im_DATA)
        self.set_texture_uniform(cv_texture, name, id, reload)

    def set_texture_uniform(self, texture, name, id, reload=False):
        if name not in self.textures or reload == True:
            self.texture_uniforms[name] = self.prog.get(name, FakeUniform())
            self.textures[name] = texture
        self.texture_uniforms[name].value = id

    def extract_img(self, path, format='png', quality=100):
        if format=='jpeg':
            image = Image.frombytes('RGB', self.size, self.fbo.read(components=3))
        else:
            image = Image.frombytes('RGBA', self.size, self.fbo.read(components=4))
        image = image.transpose(Image.FLIP_TOP_BOTTOM)
        image.save(path, format=format, quality=quality)
    
    def extract_img_raw(self, format='jpeg'):
        if format == 'jpeg':
            image = self.fbo.read(components=3)
        else:
            image = self.fbo.read(components=4)
        return image

    def extract_np_img(self) -> np.ndarray:
        img_buf = self.fbo.read()
        img_width = self.fbo.size[0]
        img_height = self.fbo.size[1]
        img = np.frombuffer(img_buf, np.uint8).reshape(img_height, img_width, 3)[::-1]
        return img

    def setData(self, data:iter, mode="points", line_w:float=0.02):
        self.data = data
        self.mode = mode
        self.line_w = line_w

    def release(self, name):
        for (_name, texture) in self.textures.items():
            if _name == name:
                texture.release()

    def setClearColor(self, color:tuple):
        self.bck_col = color

    def render(self):
        if self.data == None:
            return
        
        self.fbo.use()
        self.fbo.clear(*self.bck_col)

        #self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
        self.ctx.blend_equation = moderngl.FUNC_ADD, moderngl.MAX

        # self.ctx.blend_func = moderngl.ONE, moderngl.ONE_MINUS_SRC_ALPHA
        # self.ctx.blend_equation = moderngl.FUNC_ADD

        if callable(self.blend_func):
            self.blend_func()

        # self.ctx.blend_func = moderngl.ONE, moderngl.ONE_MINUS_SRC_ALPHA
        # self.ctx.blend_equation = moderngl.FUNC_ADD

        # self.ctx.blend_equation = moderngl.FUNC_ADD, moderngl.MAX 
        # self.ctx.blend_func = moderngl.ONE, moderngl.ZERO
        

        for (name, texture) in self.textures.items():
            textureid = self.texture_uniforms[name].value
            self.textures[name].use(location=textureid)

        if len(self.data) > 0:
            if self.mode == "points":
                self.drawPoints(self.data)
            elif self.mode == "lines":
                self.drawLines(self.data, w=self.line_w)

    
    def drawLines(self, data:iter, id:int=0, w:float=2):
        self.vbo.clear()
        line_data = create_line_data(data, id, w, self.size)
        line_data = np.concatenate(line_data)
        self.vbo.write(line_data.tobytes())
        self.vao.render(moderngl.TRIANGLES, instances=1, vertices=len(line_data))

    def drawPoints(self, data:iter):
        self.vbo.clear()
        pnt_data = create_pnt_data(data, self.size)
        pnt_data = np.concatenate(pnt_data)
        self.vbo.write(pnt_data.tobytes())
        self.vao.render(moderngl.TRIANGLES, instances=1, vertices=len(pnt_data))


class Geom3DFBO:
    vert_shader = '''
    #version 330

    in vec3 in_vrt;
    in vec3 in_nrm;
    in float id;

    out vec3 NORM;
    out float ID;

    uniform mat4 Mvp;

    void main() {
        ID = id;
        NORM = normalize(in_nrm);
        vec3 pos = in_vrt;
        gl_Position = Mvp * vec4(pos, 1.0);
    }
    '''

    def __init__(self, ctx:moderngl.Context, size:tuple, shader:str, vertex_shader:str=''):
        self.ctx = ctx
        self.size = size
        
        if vertex_shader != '':
            self.vert_shader = vertex_shader
        self.prog = self.ctx.program(
            vertex_shader=self.vert_shader,
            fragment_shader=shader,
        )
        self.texture = self.ctx.texture(self.size, components=4, dtype="f4")
        self.depth = self.ctx.depth_renderbuffer(self.size)
        self.fbo = self.ctx.framebuffer(self.texture, self.depth)
        self.set_uniform("resolution", self.size)

        self.vbo = None
        self.vao = None

        self.bck_col = (0, 0, 0)

        self.data = None
        self.vertex_data = None
        self.norm_data = None

        self.textures = {}
        self.texture_uniforms = {}

        self.mvp = self.prog.get('Mvp', FakeUniform())
        
        

    def setCameraMatrix(self, 
                        fov:float=45,
                        mindist:float=0.1,
                        maxdist:float=1000,
                        campos:tuple=(0,0,3), 
                        lookat:tuple=(0,0,0), 
                        up:tuple=(0,1,0)):
        self.proj = Matrix44.perspective_projection(fov, self.size[0]/self.size[1], mindist, maxdist)

        self.camera = campos
        self.look_at = lookat
        self.view_up = up
        self.view = Matrix44.look_at(
            self.camera,
            self.look_at,
            self.view_up,
        )
        self.mvp.write((self.proj * self.view).astype('f4'))
    
    def release_all(self):
        for (name, texture) in self.textures.items():
            self.textures[name].release()
        self.texture.release()

    def set_uniform(self, name, value):
        uniform = self.prog.get(name, FakeUniform())
        uniform.value = value
    
    def set_texture_uniform_from_path(self, path, name, id, reload=True):
        im = Image.open(path)
        im_WIDTH, im_HEIGHT, im_DATA = im.size[0], im.size[1], im.convert(
            'RGBA').tobytes("raw", "RGBA", 0, -1)
        path_texture = self.ctx.texture(
            (im.size[0], im.size[1]), components=4, data=im_DATA)
        self.set_texture_uniform(path_texture, name, id, reload)

    def set_texture_uniform_from_pil(self, pil_img:Image, name, id, reload=True):
        im_WIDTH, im_HEIGHT, im_DATA = pil_img.size[0], pil_img.size[1], pil_img.convert(
            'RGBA').tobytes("raw", "RGBA", 0, -1)
        pil_texture = self.ctx.texture(
            (pil_img.size[0], pil_img.size[1]), components=4, data=im_DATA)
        self.set_texture_uniform(pil_texture, name, id, reload)

    def set_texture_uniform_from_cv2(self, cv2img, name, id, reload=True):
        if cv2 is None:
            raise ImportError(
                "OpenCV is required for this feature. "
                "Install it with: pip install chgnhyk[opencv]"
            )
        correct_img = cv2.cvtColor(cv2img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(correct_img)
        im_WIDTH, im_HEIGHT, im_DATA = pil_img.size[0], pil_img.size[1], pil_img.convert(
            'RGBA').tobytes("raw", "RGBA", 0, -1)
        cv_texture = self.ctx.texture(
            (im_WIDTH, im_HEIGHT), components=4, data=im_DATA)
        self.set_texture_uniform(cv_texture, name, id, reload)

    def set_texture_uniform(self, texture, name, id, reload=False):
        if name not in self.textures or reload == True:
            self.texture_uniforms[name] = self.prog.get(name, FakeUniform())
            self.textures[name] = texture
        self.texture_uniforms[name].value = id

    def extract_img(self, path, format='png', quality=100):
        if format=='jpeg':
            image = Image.frombytes('RGB', self.size, self.fbo.read(components=3))
        else:
            image = Image.frombytes('RGBA', self.size, self.fbo.read(components=4))
        image = image.transpose(Image.FLIP_TOP_BOTTOM)
        image.save(path, format=format, quality=quality)
    
    def extract_img_raw(self, format='jpeg'):
        if format == 'jpeg':
            image = self.fbo.read(components=3)
        else:
            image = self.fbo.read(components=4)
        return image

    def extract_np_img(self) -> np.ndarray:
        img_buf = self.fbo.read()
        img_width = self.fbo.size[0]
        img_height = self.fbo.size[1]
        img = np.frombuffer(img_buf, np.uint8).reshape(img_height, img_width, 3)[::-1]
        return img

    def setData(self, data:iter):
        self.data = data

    def load3DModel(self, path:str):
        mesh = trimesh.load_mesh(path)
        # mesh.rezero()          # optional: clean tiny float offsets
        # mesh.remove_infinite_values()
        # mesh.remove_unreferenced_vertices()
        mesh.fix_normals()
        #mesh.faces = mesh.faces[:, ::-1]
        mesh.apply_translation(-mesh.bounding_box.centroid)
        # bounds = mesh.bounding_box.bounds
        # cx, cy, cz = (bounds[0][0]+bounds[1][0])*0.5, (bounds[0][1]+bounds[1][1])*0.5, (bounds[0][2]+bounds[1][2])*0.5
        self.vertex_data = mesh.vertices[mesh.faces].reshape(-1, 3)
        self.norm_data = mesh.vertex_normals[mesh.faces].reshape(-1, 3)
        # self.norm_data = mesh.face_normals.repeat(3, axis=0)
    
        self.data = []
        for i in range(len(self.vertex_data)):
            self.data.extend(self.vertex_data[i])
            self.data.extend(self.norm_data[i])
            self.data.append(i)

        self.vertex_count = len(self.data) // 7


    def writeData(self, data_format:iter=["3f 3f 1f", "in_vrt", "in_nrm", "id"]):
        if self.vbo != None:
            self.vbo.release()
        if self.vao != None:
            self.vao.release()
        
        self.vbo = self.ctx.buffer(reserve=len(self.data)*4)
        self.vao = self.ctx.vertex_array(self.prog, [(self.vbo, *data_format)])
        
        self.vbo.clear()
        v_data = np.array(self.data, dtype='f4')
        self.vbo.write(v_data.tobytes())

    def release(self, name):
        for (_name, texture) in self.textures.items():
            if _name == name:
                texture.release()

    def setClearColor(self, color:tuple):
        self.bck_col = color

    def render(self):
        if self.data == None:
            return
        
        self.fbo.use()
        self.fbo.clear(*self.bck_col)
        #self.ctx.clear_depth = 1.0

        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.enable(moderngl.BLEND)

        for (name, texture) in self.textures.items():
            textureid = self.texture_uniforms[name].value
            self.textures[name].use(location=textureid)

        
        self.vao.render(moderngl.TRIANGLES, instances=1, vertices=self.vertex_count)

