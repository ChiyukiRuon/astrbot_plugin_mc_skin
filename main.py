import asyncio
import base64
from pathlib import Path
import tempfile

import aiohttp

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api import logger
from astrbot.api import AstrBotConfig
from astrbot.api.message_components import Image

from .skin_renderer import render_skin_assets

PLUGIN_NAME = "astrbot_plugin_mc_skin"

UAPIPRO_API_URL = "https://uapis.cn/api/v1/game/minecraft/userinfo"

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

    @filter.command("mcskin")
    async def skin(self, event: AstrMessageEvent, username: str):
        '''查询 Minecraft 正版玩家皮肤并渲染为多视角 3D 图片。

        Args:
            username(string): Minecraft 正版玩家 ID
        '''
        if not username:
            yield event.plain_result("请提供 Minecraft 玩家 ID，例如：/mcskin Notch")
            return

        yield event.plain_result(f"正在查询 {username} 的皮肤...")

        player_info = await self._get_player_info(username)
        if not player_info:
            yield event.plain_result(f"未找到正版玩家 {username}，请检查 ID 是否正确。")
            return

        skin_url = player_info.get("skin_url")
        resolved_name = player_info.get("username", username)
        if not skin_url:
            yield event.plain_result(f"{resolved_name} 没有设置皮肤。")
            return

        try:
            skin_data = await self._download_skin(skin_url)
        except Exception as e:
            logger.error(f"Skin download error: {e}", exc_info=True)
            yield event.plain_result(f"皮肤下载失败：{e}")
            return

        async for result in self._render_skin(event, skin_data, resolved_name):
            yield result

    @filter.command("mcpreview")
    async def preview(self, event: AstrMessageEvent):
        '''预览随当前消息发送的第一张 Minecraft 皮肤贴图。'''
        skin_image = next(
            (part for part in event.get_messages() if isinstance(part, Image)),
            None,
        )
        if skin_image is None:
            yield event.plain_result(
                "请在发送 /mcpreview 的同一条消息中附带 PNG 皮肤贴图（64×32、64×64 或 128×128）。"
            )
            return

        yield event.plain_result("正在生成皮肤预览...")
        try:
            image_base64 = await asyncio.wait_for(
                skin_image.convert_to_base64(), timeout=15,
            )
            skin_data = base64.b64decode(image_base64, validate=True)
        except Exception as e:
            logger.error(f"Skin image read error: {e}", exc_info=True)
            yield event.plain_result("无法读取皮肤图片，请重新发送皮肤贴图原图后重试。")
            return

        async for result in self._render_skin(event, skin_data):
            yield result

    async def _download_skin(self, skin_url: str) -> bytes:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                skin_url, timeout=aiohttp.ClientTimeout(total=15),
            ) as response:
                response.raise_for_status()
                data = bytearray()
                async for chunk in response.content.iter_chunked(65536):
                    data.extend(chunk)
                    if len(data) > 2 * 1024 * 1024:
                        raise ValueError("皮肤文件大小超过 2 MB")
                return bytes(data)

    async def _render_skin(self, event: AstrMessageEvent, skin_data: bytes, resolved_name: str = ""):
        try:
            with tempfile.TemporaryDirectory(prefix="astrbot_mc_skin_") as temp_dir:
                preview_path, gif_path = await asyncio.to_thread(
                    render_skin_assets, skin_data, resolved_name, Path(temp_dir),
                )
                try:
                    await self._send_skin_images(event, preview_path, gif_path)
                except Exception as e:
                    logger.error(f"Skin image send error: {e}", exc_info=True)
                    yield event.plain_result(f"皮肤图片发送失败：{e}")
        except Exception as e:
            logger.error(f"Render error: {e}", exc_info=True)
            yield event.plain_result(f"皮肤渲染失败：{e}")

    async def _send_skin_images(self, event: AstrMessageEvent, preview_path: Path, gif_path: Path):
        try:
            await event.send(event.chain_result([
                Image.fromFileSystem(str(preview_path)),
                Image.fromFileSystem(str(gif_path)),
            ]))
            return
        except Exception as e:
            logger.warning(f"Combined skin image send failed, sending separately: {e}")

        failures = []
        for path in (preview_path, gif_path):
            try:
                await event.send(event.image_result(str(path)))
            except Exception as e:
                logger.error(f"Failed to send {path.name}: {e}", exc_info=True)
                failures.append(path.name)
        if failures:
            raise RuntimeError("无法发送 " + "、".join(failures))

    async def terminate(self):
        pass
