from .FBOPass import FBO
from .FBOTilePass import TileFBO
from .FBOParticlePass import ParticlesFBO
from .GeometryFBO import Geom2DFBO, Geom3DFBO
from .utils import progress_bar
import moviepy
import time as tm
from typing import Union, Callable
import numpy as np
from pathlib import Path
import os
import math
import imageio.v2 as imageio
import av

def pil_to_texture(ctx, pil_img):
    im_WIDTH, im_HEIGHT, im_DATA = pil_img.size[0], pil_img.size[1], pil_img.convert(
        'RGBA').tobytes("raw", "RGBA", 0, -1)
    pil_texture = ctx.texture(
        (pil_img.size[0], pil_img.size[1]), components=4, data=im_DATA)
    return pil_texture

class Video:
    def __init__(self, path):
        self.container = av.open(path)
        self.stream = self.container.streams.video[0]

    def get_frame_at_time(self, seconds):
        timestamp = int(seconds / self.stream.time_base)

        self.container.seek(
            timestamp,
            stream=self.stream
        )

        for frame in self.container.decode(self.stream):
            if frame.time is not None and frame.time >= seconds:
                return frame.to_image()

        return None

    def close(self):
        self.container.close()

class ClipRenderer:
    def __init__(self, duration, fps, rest_time = 0.0, frames_folder:Path = Path('')):
        """
        Single video rendered with single or multiple FBO, TileFBO
        """
        self.duration = duration
        self.fps = fps
        self.render_length = duration * fps
        self.rest_time = rest_time
        self.input_func = None
        self.strt_func = None
        self.passes = []
        self.t = 0.0
        self.frames_folder = frames_folder
        self.videos = []

        self.should_save_frames = False

    def resetDuration(self, duration):
        self.duration = duration
        self.render_length = self.duration * self.fps

    def setRenderFunc(self, input_func:Callable):
        self.input_func = input_func

    def setStartFunc(self, strt_func:Callable):
        self.strt_func = strt_func

    def addFBOPass(self, name: str, render_pass: Union[FBO, TileFBO, Geom2DFBO, Geom3DFBO, ParticlesFBO]):
        self.passes.append({
            "render_pass": render_pass,
            "name": name
        })

    def addVideo(self, path, name:str, id: int):
        self.videos.append({
            "video": Video(path),
            "name": name,
            "id": id
        })

    def getClipTimer(self, t):
        frame_count = int(round(t * self.fps))
        et = frame_count / (self.render_length - 1)
        et = max(0, min(1, et))
        return et

    def render_(self, timer):
        frames = []
        for vid in self.videos:
            img = vid["video"].get_frame_at_time(timer * self.duration)
            if img is not None:
                frames.append({
                    "frame": img,
                    "name": vid["name"],
                    "id": vid["id"]
                })

        
        self.t = timer
        loop_timer = 1-abs(2*timer-1)
        if callable(self.input_func):
            self.input_func(self, timer)
        for i in range(len(self.passes)):
            self.passes[i]["render_pass"].set_uniform("duration", self.duration)
            self.passes[i]["render_pass"].set_uniform("timer", timer)
            self.passes[i]["render_pass"].set_uniform("loop_timer", loop_timer)
            for frm in frames:
                self.passes[i]["render_pass"].release(frm["name"])
                self.passes[i]["render_pass"].set_texture_uniform(
                    
                    pil_to_texture(self.passes[i]["render_pass"].ctx, frm["frame"]),
                    frm["name"],
                    frm["id"],
                    True
                )
            self.passes[i]["render_pass"].render()
               
    
    def render_frame(self, t) -> np.ndarray:
        if self.rest_time > 0.0:
            tm.sleep(self.rest_time)

        timer = self.getClipTimer(t)
        self.render_(timer)

        frame = self.passes[len(self.passes)-1]["render_pass"].extract_np_img()

        if self.should_save_frames:
            frame_num = round(t * self.fps)
            imageio.imwrite(self.frames_folder.joinpath(f"{frame_num:05d}.jpg"), frame)
        
        return frame
    
    def render_frame_sample(self, t, iterative=False):
        if iterative:
            timer = self.getClipTimer(t)
            self.t = timer
            loop_timer = 1-abs(2*timer-1)
            stps = int(timer * self.duration * self.fps)
            for stp in range(stps):
                timer = stp / (self.duration * self.fps - 1)
                self.render_(timer)
        else:
            timer = self.getClipTimer(t)
            self.render_(timer)

    def render(self, should_save_frame = False):
        self.should_save_frames = should_save_frame
        clip = moviepy.VideoClip(self.render_frame, duration=self.duration)
        return clip

    def render_pyav(self, path = "output.mp4", should_save_frame = False):
        self.should_save_frames = should_save_frame

        # need first frame to get resolution
        frame = self.render_frame(0)

        height, width = frame.shape[:2]

        container = av.open(str(path), mode="w")

        stream = container.add_stream(
            "libx264",
            rate=self.fps
        )

        stream.width = width
        stream.height = height
        stream.pix_fmt = "yuv420p"

        # First frame
        video_frame = av.VideoFrame.from_ndarray(
            frame,
            format="rgb24"
        )

        for packet in stream.encode(video_frame):
            container.mux(packet)

        # Remaining frames
        for i in range(1, self.render_length):
            t = i / self.fps

            frame = self.render_frame(t)

            video_frame = av.VideoFrame.from_ndarray(
                frame,
                format="rgb24"
            )

            progress_bar(100 * (i+1)/self.render_length, "video rendering")
            for packet in stream.encode(video_frame):
                container.mux(packet)

        # Flush encoder
        for packet in stream.encode():
            container.mux(packet)

        container.close()

    def extractImage(self, path, format='png', quality=100):
        if len(self.passes) > 0:
            self.passes[len(self.passes)-1]["render_pass"].extract_img(path, format, quality)

    def release(self):
        for i in range(len(self.passes)):
            self.passes[i]["render_pass"].release_all()

        for vid in self.videos:
            vid["video"].close()
    
class ClipMerger:
    def __init__(self):
        """
        Single or Multiple videos merged into one
        """
        self.clips = []
        self.audio = None
        self.fps = 0
        self.duration = 0

    def addClip(self, clip:ClipRenderer):
        self.clips.append(clip)
        self.duration += clip.duration
        self.fps = max(self.fps, clip.fps)

    def addAudio(self, path:str):
        self.audio = moviepy.AudioFileClip(path)
    
    def renderClips(self, path:str, tmp_folder:Path, audio_fade=0.1, ffmpeg_params=[]):
        for i in range(len(self.clips)):
            if callable(self.clips[i].strt_func):
                self.clips[i].strt_func(self.clips[i])
            vid_clip = self.clips[i].render()
            vid_clip.write_videofile(str(tmp_folder.joinpath(f'{i}_tmp.mp4')), fps=self.clips[i].fps)
            vid_clip.close()
            
        
        self.masterClips(path, tmp_folder, audio_fade, ffmpeg_params=ffmpeg_params)

    def masterClips(self, path:str, tmp_folder:Path, audio_fade=0.1, ffmpeg_params=[]):
        _clips = []
        for i in range(len(self.clips)):
            vid_file = moviepy.VideoFileClip(str(tmp_folder.joinpath(f'{i}_tmp.mp4')))
            _clips.append(vid_file)

        final_vid = moviepy.concatenate_videoclips(_clips)
        
        if self.audio is not None:
            self.audio = self.audio.subclipped(0, min(self.audio.duration,final_vid.duration))
            final_vid = final_vid.with_audio(self.audio)
            final_vid = final_vid.with_effects([moviepy.afx.AudioFadeOut(audio_fade), moviepy.afx.AudioFadeIn(audio_fade)])
            final_vid.write_videofile(path, fps=self.fps, audio_codec="aac", ffmpeg_params=ffmpeg_params)
        else:
            final_vid.write_videofile(path, fps=self.fps, ffmpeg_params=ffmpeg_params)

        for i in range(len(_clips)):
            _clips[i].close()
            os.remove(str(tmp_folder.joinpath(f'{i}_tmp.mp4')))
    
    def release(self):
        for clip in self.clips:
            clip.release()


def AddAudioToVideo(out_path:str='', clip_path:str='', audio_path:str='', audio_fade = 0.1, ffmpeg_params=[], audio_scale = 1.0):
    clip = moviepy.VideoFileClip(clip_path)
    audio = moviepy.AudioFileClip(audio_path)

    audio = audio.subclipped(0, min(audio.duration, clip.duration))
    audio = audio.with_volume_scaled(audio_scale)
    final_vid = clip.with_audio(audio)
    final_vid = final_vid.with_effects([moviepy.afx.AudioFadeOut(audio_fade), moviepy.afx.AudioFadeIn(audio_fade)])
    final_vid.write_videofile(out_path, fps=clip.fps, audio_codec="aac", ffmpeg_params=ffmpeg_params)