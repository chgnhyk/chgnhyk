import numpy as np
from PIL import Image
import moderngl
import time as tm
from typing import Union
from .utils import FakeUniform, EXT_MAP
from pathlib import Path
import os

try:
    import cv2
except ImportError:
    cv2 = None

class FBO:

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

    def __init__(self, ctx, size, shader, enable_backbuffer = False, rest_time = 0.0):
        self.ctx = ctx
        self.size = size
        self.enable_backbuffer = enable_backbuffer
        self.rest_time = rest_time

        self.texture = self.ctx.texture(self.size, components=4, dtype="f4")
        self.fbo = self.ctx.framebuffer(self.texture)
        self.prog = self.ctx.program(
            vertex_shader=self.quad_vertex_shader, fragment_shader=shader)

        vertex_data = np.array([
            -1.0, -1.0, 0.0, 0.0,
            +1.0, -1.0, 1.0, 0.0,
            -1.0, +1.0, 0.0, 1.0,
            +1.0, +1.0, 1.0, 1.0,
        ]).astype(np.float32)

        content = [(
            self.ctx.buffer(vertex_data),
            '2f 2f',
            'in_vert', 'in_uv'
        )]

        self.vao = self.ctx.vertex_array(self.prog, content)

        self.time = self.prog.get('time', FakeUniform())
        self.resolution = self.prog.get('resolution', FakeUniform())

        if self.resolution:
            self.resolution.value = self.size
        else:
            print(f'unable to set resolution uniform {self.resolution}')

        self.textures = {}
        self.texture_uniforms = {}

        if self.enable_backbuffer == True:
            self.bck_texture = self.ctx.texture(
                self.size, components=4, dtype="f4")
            self.bck_fbo = self.ctx.framebuffer(self.bck_texture)
            self.bck_prog = self.ctx.program(
                vertex_shader=self.quad_vertex_shader, fragment_shader=self.copier_fragment_shader)
            self.bck_vao = self.ctx.vertex_array(self.bck_prog, content)
            
            self.set_texture_uniform(self.bck_texture, "bckbuffer", 0)
            
            self.copy_target_uniform = self.bck_prog.get(
                'copy_target', FakeUniform())
            self.copy_target_uniform.value = 0
        else:
            self.bck_fbo = None

        

    def release_all(self):
        if hasattr(self, 'bck_texture'):
            self.bck_texture.release()
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

    def set_texture_uniform_from_pil(self, pil_img, name, id, reload=True):
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
        # if name in self.textures and reload == True:
        #     self.textures[name].release()
        if name not in self.textures or reload == True:
            self.texture_uniforms[name] = self.prog.get(name, FakeUniform())
            self.textures[name] = texture
        self.texture_uniforms[name].value = id
        self.set_uniform(f"{name}_res", texture.size)

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

    def render(self, render_to_window = False):
        if self.rest_time > 0.0:
            tm.sleep(self.rest_time)

        if render_to_window:
            self.ctx.screen.use()
        else:
            
            self.fbo.use()

        for (name, texture) in self.textures.items():
            textureid = self.texture_uniforms[name].value
            self.textures[name].use(location=textureid)

        # if self.enable_backbuffer == True:
        #     self.bck_texture.use(location=0)
            # not sure why, but this does not work properly when using multipass if location is 2
            # for some reason location 0 seems to works okay, even though it is same as copy_target     
        
        self.vao.render(moderngl.TRIANGLE_STRIP)

        if self.enable_backbuffer == True:
            self.bck_fbo.use()
            self.texture.use(location=0)
            self.bck_vao.render(moderngl.TRIANGLE_STRIP)

    def release(self, name):
        for (_name, texture) in self.textures.items():
            if _name == name:
                texture.release()


