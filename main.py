import aiohttp
from pathlib import Path

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api import logger
from astrbot.api import AstrBotConfig

PLUGIN_NAME = "astrbot_plugin_mc_skin"

UAPIPRO_API_URL = "https://uapis.cn/api/v1/game/minecraft/userinfo"

TEMPLATE_3D = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    background: #FFFFFF;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
    padding: 16px;
}
.row {
    display: flex;
    gap: 12px;
    justify-content: center;
    align-items: flex-start;
}
.view-wrapper {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
}
.view-wrapper canvas {
    width: {{ cell_w }}px;
    height: {{ cell_h }}px;
    display: block;
}
.view-label {
    font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
    font-size: 16px;
    color: #999;
    user-select: none;
}
.player-name-wrapper {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
}
.player-name-wrapper canvas {
    width: {{ cell_w }}px;
    height: {{ cell_h }}px;
    display: block;
}
.player-name-label {
    font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
    font-size: 16px;
    color: #999;
    user-select: none;
}
.player-id {
    font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
    font-size: 28px;
    font-weight: 900;
    color: #222;
    user-select: none;
    text-align: center;
    text-shadow:
        -1px -1px 0 #fff,
         1px -1px 0 #fff,
        -1px  1px 0 #fff,
         1px  1px 0 #fff,
        -2px -2px 0 #fff,
         2px -2px 0 #fff,
        -2px  2px 0 #fff,
         2px  2px 0 #fff;
}
.spacer {
    width: {{ cell_w }}px;
    height: 0;
}
</style>
</head>
<body>
<div class="row">
    {% for view in top_row %}
        {% if view.show_player_id %}
        <div class="player-name-wrapper">
            <canvas class="view-canvas" data-angle-y="{{ view.angle_y }}" data-angle-x="{{ view.angle_x }}"></canvas>
            <span class="player-name-label">{{ view.label }}</span>
        </div>
        {% else %}
        <div class="view-wrapper">
            <canvas class="view-canvas" data-angle-y="{{ view.angle_y }}" data-angle-x="{{ view.angle_x }}"></canvas>
            <span class="view-label">{{ view.label }}</span>
        </div>
        {% endif %}
    {% endfor %}
</div>
<div class="row" style="align-items: center;">
    {% for view in bottom_row %}
    <div class="view-wrapper">
        <canvas class="view-canvas" data-angle-y="{{ view.angle_y }}" data-angle-x="{{ view.angle_x }}"></canvas>
        <span class="view-label">{{ view.label }}</span>
    </div>
    {% endfor %}
    {% if show_player_name %}
    <div style="display: flex; align-items: center; width: {{ cell_w }}px; justify-content: center;">
        <span class="player-id">{{ player_name }}</span>
    </div>
    {% endif %}
</div>

<script type="importmap">
{
  "imports": {
    "three": "https://unpkg.com/three@0.160.0/build/three.module.js",
    "three/addons/": "https://unpkg.com/three@0.160.0/examples/jsm/"
  }
}
</script>
<script type="module">
import * as THREE from 'three';

const SKIN_URL = "{{ skin_url }}";
const CELL_W = {{ cell_w }};
const CELL_H = {{ cell_h }};

function createMaterial(ux, uy, uw, uh, img, flipH) {
    const c = document.createElement('canvas');
    c.width = uw;
    c.height = uh;
    const ctx = c.getContext('2d');
    if (flipH) { ctx.translate(uw, 0); ctx.scale(-1, 1); }
    ctx.drawImage(img, ux, uy, uw, uh, 0, 0, uw, uh);
    const tex = new THREE.CanvasTexture(c);
    tex.magFilter = THREE.NearestFilter;
    tex.minFilter = THREE.NearestFilter;
    tex.colorSpace = THREE.SRGBColorSpace;
    return new THREE.MeshLambertMaterial({ map: tex, transparent: true, alphaTest: 0.05 });
}

function buildModel(img) {
    const g = new THREE.Group();
    const s = 2;

    const headGeo = new THREE.BoxGeometry(8*s, 8*s, 8*s);
    const headMats = [
        createMaterial(0,8,8,8,img,false), createMaterial(16,8,8,8,img,true),
        createMaterial(8,0,8,8,img,false), createMaterial(16,0,8,8,img,false),
        createMaterial(8,8,8,8,img,false), createMaterial(24,8,8,8,img,true),
    ];
    const head = new THREE.Mesh(headGeo, headMats);
    head.position.y = 28 * s; g.add(head);

    const hatGeo = new THREE.BoxGeometry(8.5*s, 8.5*s, 8.5*s);
    const hatMats = [
        createMaterial(32,8,8,8,img,false), createMaterial(48,8,8,8,img,true),
        createMaterial(40,0,8,8,img,false), createMaterial(48,0,8,8,img,false),
        createMaterial(40,8,8,8,img,false), createMaterial(56,8,8,8,img,true),
    ];
    const hat = new THREE.Mesh(hatGeo, hatMats);
    hat.position.copy(head.position); g.add(hat);

    const bodyGeo = new THREE.BoxGeometry(8*s, 12*s, 4*s);
    const bodyMats = [
        createMaterial(16,20,4,12,img,false), createMaterial(28,20,4,12,img,true),
        createMaterial(20,16,8,4,img,false), createMaterial(28,16,8,4,img,false),
        createMaterial(20,20,8,12,img,false), createMaterial(32,20,8,12,img,true),
    ];
    const body = new THREE.Mesh(bodyGeo, bodyMats);
    body.position.y = 18 * s; g.add(body);

    const bodyHatGeo = new THREE.BoxGeometry(8.5*s, 12.6*s, 4.5*s);
    const bodyHatMats = [
        createMaterial(16,36,4,12,img,false), createMaterial(28,36,4,12,img,true),
        createMaterial(20,32,8,4,img,false), createMaterial(28,32,8,4,img,false),
        createMaterial(20,36,8,12,img,false), createMaterial(32,36,8,12,img,true),
    ];
    const bodyHat = new THREE.Mesh(bodyHatGeo, bodyHatMats);
    bodyHat.position.copy(body.position); g.add(bodyHat);

    const armGeo = new THREE.BoxGeometry(4*s, 12*s, 4*s);
    const armRMats = [
        createMaterial(40,20,4,12,img,false), createMaterial(48,20,4,12,img,true),
        createMaterial(44,16,4,4,img,false), createMaterial(48,16,4,4,img,false),
        createMaterial(44,20,4,12,img,false), createMaterial(52,20,4,12,img,true),
    ];
    const armR = new THREE.Mesh(armGeo, armRMats);
    armR.position.set(-6*s, 18*s, 0); g.add(armR);

    const armRHatGeo = new THREE.BoxGeometry(4.5*s, 12.6*s, 4.5*s);
    const armRHatMats = [
        createMaterial(40,36,4,12,img,false), createMaterial(48,36,4,12,img,true),
        createMaterial(44,32,4,4,img,false), createMaterial(48,32,4,4,img,false),
        createMaterial(44,36,4,12,img,false), createMaterial(52,36,4,12,img,true),
    ];
    const armRHat = new THREE.Mesh(armRHatGeo, armRHatMats);
    armRHat.position.copy(armR.position); g.add(armRHat);

    const armLMats = [
        createMaterial(32,52,4,12,img,false), createMaterial(40,52,4,12,img,true),
        createMaterial(36,48,4,4,img,false), createMaterial(40,48,4,4,img,false),
        createMaterial(36,52,4,12,img,false), createMaterial(44,52,4,12,img,true),
    ];
    const armL = new THREE.Mesh(armGeo, armLMats);
    armL.position.set(6*s, 18*s, 0); g.add(armL);

    const armLHatGeo = new THREE.BoxGeometry(4.5*s, 12.6*s, 4.5*s);
    const armLHatMats = [
        createMaterial(48,52,4,12,img,false), createMaterial(56,52,4,12,img,true),
        createMaterial(52,48,4,4,img,false), createMaterial(56,48,4,4,img,false),
        createMaterial(52,52,4,12,img,false), createMaterial(60,52,4,12,img,true),
    ];
    const armLHat = new THREE.Mesh(armLHatGeo, armLHatMats);
    armLHat.position.copy(armL.position); g.add(armLHat);

    const legGeo = new THREE.BoxGeometry(4*s, 12*s, 4*s);
    const legRMats = [
        createMaterial(0,20,4,12,img,false), createMaterial(8,20,4,12,img,true),
        createMaterial(4,16,4,4,img,false), createMaterial(8,16,4,4,img,false),
        createMaterial(4,20,4,12,img,false), createMaterial(12,20,4,12,img,true),
    ];
    const legR = new THREE.Mesh(legGeo, legRMats);
    legR.position.set(-2*s, 6*s, 0); g.add(legR);

    const legRHatGeo = new THREE.BoxGeometry(4.5*s, 12.6*s, 4.5*s);
    const legRHatMats = [
        createMaterial(0,36,4,12,img,false), createMaterial(8,36,4,12,img,true),
        createMaterial(4,32,4,4,img,false), createMaterial(8,32,4,4,img,false),
        createMaterial(4,36,4,12,img,false), createMaterial(12,36,4,12,img,true),
    ];
    const legRHat = new THREE.Mesh(legRHatGeo, legRHatMats);
    legRHat.position.copy(legR.position); g.add(legRHat);

    const legLMats = [
        createMaterial(16,52,4,12,img,false), createMaterial(24,52,4,12,img,true),
        createMaterial(20,48,4,4,img,false), createMaterial(24,48,4,4,img,false),
        createMaterial(20,52,4,12,img,false), createMaterial(28,52,4,12,img,true),
    ];
    const legL = new THREE.Mesh(legGeo, legLMats);
    legL.position.set(2*s, 6*s, 0); g.add(legL);

    const legLHatGeo = new THREE.BoxGeometry(4.5*s, 12.6*s, 4.5*s);
    const legLHatMats = [
        createMaterial(0,52,4,12,img,false), createMaterial(8,52,4,12,img,true),
        createMaterial(4,48,4,4,img,false), createMaterial(8,48,4,4,img,false),
        createMaterial(4,52,4,12,img,false), createMaterial(12,52,4,12,img,true),
    ];
    const legLHat = new THREE.Mesh(legLHatGeo, legLHatMats);
    legLHat.position.copy(legL.position); g.add(legLHat);

    return g;
}

function renderView(canvas, model, angleY, angleX) {
    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false, preserveDrawingBuffer: true });
    renderer.setPixelRatio(2);
    renderer.setSize(CELL_W, CELL_H);
    renderer.setClearColor(0xffffff, 1);

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xffffff);
    scene.add(new THREE.AmbientLight(0xffffff, 0.85));
    const dl = new THREE.DirectionalLight(0xffffff, 0.9);
    dl.position.set(10, 25, 15);
    scene.add(dl);
    const bl = new THREE.DirectionalLight(0xffffff, 0.35);
    bl.position.set(-5, 10, -10);
    scene.add(bl);

    const clone = model.clone(true);
    scene.add(clone);

    const box = new THREE.Box3().setFromObject(clone);
    const center = box.getCenter(new THREE.Vector3());
    const bSize = box.getSize(new THREE.Vector3());
    const maxDim = Math.max(bSize.x, bSize.y, bSize.z);
    const half = maxDim * 0.65;

    const cam = new THREE.OrthographicCamera(-half, half, half, -half, 0.1, 300);
    const ay = THREE.MathUtils.degToRad(angleY);
    const ax = THREE.MathUtils.degToRad(angleX);
    const dist = maxDim * 1.8;

    cam.position.x = Math.sin(ay) * Math.cos(ax) * dist + center.x;
    cam.position.y = Math.sin(ax) * dist + center.y;
    cam.position.z = Math.cos(ay) * Math.cos(ax) * dist + center.z;
    cam.lookAt(center.x, center.y, center.z);
    cam.updateProjectionMatrix();

    renderer.render(scene, cam);
}

const img = new Image();
img.crossOrigin = "anonymous";
img.onload = () => {
    const model = buildModel(img);
    document.querySelectorAll('.view-canvas').forEach(c => {
        renderView(c, model, parseFloat(c.dataset.angleY), parseFloat(c.dataset.angleX));
    });
    setTimeout(() => document.body.setAttribute("data-rendered", "true"), 500);
};
img.onerror = () => {
    document.body.innerHTML = '<div style="color:red;padding:20px;">加载失败</div>';
    document.body.setAttribute("data-rendered", "true");
};
img.src = SKIN_URL;
</script>
</body>
</html>'''


class SkinPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config

    async def _get_player_info(self, username: str) -> dict | None:
        params = {"username": username}
        headers = {}
        api_key = self.config.get("api_key", "")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    UAPIPRO_API_URL, params=params, headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    elif resp.status == 404:
                        return None
                    else:
                        logger.error(f"UApiPro error {resp.status}: {await resp.text()}")
                        return None
        except Exception as e:
            logger.error(f"UApiPro request failed for {username}: {e}")
            return None

    @filter.command("skin")
    async def skin(self, event: AstrMessageEvent, username: str):
        '''查询 Minecraft 正版玩家皮肤并渲染为多视角 3D 图片。

        Args:
            username(string): Minecraft 正版玩家 ID
        '''
        if not username:
            yield event.plain_result("请提供 Minecraft 玩家 ID，例如：/skin Notch")
            return

        yield event.plain_result(f"🔍 正在查询 {username} 的皮肤...")

        player_info = await self._get_player_info(username)
        if not player_info:
            yield event.plain_result(f"❌ 未找到正版玩家 {username}，请检查 ID 是否正确。")
            return

        skin_url = player_info.get("skin_url")
        resolved_name = player_info.get("username", username)
        if not skin_url:
            yield event.plain_result(f"❌ {resolved_name} 没有设置皮肤。")
            return

        cell_w = self.config.get("cell_w", 400)
        cell_h = self.config.get("cell_h", 550)

        angle_iso = self.config.get("angle_iso", 25)
        angle_front = self.config.get("angle_front", 0)
        angle_right = self.config.get("angle_right", 0)
        angle_back = self.config.get("angle_back", 0)
        angle_left = self.config.get("angle_left", 0)

        show_isometric = self.config.get("render_isometric", True)
        show_front = self.config.get("render_front", True)
        show_right = self.config.get("render_right", True)
        show_back = self.config.get("render_back", True)
        show_left = self.config.get("render_left", True)

        top_row = []
        if show_front:
            top_row.append({"angle_y": 0, "angle_x": angle_front, "label": "正面", "show_player_id": False})
        if show_back:
            top_row.append({"angle_y": 180, "angle_x": angle_back, "label": "背面", "show_player_id": False})
        if show_isometric:
            top_row.append({"angle_y": 30, "angle_x": angle_iso, "label": "3D 视角", "show_player_id": True})

        bottom_row = []
        if show_left:
            bottom_row.append({"angle_y": 270, "angle_x": angle_left, "label": "左侧"})
        if show_right:
            bottom_row.append({"angle_y": 90, "angle_x": angle_right, "label": "右侧"})

        show_player_name = len(top_row) == 3 and len(bottom_row) == 2

        if not top_row:
            top_row.append({"angle_y": 30, "angle_x": 25, "label": "默认", "show_player_id": True})

        try:
            url = await self.html_render(
                TEMPLATE_3D,
                {
                    "skin_url": skin_url,
                    "player_name": resolved_name,
                    "top_row": top_row,
                    "bottom_row": bottom_row,
                    "show_player_name": show_player_name,
                    "cell_w": cell_w,
                    "cell_h": cell_h,
                },
                options={
                    "type": "png",
                    "omit_background": False,
                    "full_page": True,
                    "timeout": 30000,
                },
            )
            yield event.image_result(url)
        except Exception as e:
            logger.error(f"Render error: {e}", exc_info=True)
            yield event.plain_result(f"❌ 皮肤渲染失败: {str(e)}")

    async def terminate(self):
        pass