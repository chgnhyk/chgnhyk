import numpy as np
from PIL import Image
import moderngl
from pyrr import Matrix44
import math
from typing import Union
from .utils import FakeUniform, EXT_MAP
from pathlib import Path

def particle(i, num):

    x = np.random.uniform(-0.5, 0.5)
    y = np.random.uniform(-0.5, 0.5)
    z = 1 #np.random.uniform(-1.0, 1.0)

    r = np.random.uniform(0.0, 1.0)
    g = np.random.uniform(0.0, 1.0)
    b = np.random.uniform(0.0, 1.0)
    return [x, y, z, r, g, b]



class ParticlesFBO:

    quad_vertex_shader = '''
    #version 330
    in vec2 in_vert;
    in vec2 in_uv;
    out vec2 UV;
    void main() {
        gl_Position = vec4(in_vert, 0.0, 1.0);
        UV = in_uv;
    }
    '''
    copier_fragment_shader = '''
    #version 330
    out vec4 outputColor;
    in vec2 UV;

    uniform sampler2D copy_target;

    void main()
    {
        vec4 copy = texture(copy_target,UV);
        outputColor = copy;
    }
    '''

    def __init__(self, ctx, size, vertex_shader, fragment_shader, transform_shader, enable_backbuffer = False, rest_time = 0.0, num = 10000, particle_func = None):
        self.ctx = ctx
        self.size = size
        self.enable_backbuffer = enable_backbuffer

        self.texture = self.ctx.texture(self.size, components=4, dtype="f4")
        self.fbo = self.ctx.framebuffer(self.texture)
        self.prog = self.ctx.program(
            vertex_shader=vertex_shader, fragment_shader=fragment_shader)

        vertex_data = np.array([
            # x,    y,   z,    u,   v
            -1.0, -1.0, 0.0,  0.0, 0.0,
            +1.0, -1.0, 0.0,  1.0, 0.0,
            -1.0, +1.0, 0.0,  0.0, 1.0,
            +1.0, +1.0, 0.0,  1.0, 1.0,
        ]).astype(np.float32)

        content = [(
            self.ctx.buffer(vertex_data),
            '3f 2f',
            'in_vert', 'in_uv'
        )]

        self.transform_prog = self.ctx.program(
            vertex_shader = transform_shader, 
            varyings = ['out_pos', 'out_col'])

        self.particle_number = num

        self.particle_func = particle_func

        if callable(self.particle_func):
            particles = np.array([self.particle_func(i, self.particle_number) for i in range(self.particle_number)], dtype='f4')
        else:
            particles = np.array([particle(i, self.particle_number) for i in range(self.particle_number)], dtype='f4')

        self.vbo1 = self.ctx.buffer(particles.tobytes())
        self.vbo2 = self.ctx.buffer(reserve=self.vbo1.size)

        self.vao1 = self.ctx.vertex_array(self.transform_prog, [(self.vbo1, '3f 3f', 'in_pos', 'in_col')])
        self.vao2 = self.ctx.vertex_array(self.transform_prog, [(self.vbo2, '3f 3f', 'in_pos', 'in_col')])
        self.render_vao = self.ctx.vertex_array(self.prog, [(self.vbo1, '3f 3f', 'in_vert', 'in_col')])

        self.aspect_ratio = self.size[0] / self.size[1]
        self.mvp = self.prog.get('Mvp', FakeUniform())
        self.campos = self.transform_prog.get('CAMPOS', FakeUniform())
        self.real_cam = self.prog.get('CAMPOS', FakeUniform())
        self.time = self.prog.get('time', FakeUniform())
        self.resolution = self.prog.get('resolution', FakeUniform())

        if self.resolution:
            self.set_uniform("resolution", self.size)
        else:
            print(f'unable to set resolution uniform {self.resolution}')

        if self.enable_backbuffer == True:
            self.bck_texture = self.ctx.texture(
                self.size, components=4, dtype="f4")
            self.bck_fbo = self.ctx.framebuffer(self.bck_texture)
            self.bck_prog = self.ctx.program(
                vertex_shader=self.quad_vertex_shader, fragment_shader=self.copier_fragment_shader)
            self.bck_vao = self.ctx.vertex_array(self.bck_prog, content)

            self.backbuffer_uniform = self.prog.get(
                'backbuffer', FakeUniform())
            self.copy_target_uniform = self.bck_prog.get(
                'copy_target', FakeUniform())
        else:
            self.bck_fbo = None

        self.textures = {}
        self.texture_uniforms = {}
        self.textures_ = {}
        self.texture_uniforms_ = {}


        self.proj = Matrix44.perspective_projection(45.0, self.aspect_ratio, 0.1, 1000.0)
        self.lookat = Matrix44.look_at(
            (0.0, 0.0, 3.0),
            (0.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
        )
        self.set_cam((0.0, 0.0, 3.0))

        self.clear_col = (0.0,0.0,0.0)

    def set_clear_col(self, col:tuple = (0.0,0.0,0.0)):
        self.clear_col = col

    def release_all(self):
        if hasattr(self, 'bck_texture'):
            self.bck_texture.release()
        for (name, texture) in self.textures.items():
            self.textures[name].release()
            self.textures_[name].release()
        self.texture.release()

    def set_uniform(self, name, value):
        uniform = self.prog.get(name, FakeUniform())
        uniform.value = value

        uniform = self.transform_prog.get(name, FakeUniform())
        uniform.value = value

    def set_texture_uniform_from_path(self, path, name, id):
        im = Image.open(path)
        im_WIDTH, im_HEIGHT, im_DATA = im.size[0], im.size[1], im.convert(
            'RGBA').tobytes("raw", "RGBA", 0, -1)
        texture = self.ctx.texture(
            (im.size[0], im.size[1]), components=4, data=im_DATA)
        self.set_texture_uniform(texture, name, id)

    def set_texture_uniform(self, texture, name, id):
        if name not in self.textures:
            self.texture_uniforms[name] = self.prog.get(name, FakeUniform())
            self.textures[name] = texture

            self.texture_uniforms_[name] = self.transform_prog.get(name, FakeUniform())
            self.textures_[name] = texture
        self.texture_uniforms[name].value = id
        self.texture_uniforms_[name].value = id

    def clear(self):
        self.fbo.clear()
        if self.bck_fbo:
            self.bck_fbo.clear()

    def extract_img(self, path: Union[str, Path], format='png', quality=100):
        path_format = Path(path).suffix.lower().lstrip(".")
        path_format = EXT_MAP.get(path_format)
        if format != path_format:
            format = path_format
        
        if format == 'jpeg':
            image = Image.frombytes('RGB', self.size, self.fbo.read(components=3))
        else:
            image = Image.frombytes('RGBA', self.size, self.fbo.read(components=4))
        image = image.transpose(Image.FLIP_TOP_BOTTOM)
        image.save(str(path), format=format, quality=quality)

    def extract_np_img(self) -> np.ndarray:
        img_buf = self.fbo.read()
        img_width = self.fbo.size[0]
        img_height = self.fbo.size[1]
        img = np.frombuffer(img_buf, np.uint8).reshape(img_height, img_width, 3)[::-1]
        return img
    
    # def extract_vao(self, path, format='jpeg'):
    #     image = Image.frombytes('LA', (self.particle_number, self.particle_number), self.vbo1.read(size=-1,offset=2))
    #     image = image.transpose(Image.FLIP_TOP_BOTTOM)
    #     image.save(path, format=format)

    def set_cam(self, _campos, _lookat = (0,0,0), _up = (0,1,0)):
        self.campos.value =  _campos
        self.real_cam.value = _campos
        self.lookat = Matrix44.look_at(
            _campos,
            _lookat,
            _up,
        )
        self.mvp.write((self.proj * self.lookat).astype('f4'))

    def render(self):
        self.fbo.use()
        
        self.fbo.clear(*self.clear_col)
        self.ctx.enable(moderngl.PROGRAM_POINT_SIZE)
        self.ctx.enable(moderngl.BLEND)
        #self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.blend_equation = moderngl.FUNC_ADD, moderngl.MAX
        
        for (name, texture) in self.textures.items():
            # print(name, texture, self.texture_uniforms[name].value)
            textureid = self.texture_uniforms[name].value
            self.textures[name].use(textureid)
            self.texture_uniforms[name].value = textureid

            textureid_ = self.texture_uniforms_[name].value
            self.textures_[name].use(textureid_)
            self.texture_uniforms_[name].value = textureid_

        if self.enable_backbuffer == True:
            self.bck_texture.use(1)
            self.backbuffer_uniform.value = 1

        self.vao1.transform(self.vbo2, moderngl.POINTS, self.particle_number)
        self.ctx.copy_buffer(self.vbo1, self.vbo2)
        self.render_vao.render(moderngl.POINTS, self.particle_number)
        
        if self.enable_backbuffer == True:
            self.bck_fbo.use()

            self.texture.use(0)
            self.copy_target_uniform.value = 0

            self.bck_vao.render(moderngl.TRIANGLE_STRIP)
