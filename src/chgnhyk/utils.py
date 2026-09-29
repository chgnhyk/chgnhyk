import shutil
from pathlib import Path
from importlib import resources
from typing import Union

EXT_MAP = {
    "jpg": "jpeg",
    "jpeg": "jpeg",
    "png": "png",
    "tif": "tiff",
    "tiff": "tiff",
    "webp": "webp",
}

class FakeUniform:
    value = None

def progress_bar(progress: float, txt="progress"):
    # Get current terminal width
    term_width = shutil.get_terminal_size().columns
    
    # Leave room for percentage text
    margin = len(txt) + 7 + 6
    bar_width = max(margin, term_width - margin)
    
    filled = int((progress / 100) * bar_width)
    bar = "#" * filled + "-" * (bar_width - filled)
    
    print(f"\r[{bar}] {progress:.2f}% : {txt}", end="", flush=True)


shader_common = resources.files("chgnhyk.assets.shaders").joinpath("common.glsl").read_text(encoding="utf-8")

def get_asset_path(path:str, file:str):
    return str(resources.files(path).joinpath(file))

def load_shader(shader_path: Union[str, Path], common=True, common_path: Union[str, Path] = ''):
    scene_shader = ""

    open_target = shader_path
    if isinstance(shader_path, Path) == False:
        open_target = Path(shader_path)
    
    with open_target.open() as f:
        scene_shader = f.read()
    if common:
        if common_path != '':
            if isinstance(common_path, Path) == False:
                common_path = Path(common_path)
            with common_path.open() as ff:
                _common_shader = ff.read()
            scene_shader = scene_shader.replace("//####COMMON####", _common_shader)
        else:
            scene_shader = scene_shader.replace("//####COMMON####", shader_common)
    return scene_shader