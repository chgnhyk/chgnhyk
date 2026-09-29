from .FBOPass import FBO
from .utils import FakeUniform
import time as tm
from .utils import progress_bar
import numpy as np
import os
import glob
from typing import Union
from pathlib import Path
from PIL import Image

def get_concat_h(im1, im2):
    dst = Image.new('RGB', (im1.width + im2.width, im1.height))
    dst.paste(im1, (0, 0))
    dst.paste(im2, (im1.width, 0))
    return dst

def get_concat_v(im1, im2):
    dst = Image.new('RGB', (im1.width, im1.height + im2.height))
    dst.paste(im1, (0, 0))
    dst.paste(im2, (0, im1.height))
    return dst



class TileFBO:

    tiler_fragment_shader = '''
    #version 330
    out vec4 outputColor;
    in vec2 UV;

    uniform sampler2D bckbuffer;
    uniform sampler2D scene_buffer;

    uniform float render_compression;
    uniform float render_count;

    void main()
    {
        vec2 ouv = UV;
        vec2 uid = floor(ouv * render_compression);
        vec2 fuv = fract(ouv * render_compression);
        float render_index = uid.x + uid.y * render_compression;

        if(render_index == render_count){
            outputColor = texture(scene_buffer, fuv);
        }else{
            outputColor = texture(bckbuffer, ouv);
        }
        
    }
    '''

    def __init__(self, ctx, size, shader, render_compression, tile_path, only_tiles = False, log_off = False, rest_time = 0.0, alpha = False, cleanup = True):
        self.tile_path = tile_path
        self.rest_time = rest_time
        self.log_off = log_off
        self.alpha = alpha
        self.cleanup = cleanup
        self.ctx = ctx

        self.size = size
        self.render_compression = render_compression
        self.only_tiles = only_tiles

        if self.only_tiles == False:
            self.fbo = FBO(ctx = ctx, size = self.size, shader = self.tiler_fragment_shader, enable_backbuffer = True)

        self.scene_size = (int(self.size[0] / self.render_compression), int(self.size[1] / self.render_compression))
        self.scene_fbo = FBO(ctx = ctx, size = self.scene_size, shader = shader, enable_backbuffer = False)
        
        if self.only_tiles == False:
            self.fbo.set_uniform('render_compression', self.render_compression)
            self.fbo.set_texture_uniform(self.scene_fbo.texture, 'scene_buffer', 6)

        self.scene_fbo.set_uniform('render_compression', self.render_compression)
        self.scene_fbo.set_uniform('sresolution', self.size)

    def concatenate_tiles(self, name='', rest_time = 0.05):
        for y in range(self.render_compression):
            for x in range(self.render_compression):
                if rest_time > 0.0:
                    tm.sleep(rest_time)
                idx = (self.render_compression - 1 - y) * self.render_compression + x
                progress_idx = x + self.render_compression * y
                progress_bar(100*(progress_idx+1)/(self.render_compression * self.render_compression), f"{progress_idx+1} of {self.render_compression * self.render_compression}")
                #print(f'{idx} of {render_compression * render_compression}')
                if x == 0:
                    img1 = Image.open(str(self.tile_path.joinpath(f'frame_{idx}.png')))
                    img1.save(str(self.tile_path.joinpath(f'whole_h_{y}.png')))
                else:
                    img1 = Image.open(str(self.tile_path.joinpath(f'whole_h_{y}.png')))
                    img2 = Image.open(str(self.tile_path.joinpath(f'frame_{idx}.png')))
                    get_concat_h(img1, img2).save(str(self.tile_path.joinpath(f'whole_h_{y}.png')))
            if y == 0:
                img1 = Image.open(str(self.tile_path.joinpath(f'whole_h_{y}.png')))
                img1.save(str(self.tile_path.joinpath('whole.png')))
            else:
                img1 = Image.open(str(self.tile_path.joinpath('whole.png')))
                img2 = Image.open(str(self.tile_path.joinpath(f'whole_h_{y}.png')))
                get_concat_v(img1, img2).save(str(self.tile_path.joinpath('whole.png')))
        
        whl_img = Image.open(str(self.tile_path.joinpath('whole.png')))
        whl_img.save(str(self.tile_path.parent.joinpath(f"whole_{name}.png")))
        print()

    def tile_render(self, render_idx, should_extract = False):
        self.scene_fbo.set_uniform('render_count', render_idx)
        self.scene_fbo.render()

        if should_extract:
            self.scene_fbo.extract_img(str(self.tile_path.joinpath(f'frame_{render_idx}.png')))

    def render(self):
        if self.render_compression == 1:
            for i in range(self.render_compression * self.render_compression):
                self.scene_fbo.set_uniform('render_count', i)
                self.scene_fbo.render()

                if self.only_tiles == False:
                    self.fbo.set_uniform('render_count', i)
                    self.fbo.render()

                scene_progress = 100 * (i+1) / (self.render_compression * self.render_compression)
                if self.log_off == False:
                    progress_bar(scene_progress, "scene rendering")
                #print(f'scene rendering : {scene_progress:.2f}%')
            if self.log_off is not False:
                #print()
                pass
        else:

            for i in range(self.render_compression * self.render_compression):
                if self.rest_time > 0.0:
                    tm.sleep(self.rest_time)
                self.scene_fbo.set_uniform('render_count', i)
                self.scene_fbo.render()
                
                if self.alpha:
                    self.scene_fbo.extract_img(str(self.tile_path.joinpath(f'frame_{i}.png')))
                else:
                    self.scene_fbo.extract_img(str(self.tile_path.joinpath(f'frame_{i}.jpg')), 'jpeg')
                    

                scene_progress = 100 * (i+1) / (self.render_compression * self.render_compression)
                if self.log_off == False:
                    progress_bar(scene_progress, "scene rendering")
                #print(f'scene rendering : {scene_progress:.2f}%')
            if self.log_off == False:
                print()

            if self.only_tiles == False:
                for i in range(self.render_compression * self.render_compression):
                    if self.rest_time > 0.0:
                        tm.sleep(self.rest_time)
                    if self.alpha:
                        self.fbo.set_texture_uniform_from_path(str(self.tile_path.joinpath(f'frame_{i}.png')), 'scene_buffer', 2)
                    else:
                        self.fbo.set_texture_uniform_from_path(str(self.tile_path.joinpath(f'frame_{i}.jpg')), 'scene_buffer', 2)
                    self.fbo.set_uniform('render_count', i)
                    self.fbo.render()

                    scene_progress = 100 * (i+1) / (self.render_compression * self.render_compression)
                    if self.log_off == False:
                        progress_bar(scene_progress, "scene copying")
                    #print(f'scene copying : {scene_progress:.2f}%')

                    self.fbo.release("scene_buffer")
                if self.log_off == False:
                    print()

    def set_uniform(self, name, value):
        self.scene_fbo.set_uniform(name, value)

    def set_texture_uniform(self, texture, name, id, reload=False):
        self.scene_fbo.set_texture_uniform(texture, name, id, reload)
    
    def extract_img(self, path: Union[str, Path], format='png', quality=100):
        if self.only_tiles == False:
            self.fbo.extract_img(path, format=format, quality=quality)
        else:
            print("Whole image extraction possible when 'only_tiles' option is False")
    
    def extract_img_raw(self, format='jpeg'):
        if self.only_tiles == False:
            return self.fbo.extract_img_raw(format=format)
        else:
            print("Whole image extraction possible when 'only_tiles' option is False")
            return None
    
    def extract_np_img(self) -> np.ndarray:
        return self.fbo.extract_np_img()

    def release(self, name):
        if self.only_tiles == False:
            self.fbo.release(name)
        self.scene_fbo.release(name)
        


    def release_all(self):
        if self.only_tiles == False:
            self.fbo.release_all()
        self.scene_fbo.release_all()

        if self.cleanup:
            files = glob.glob(f'{str(self.tile_path)}/*')
            for f in files:
                os.remove(f)