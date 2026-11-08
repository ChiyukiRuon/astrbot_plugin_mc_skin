# astrbot_plugin_mc_skin

🎮 **Minecraft 正版皮肤 3D 查询插件** —— 在聊天平台一键查询任意正版玩家的皮肤并渲染为多视角 3D 方块人图片。

---

## ✨ 功能

- `/skin <玩家ID>` 查询 Minecraft 正版玩家皮肤
- `/preview` 发送命令时附带皮肤图片即可预览
- **3D 渲染**：使用 Three.js 将皮肤贴图映射到方块人模型
- **五视图布局**：
  - 上排：正面 | 背面 | 3D 视角（下方显示玩家 ID）
  - 下排：左侧 | 右侧 | 玩家名
- 每个视图可**独立调节俯仰角**
- 正确叠加帽子层（第二层皮肤）
- 白色背景 + 玩家名描边
- 数据来源：**UApiPro** 免费 API

---

## 📥 安装

### 方式一：插件市场安装（推荐）

在 AstrBot WebUI → 插件管理 → 插件市场中搜索 `astrbot_plugin_mc_skin` 安装。

### 方式二：手动安装

1. 下载本插件压缩包并解压
2. 将 `astrbot_plugin_mc_skin` 文件夹放入 `AstrBot/data/plugins/` 目录
3. 在 AstrBot 使用的 Python 环境中，进入插件目录安装依赖：
   ```bash
   python -m pip install -r requirements.txt
   ```
4. 在 WebUI 插件管理中点击「重载插件」

已有用户更新后也需安装新增的 `Pillow` 依赖，再重载插件。Docker 部署请在 AstrBot 容器内安装依赖。

---

🚀 使用

```
/skin Notch
/skin Dream
/skin chemistryh2o
```

---

⚙️ 配置
```
配置项 类型 默认值 说明
api_key string (空) UApiPro API 密钥
cell_w int 400 视图宽度
cell_h int 550 视图高度
render_isometric bool true 3D 视角开关
angle_iso int 25 3D 视角俯仰角
render_front bool true 正面开关
angle_front int 0 正面俯仰角
render_back bool true 背面开关
angle_back int 0 背面俯仰角
render_left bool true 左侧开关
angle_left int 0 左侧俯仰角
render_right bool true 右侧开关
angle_right int 0 右侧俯仰角

```
---

🔧 技术细节

```
· Three.js 通过 CDN 加载，构建方块人模型
· 每个身体部位独立 UV 映射（头 8×8×8、身体 8×12×4、手臂 4×12×4、腿 4×12×4）
· 帽子层比基础层略大（8.5 vs 8），叠加显示
· 正交相机 + 包围盒自动适配画面
· 双环境光 + 方向光模拟 Minecraft 光照风格

```
---

📄 依赖

```
· AstrBot >= 4.9.2
· aiohttp — 异步 HTTP 请求
· Pillow — 读取、校验皮肤图片并转换为 PNG，用于皮肤预览
· 需要外网访问以加载 Three.js CDN

```
---

👤 作者

chemistryh2o

---

📜 许可证

MIT License
