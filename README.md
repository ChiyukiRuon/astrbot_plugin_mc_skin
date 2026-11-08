# astrbot_plugin_mc_skin

Minecraft 皮肤查询与图片预览插件。`ayaka` 分支使用本地 Pillow 渲染，输出四向视图 PNG 和旋转 GIF。

- `/mcskin <玩家ID>`：查询正版玩家皮肤并生成预览。
- `/mcpreview`：同一条消息附带皮肤贴图，预览第一张图片。
- 支持 64×32、64×64、128×128 的 PNG 皮肤，自动推测经典或纤细模型。

在 AstrBot 使用的 Python 环境中进入插件目录，执行 `python -m pip install -r requirements.txt` 安装 aiohttp 和 Pillow >= 10.0，再重载插件。Docker 部署需在 AstrBot 容器内安装依赖。

渲染实现移植自 [Tantless 提交的 PR #2](https://github.com/cmtho/astrbot_plugin_mc_skin/pull/2)，基于提交 `b8dbf64e02e02de4511df0b5372b397741b3cf16`。

原作者：chemistryh2o。许可证：MIT。
