# Package Name

Visual engine of Choi Gunhyuk

## Installation

Install the package from PyPI:

```bash
pip install chgnhyk
```

* Details: [chgnhyk installation doc](https://coffee-minute-695.notion.site/chgnhyk-Installation-Usage-3d63d4eb48e48056afa0e06a6a62abea)


ffmpeg 
- required to generate video with moviepy
- not required to when using `render_pyav()` function in `ClipRenderer`

csound 
libcsnd6-6.0v5 
- required to generate audio 

### Installation options
```bash
pip install chgnhyk[audio]
```
- requires csound

```bash
pip install chgnhyk[window]
```
- installs moderngl_window

```bash
pip install chgnhyk[mediapipe]
```
- installs mediapipe
- downgrades numpy to 1.26.4

```bash
pip install "chgnhyk[opencv]"
```
- install with opencv

```bash
pip install "chgnhyk[audio, window, mediapipe]"
```
- install with three options



## Usage

# Basic example 1:
- moviepy(ffmpeg needed) as video encoding backend
```python
from chgnhyk import FBO, ClipRenderer
from moderngl import create_context

CTX = create_context(require=(330), standalone=True)
SIZE = (1080, 1080)

shader = '''
#version 330
out vec4 outputColor;
in vec2 UV;

uniform sampler2D bckbuffer;
uniform vec2 resolution;

uniform float timer;
uniform float loop_timer;
uniform float duration;

void main() {
    vec2 uv = UV;
    vec2 rs = resolution;

    outputColor = vec4(uv, 1., 1.);
}
'''

scene = FBO(
    ctx = CTX, size = (1080, 1080), shader = shader
)

clip = ClipRenderer(duration=2, fps=30, rest_time=0.)
clip.addFBOPass("", scene)

clip.render_frame_sample(clip.duration * 0.0)
clip.extractImage((f"test_{clip.t}.jpg"))

vid = clip.render()
vid.write_videofile(str("test.mp4"), fps=clip.fps)

clip.release()
CTX.release()
```


# Basic example 2:
- pyav as video encoding backend
```python
from chgnhyk import FBO, ClipRenderer
from moderngl import create_context

CTX = create_context(require=(330), standalone=True)
SIZE = (1080, 1080)

shader = '''
#version 330
out vec4 outputColor;
in vec2 UV;

uniform sampler2D bckbuffer;
uniform vec2 resolution;

uniform float timer;
uniform float loop_timer;
uniform float duration;

void main() {
    vec2 uv = UV;
    vec2 rs = resolution;

    outputColor = vec4(uv, 1., 1.);
}
'''

scene = FBO(
    ctx = CTX, size = (1080, 1080), shader = shader
)

clip = ClipRenderer(duration=2, fps=30, rest_time=0.)
clip.addFBOPass("", scene)

clip.render_frame_sample(clip.duration * 0.0)
clip.extractImage((f"test_{clip.t}.jpg"))
clip.render_pyav("test.mp4")

clip.release()
CTX.release()
```


# Video example:
- create "sample" folder
- create "shaders" folder and put shader files there

shader file in "shaders" folder
```glsl
#version 330
out vec4 outputColor;
in vec2 UV;

uniform sampler2D bckbuffer;
uniform vec2 resolution;
uniform sampler2D VID;
uniform vec2 VID_res;

uniform float timer;
uniform float loop_timer;
uniform float duration;

#define PI 3.14159265

float rand(vec3 p){
    float sd1 = dot(p, vec3(31.3131,23.2323,17.1717));
    float sd2 = dot(p, vec3(13.1313,15.1515,19.1919));
    float sv = sin(sd1) + sin(sd2);
    return fract(sv * 45678.654321);
}

vec2 rotate(vec2 p, float a){
    return vec2(
        p.x * cos(a) - p.y * sin(a),
        p.x * sin(a) + p.y * cos(a)
    );
}

float sd_segment(vec2 p, vec2 a, vec2 b, float w){
    vec2 ba = b - a;
    vec2 pa = p - a;
    vec2 dr = normalize(ba);
    float l = length(ba);

    float dt = dot(pa, dr);
    vec2 h = a + dt * dr;

    float dst = length(h-p)-w;
    if(dt <= .0){
        dst = length(p-a)-w;
    }

    if(dt >= l){
        dst = length(p-b)-w;
    }

    return dst;
}

void main() {
    vec2 uv = UV;
    vec2 rs = resolution;
    uv = (uv-.5);
    uv *= rs/rs.y;

    vec2 sc = vec2(40.);
    
    vec2 iuv = floor(uv*sc);
    if(mod(iuv.y,2.) == .0){
        uv.x -= .5/sc.x;
    }
    iuv = floor(uv*sc);
    vec2 fuv = fract(uv*sc)-.5;
    vec2 vtc = (iuv/sc)*rs.y/rs + .5;
    vec4 vsamp = texture(VID, vtc);
    vec4 ovsamp = texture(VID, UV);

    float h = length(vsamp.rgb)/length(vec3(1.));
    h = floor(h * 8.)/8.;
    fuv = rotate(fuv, h * PI * 2.);
    float sh = sd_segment(fuv, vec2(-.4,.0), vec2(.4,.0), .02);
    sh = 1.-smoothstep(.0,.001 * sc.x,sh);

    vec3 col;
    col = mix(vsamp.rgb, vec3(.1,1.,.1), sh);
    outputColor = vec4(col, 1.);
}
```

main python script
```python
from chgnhyk import FBO, load_shader, ClipRenderer
from moderngl import create_context
from pathlib import Path

work_path = Path(__file__).parent
shader_path = work_path.joinpath("shaders/")
sample_path = work_path.joinpath("sample/")


CTX = create_context(require=(330), standalone=True)
ratio = 1
SIZE = (1080, 1080) # change to match video file

scene = FBO(ctx=CTX, size=SIZE, shader=load_shader(shader_path.joinpath("scene.glsl")))

clip = ClipRenderer(duration=5, fps=30, rest_time=0.) #8 #30
scene.set_uniform("duration", clip.duration)
clip.addFBOPass(name = 'scene', render_pass = scene)
clip.addVideo(sample_path.joinpath("video.mp4"), "VID", 8)

clip.render_frame_sample(clip.duration * 0.0)
clip.extractImage(sample_path.joinpath(f"test_{clip.t}.jpg"))

vid = clip.render()
vid.write_videofile(str(sample_path.joinpath("test.mp4")), fps=clip.fps)

clip.release()
CTX.release()
```


## Requirements

* Python 3.9 or later

## License

This project is licensed under the MIT License.

## Author

Choi Gunhyuk

## Links

* GitHub: https://github.com/hlp-pls/chgnhyk
