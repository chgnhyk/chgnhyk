import moderngl_window
from moderngl_window.conf import settings
from moderngl_window.timers.clock import Timer
import math
import random
import os
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
from moviepy import ImageSequenceClip
import re
import time as tm

from .FBOPass import FBO
from .FBOTilePass import TileFBO
from .GeometryFBO import Geom2DFBO, Geom3DFBO
from typing import Union, Callable

class RealtimeEngine:
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

    def __init__(self, size=(540, 540), title='chgnhyk', frame_path='', fps=30):
        # Configure to use pyglet window
        settings.WINDOW["vsync"] = False
        settings.WINDOW["title"] = title
        settings.WINDOW["size"] = size
        settings.WINDOW["aspect_ratio"] = size[0] / size[1]
        settings.WINDOW["class"] = "moderngl_window.context.pyglet.Window"
        self.wnd = moderngl_window.create_window_from_settings()
        self.ctx = self.wnd.ctx
        self.size = size
        self.fps = fps
        self.real_fps = fps
        self.frame_count = 0
        self.is_recording = False
        self.has_recorded = False

        self.crr_tm = tm.time()
        self.strt_tm = tm.time()
        self.prv_tm = self.crr_tm - 1e8

        self.frame_path = frame_path

        # register event methods
        self.wnd.resize_func = self.on_resize
        self.wnd.iconify_func = self.on_iconify
        self.wnd.key_event_func = self.on_key_event
        self.wnd.mouse_position_event_func = self.on_mouse_position_event
        self.wnd.mouse_drag_event_func = self.on_mouse_drag_event
        self.wnd.mouse_scroll_event_func = self.on_mouse_scroll_event
        self.wnd.mouse_press_event_func = self.on_mouse_press_event
        self.wnd.mouse_release_event_func = self.on_mouse_release_event
        self.wnd.unicode_char_entered_func = self.on_unicode_char_entered
        self.wnd.close_func = self.on_close

        self.input_func = None
        self.passes = []

        self.render_fbo = FBO(ctx = self.ctx, size = self.size, shader = self.copier_fragment_shader)

        self._save_executor = ThreadPoolExecutor(max_workers=2)

    def setRenderFunc(self, input_func:Callable):
        self.input_func = input_func

    def addFBOPass(self, name: str, render_pass: Union[FBO, Geom2DFBO, Geom3DFBO], is_last = False):
        self.passes.append({
            "render_pass": render_pass,
            "name": name
        })

        if is_last:
            self.render_fbo.set_texture_uniform(render_pass.texture, "copy_target", 2)

    def on_render(self, time, frame_time):
        self.ctx.clear()
        if callable(self.input_func):
            self.input_func(self, time)
        for i in range(len(self.passes)):
            self.passes[i]["render_pass"].set_uniform("time", time)
            self.passes[i]["render_pass"].set_uniform("frame_time", frame_time)
            self.passes[i]["render_pass"].render()
            # else:
            #     self.passes[i]["render_pass"].render(render_to_window = True)
        self.render_fbo.render(render_to_window = True)

        if self.is_recording:
            self.save_frame()
            self.frame_count += 1

    def run(self):
        timer = Timer()
        timer.start()

        while not self.wnd.is_closing:
            self.crr_tm = tm.time()
            tm_dt = self.crr_tm - self.prv_tm
            tar_dt = 1.0/self.fps
            if tm_dt >= tar_dt:
                self.wnd.clear()
                time, frame_time = timer.next_frame()
                self.on_render(time, frame_time)
                self.wnd.swap_buffers()
            
                self.prv_tm = self.crr_tm

        self.wnd.destroy()

    def on_resize(self, width: int, height: int):
        print("Window was resized. buffer size is {} x {}".format(width, height))

    def on_iconify(self, iconify: bool):
        """Window hide/minimize and restore"""
        print("Window was iconified:", iconify)
    
    def _encode_video(self):
        # Gather and sort frames — sorting is critical for correct order
        frames = []
        for f in os.listdir(self.frame_path):
            m = re.match(r'^(\d{6})\.jpg$', f)
            if m and int(m.group(1)) < self.frame_count:
                frames.append(os.path.join(self.frame_path, f))
        frames.sort()
        
        clip = ImageSequenceClip(frames, fps=self.fps)  # your fps here
        clip.write_videofile(
            os.path.join(self.frame_path.parent, "output.mp4"),
            codec="libx264"
        )

    def save_frame(self, name=""):
        last_pass = self.passes[len(self.passes)-1]["render_pass"]
        raw = last_pass.extract_img_raw()
        size = last_pass.size
        
        filename = f"{str(self.frame_count).zfill(6)}.jpg"
        if name != "":
            filename = name

        self._save_executor.submit(self.write_frame, raw, size, self.frame_path, filename)

        # self.passes[len(self.passes)-1]["render_pass"].extract_img(self.frame_path.joinpath("test.jpg"))
    
    def write_frame(self, raw, size, frame_path, filename):
        image = Image.frombytes('RGB', size, raw)
        image = image.transpose(Image.FLIP_TOP_BOTTOM)

        os.makedirs(frame_path, exist_ok=True)
        out_path = os.path.join(frame_path, filename)
        image.save(out_path, format="JPEG", quality=100)


    def on_key_event(self, key, action, modifiers):
        keys = self.wnd.keys

        # Key presses
        if action == keys.ACTION_PRESS:
            if key == keys.SPACE:
                pass
                #print("SPACE key was pressed")

            # Using modifiers (shift and ctrl)

            if key == keys.Z and modifiers.shift:
                pass
                #print("Shift + Z was pressed")

            if key == keys.Z and modifiers.ctrl:
                pass
                #print("ctrl + Z was pressed")

        # Key releases
        elif action == self.wnd.keys.ACTION_RELEASE:
            if key == keys.SPACE:
                if self.frame_path != '':
                    self.save_frame(f"{int(tm.time()*100)}.jpg")
                #print("SPACE key was released")

        # Move the window around with AWSD
        if action == keys.ACTION_PRESS:
            if key == keys.A:
                self.wnd.position = self.wnd.position[0] - 10, self.wnd.position[1]
            if key == keys.D:
                self.wnd.position = self.wnd.position[0] + 10, self.wnd.position[1]
            if key == keys.W:
                self.wnd.position = self.wnd.position[0], self.wnd.position[1] - 10
            if key == keys.S:
                self.wnd.position = self.wnd.position[0], self.wnd.position[1] + 10

            # toggle cursor
            if key == keys.C:
                self.wnd.cursor = not self.wnd.cursor

            # Shuffle window tittle
            if key == keys.T:
                pass
                # title = list(self.wnd.title)
                # random.shuffle(title)
                # self.wnd.title = "".join(title)

            # Toggle mouse exclusivity
            if key == keys.M:
                self.wnd.mouse_exclusivity = not self.wnd.mouse_exclusivity

            # RECORD
            if key == keys.R:
                if self.frame_path != '':
                    if self.is_recording == True:
                        self.is_recording = False
                    else:
                        self.has_recorded = True
                        self.is_recording = True

    def on_mouse_position_event(self, x, y, dx, dy):
        #print("Mouse position pos={} {} delta={} {}".format(x, y, dx, dy))
        mx = 0.5*x/self.size[0]
        my = (1-0.5*(y/self.size[1]))
        for i in range(len(self.passes)):
            self.passes[i]["render_pass"].set_uniform("mouse_pos", (mx, my))

    def on_mouse_drag_event(self, x, y, dx, dy):
        #print("Mouse drag pos={} {} delta={} {}".format(x, y, dx, dy))
        pass

    def on_mouse_scroll_event(self, x_offset, y_offset):
        #print("mouse_scroll_event", x_offset, y_offset)
        pass

    def on_mouse_press_event(self, x, y, button):
        #print("Mouse button {} pressed at {}, {}".format(button, x, y))
        #print("Mouse states:", self.wnd.mouse_states)
        pass

    def on_mouse_release_event(self, x: int, y: int, button: int):
        #print("Mouse button {} released at {}, {}".format(button, x, y))
        #print("Mouse states:", self.wnd.mouse_states)
        pass

    def on_unicode_char_entered(self, char):
        #print("unicode_char_entered:", char)
        pass

    def on_close(self):
        for i in range(len(self.passes)):
            self.passes[i]["render_pass"].release_all()

        if self.has_recorded:
            self._save_executor.shutdown(wait=True)
            self._encode_video()

            for f in os.listdir(self.frame_path):
                if re.match(r'^(\d{6})\.jpg$', f):
                    os.remove(os.path.join(self.frame_path, f))
        print("Window was closed")