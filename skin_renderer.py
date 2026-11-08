"""Render Minecraft skins as a four-view montage and a turntable GIF."""

# Adapted from Tantless's renderer in cmtho/astrbot_plugin_mc_skin#2,
# commit b8dbf64e02e02de4511df0b5372b397741b3cf16.

from __future__ import annotations

from io import BytesIO
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


PARTS = {
    "head": {"size": (8, 8, 8), "base": (0, 0), "outer": (32, 0)},
    "torso": {"size": (8, 12, 4), "base": (16, 16), "outer": (16, 32)},
    "right_arm": {"size": (4, 12, 4), "base": (40, 16), "outer": (40, 32)},
    "right_leg": {"size": (4, 12, 4), "base": (0, 16), "outer": (0, 32)},
    "left_leg": {"size": (4, 12, 4), "base": (16, 48), "outer": (0, 48)},
    "left_arm": {"size": (4, 12, 4), "base": (32, 48), "outer": (48, 48)},
}

FACE_ORDER = ("top", "bottom", "right", "front", "left", "back")

NORMALS = {
    "front": (0, 0, 1),
    "back": (0, 0, -1),
    "right": (-1, 0, 0),
    "left": (1, 0, 0),
    "top": (0, 1, 0),
    "bottom": (0, -1, 0),
}


def _load_skin(data: bytes) -> Image.Image:
    image = Image.open(BytesIO(data))
    if image.format != "PNG":
        raise ValueError("皮肤文件不是 PNG 格式")
    if image.size not in ((64, 32), (64, 64), (128, 128)):
        raise ValueError(f"不支持的皮肤尺寸：{image.width}×{image.height}")
    return image.convert("RGBA")


def _logical_scale(image: Image.Image) -> int:
    return 2 if image.size == (128, 128) else 1


def _is_legacy(image: Image.Image) -> bool:
    return image.size == (64, 32)


def _infer_model(image: Image.Image) -> str:
    if _is_legacy(image):
        return "classic"
    scale = _logical_scale(image)
    probes = (
        (54, 20, 56, 32),
        (54, 36, 56, 48),
        (46, 52, 48, 64),
        (62, 52, 64, 64),
    )
    alpha = image.getchannel("A")
    for box in probes:
        scaled = tuple(value * scale for value in box)
        if any(value > 0 for value in alpha.crop(scaled).getdata()):
            return "classic"
    return "slim"


def _arm_width(model: str) -> int:
    return 3 if model == "slim" else 4


def _part_size(part: str, model: str) -> tuple[int, int, int]:
    width, height, depth = PARTS[part]["size"]
    if part.endswith("_arm"):
        width = _arm_width(model)
    return width, height, depth


def _face_rects(uv: tuple[int, int], size: tuple[int, int, int], scale: int):
    u, v = uv
    width, height, depth = size
    u *= scale
    v *= scale
    width *= scale
    height *= scale
    depth *= scale
    return {
        "top": (u + depth, v, u + depth + width, v + depth),
        "bottom": (u + depth + width, v, u + depth + 2 * width, v + depth),
        "right": (u, v + depth, u + depth, v + depth + height),
        "front": (u + depth, v + depth, u + depth + width, v + depth + height),
        "left": (u + depth + width, v + depth, u + depth + width + depth, v + depth + height),
        "back": (
            u + 2 * depth + width,
            v + depth,
            u + 2 * depth + 2 * width,
            v + depth + height,
        ),
    }


def _world_boxes(model: str):
    arm_width = _arm_width(model)
    return {
        "head": (-4, 4, 24, 32, -4, 4),
        "torso": (-4, 4, 12, 24, -2, 2),
        "right_arm": (-4 - arm_width, -4, 12, 24, -2, 2),
        "left_arm": (4, 4 + arm_width, 12, 24, -2, 2),
        "right_leg": (-4, 0, 0, 12, -2, 2),
        "left_leg": (0, 4, 0, 12, -2, 2),
    }


def _face_corners(box, face: str):
    x0, x1, y0, y1, z0, z1 = box
    return {
        "front": ((x0, y1, z1), (x1, y1, z1), (x1, y0, z1), (x0, y0, z1)),
        "back": ((x1, y1, z0), (x0, y1, z0), (x0, y0, z0), (x1, y0, z0)),
        "right": ((x0, y1, z0), (x0, y1, z1), (x0, y0, z1), (x0, y0, z0)),
        "left": ((x1, y1, z1), (x1, y1, z0), (x1, y0, z0), (x1, y0, z1)),
        "top": ((x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)),
        "bottom": ((x0, y0, z1), (x1, y0, z1), (x1, y0, z0), (x0, y0, z0)),
    }[face]


def _lerp_point(start, end, amount):
    return tuple(a + (b - a) * amount for a, b in zip(start, end))


def _quad_pixel(corners, x, y, width, height):
    top_left, top_right, bottom_right, bottom_left = corners
    u0, u1 = x / width, (x + 1) / width
    v0, v1 = y / height, (y + 1) / height

    def point(u, v):
        top = _lerp_point(top_left, top_right, u)
        bottom = _lerp_point(bottom_left, bottom_right, u)
        return _lerp_point(top, bottom, v)

    return point(u0, v0), point(u1, v0), point(u1, v1), point(u0, v1)


def _shade(color, normal, outer: bool):
    light = (-0.35, 0.75, 0.85)
    length = math.sqrt(sum(value * value for value in light))
    light = tuple(value / length for value in light)
    diffuse = max(0.0, sum(a * b for a, b in zip(normal, light)))
    factor = 0.63 + 0.37 * diffuse
    if outer:
        factor = min(1.0, factor + 0.035)
    red, green, blue, alpha = color
    return round(red * factor), round(green * factor), round(blue * factor), alpha


def _source_for(image: Image.Image, part: str, layer: str):
    if not _is_legacy(image):
        return part, False
    if part == "left_arm" and layer == "base":
        return "right_arm", True
    if part == "left_leg" and layer == "base":
        return "right_leg", True
    if part in ("head", "torso", "right_arm", "right_leg"):
        if layer == "base" or (part == "head" and layer == "outer"):
            return part, False
    return None, False


def _textured_quads(image: Image.Image, model: str):
    scale = _logical_scale(image)
    quads = []
    for part, base_box in _world_boxes(model).items():
        for layer in ("base", "outer"):
            source, mirrored = _source_for(image, part, layer)
            if source is None:
                continue
            size = _part_size(source, model)
            rectangles = _face_rects(PARTS[source][layer], size, scale)
            inflate = 0.0 if layer == "base" else (0.5 if part == "head" else 0.25)
            x0, x1, y0, y1, z0, z1 = base_box
            box = (
                x0 - inflate,
                x1 + inflate,
                y0 - inflate,
                y1 + inflate,
                z0 - inflate,
                z1 + inflate,
            )
            for face in FACE_ORDER:
                patch = image.crop(rectangles[face])
                if mirrored:
                    patch = patch.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                corners = _face_corners(box, face)
                for y in range(patch.height):
                    for x in range(patch.width):
                        color = patch.getpixel((x, y))
                        if color[3] == 0:
                            continue
                        quad = _quad_pixel(corners, x, y, patch.width, patch.height)
                        quads.append((quad, _shade(color, NORMALS[face], layer == "outer")))
    return quads


def _project(point, yaw_degrees: float, elevation_degrees: float):
    x, y, z = point
    yaw = math.radians(yaw_degrees)
    elevation = math.radians(elevation_degrees)
    cos_yaw, sin_yaw = math.cos(yaw), math.sin(yaw)
    cos_elevation, sin_elevation = math.cos(elevation), math.sin(elevation)
    horizontal = cos_yaw * x - sin_yaw * z
    forward = sin_yaw * x + cos_yaw * z
    up = cos_elevation * y - sin_elevation * forward
    depth = cos_elevation * forward + sin_elevation * y
    return horizontal, -up, depth


def _mix(start, end, amount):
    return tuple(round(a + (b - a) * amount) for a, b in zip(start, end))


def _gradient_background(size: tuple[int, int]):
    width, height = size
    image = Image.new("RGBA", size)
    draw = ImageDraw.Draw(image)
    top = (244, 247, 252, 255)
    bottom = (215, 224, 238, 255)
    for y in range(height):
        draw.line((0, y, width, y), fill=_mix(top, bottom, y / max(1, height - 1)))
    return image


def _font(size: int):
    candidates = (
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/msyhbd.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    )
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def _draw_centered_text(draw, text, y, width, chosen_font, color):
    box = draw.textbbox((0, 0), text, font=chosen_font)
    text_width = box[2] - box[0]
    draw.text(((width - text_width) / 2, y), text, font=chosen_font, fill=color)


def _render_view(
    image: Image.Image,
    model: str,
    yaw: float,
    size: tuple[int, int],
    label: str,
    subtitle: str | None,
    show_shadow: bool = True,
    show_caption: bool = True,
):
    canvas = _gradient_background(size)
    width, height = size
    projected = []
    for quad, color in _textured_quads(image, model):
        points = [_project(point, yaw, 12) for point in quad]
        depth = sum(point[2] for point in points) / 4
        projected.append((depth, points, color))

    all_points = [point for _, points, _ in projected for point in points]
    if not all_points:
        raise ValueError("皮肤图片完全透明，无法生成预览")
    min_x = min(point[0] for point in all_points)
    max_x = max(point[0] for point in all_points)
    min_y = min(point[1] for point in all_points)
    max_y = max(point[1] for point in all_points)
    drawing_height = height - (86 if show_caption else 42)
    scale = min((width - 74) / (max_x - min_x), (drawing_height - 48) / (max_y - min_y))
    offset_x = width / 2 - (min_x + max_x) * scale / 2
    offset_y = 25 - min_y * scale

    def screen(point):
        return round(point[0] * scale + offset_x), round(point[1] * scale + offset_y)

    draw = ImageDraw.Draw(canvas, "RGBA")
    if show_shadow:
        feet = [_project((x, 0, z), yaw, 12) for x in (-4.5, 4.5) for z in (-2.5, 2.5)]
        shadow_x = [screen(point)[0] for point in feet]
        shadow_y = [screen(point)[1] for point in feet]
        baseline = max(shadow_y) + 10
        draw.ellipse(
            (min(shadow_x) - 20, baseline - 12, max(shadow_x) + 20, baseline + 13),
            fill=(25, 40, 70, 36),
        )
    for _, points, color in sorted(projected, key=lambda item: item[0]):
        draw.polygon([screen(point) for point in points], fill=color)

    if show_caption:
        card_top = height - (68 if subtitle else 62)
        draw.rounded_rectangle((18, card_top, width - 18, height - 16), radius=15, fill=(255, 255, 255, 218))
        if subtitle:
            _draw_centered_text(draw, label, height - 62, width, _font(24), (24, 33, 52, 255))
            _draw_centered_text(draw, subtitle, height - 35, width, _font(14), (87, 99, 122, 255))
        else:
            _draw_centered_text(draw, label, height - 54, width, _font(24), (24, 33, 52, 255))
    return canvas.convert("RGB")


def render_skin_assets(
    skin_data: bytes,
    player_name: str,
    output_dir: str | Path,
    frames: int = 24,
):
    image = _load_skin(skin_data)
    model = _infer_model(image)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    preview_path = output_dir / "skin-four-views.png"
    gif_path = output_dir / "skin-turntable.gif"

    tile_size = (440, 540)
    margin = 18
    montage = Image.new(
        "RGB",
        (tile_size[0] * 2 + margin * 3, tile_size[1] * 2 + margin * 3),
        (226, 233, 243),
    )
    model_name = "纤细模型" if model == "slim" else "经典模型"
    subtitle = f"{model_name}｜基础层 + 外层"
    views = (
        (-28, "正面 · 左侧斜视"),
        (28, "正面 · 右侧斜视"),
        (152, "背面 · 左侧斜视"),
        (208, "背面 · 右侧斜视"),
    )
    for index, (yaw, label) in enumerate(views):
        tile = _render_view(
            image,
            model,
            yaw,
            tile_size,
            label,
            subtitle,
            show_shadow=False,
            show_caption=False,
        )
        x = margin + (index % 2) * (tile_size[0] + margin)
        y = margin + (index // 2) * (tile_size[1] + margin)
        montage.paste(tile, (x, y))
    montage.save(preview_path, optimize=True)

    animation = [
        _render_view(image, model, index * 360 / frames, tile_size, player_name, None)
        for index in range(frames)
    ]
    animation[0].save(
        gif_path,
        save_all=True,
        append_images=animation[1:],
        duration=85,
        loop=0,
        disposal=2,
        optimize=False,
    )
    return preview_path, gif_path

