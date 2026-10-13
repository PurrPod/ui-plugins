<h1 align="center">PurrCat UI Plugin Market</h1>

<p align="center">
    专为 <a href="https://github.com/PurrPod/purrcat">PurrCat</a> 极简模式（web-minimal）构建的 UI 插件市场与注册表中心。
</p>

---

## 1. 简介

UI Plugin（UI 插件）是 PurrCat 极简模式宿主（`ui/web-minimal`）中的可视化插件。宿主是纯静态页面，插件以 `<iframe>` 形式挂载，按 `slot.area` 入驻到宿主的不同区域（`rail` / `sidebar` / `session` / `background` / `panel-container` / `panel` / `pet` / `popup`）。

每个 UI 插件都是一个独立文件夹，内含描述文件 `plugin.json` 与入口页面 `index.html`（资源建议全部内联，避免额外子目录）。下载安装后落入用户插件根 `~/.purrcat/webmin-plugins/`，宿主热插拔即时生效。

插件可在 `plugin.json` 中声明 `dependency`，声明为 skill / plugin / mcp / agentloop / sensor / graph 的依赖会在市场下载该插件时被自动一并安装。

---

## 2. 仓库架构设计

```text
ui-plugin/
├── .github/workflows/   # CI/CD 自动化构建流水线
├── scripts/             # 注册表构建与校验脚本
├── images/              # 插件展示图片（可选，供 registry 的 image 字段引用）
├── registry.json        # 全局注册表 (由 Action 自动生成)
├── README.md            # 说明文档与插件列表 (由 Action 自动更新)
│
└── plugins/             # 官方 UI 插件 (源码直接在本仓库维护)
    └── <plugin-name>/   # 每个插件一个独立文件夹
        ├── plugin.json  # 插件描述文件 (id / name / description / slot / entry / root / image / dependency / configSchema)
        └── index.html   # 插件入口页面（与 plugin.json 的 entry 对应）
```

---

## 3. 已收录 UI 插件清单

*(注：本列表由自动化流水线实时生成)*

<!-- PLUGINS:START -->
| 插件名 (Install ID) | 描述 | 图片 |
| :--- | :--- | :--- |
| `doodle-chat` | 手绘涂鸦风格的会话面板：照搬完整模式 ChatPage 的聊天框与消息气泡排版（用户气泡右对齐、助手气泡带头像标签、思考/工具气泡内联，底部为手写输入框与发送按钮）。 | — |
| `doodle-panel-shell` | 手绘涂鸦风格的面板容器（入驻 panel-container 区域）：顶部为涂鸦标签条（自动收纳全部 panel 区域插件），下方展台为每个面板插件各驻留一个独立 iframe（切换仅显隐、不重载），并负责把子插件与宿主之间的消息双向中继。 | — |
| `doodle-session-bar` | 手绘涂鸦风格的会话列表：把完整模式的「切换会话」列表与「待审批」列表合并成同一套涂鸦卡片风格，统一排版（会话卡片含行内重命名/删除，审批卡片含类型标签、理由展开、反馈与批准/拒绝）。 | — |
<!-- PLUGINS:END -->

---

## 4. 统一字段规范

每个插件的 `plugin.json` 必须包含以下字段（注册表条目由它派生）：

```json
{
  "id": "doodle-panel-shell",
  "name": "涂鸦面板容器",
  "description": "手绘涂鸦风格的面板容器……（中文，宿主设置面板展示）",
  "description-en": "Hand-drawn doodle panel container……（英文，市场展示）",
  "icon": "<svg …>（宿主侧栏/设置用图标）</svg>",
  "slot": { "area": "panel-container" },
  "entry": "index.html",
  "image": "",
  "root": "user",
  "dependency": [],
  "configSchema": [
    { "key": "show_desc", "label": "标签悬停显示说明", "type": "switch", "default": true }
  ]
}
```

### 字段解析

* **`id`** (必填): 安装标识，必须与文件夹名完全一致。
* **`name`** (必填): 插件显示名（宿主设置面板使用）。
* **`description`** (必填): 中文描述，用于宿主设置面板与市场中文展示。
* **`description-en`** (必填): 英文描述，注册表 `${description}` 与市场英文展示。
* **`icon`** (必填): 宿主侧栏 / 设置面板用图标（内联 SVG 字符串或内置图标名）。
* **`slot`** (必填): 插件入驻区域声明，本仓库统一为 `{ "area": "<区域>" }`。
* **`entry`** (必填): 插件入口文件（须真实存在于文件夹内）。
* **`image`** (可选): 展示图片位。为空串表示暂无图片；非空时可以是完整 URL，也可以是**仓库内相对路径**（如 `images/<name>.png`），构建脚本会自动补全为 raw 绝对 URL 写入注册表。
* **`root`** (必填): 期望放置位置，取值 `user` / `sandbox` / `builtin`。市场安装统一为 `user`（用户插件根）。
* **`dependency`** (必填): 依赖声明数组，元素形如 `{ "type": "<类型>", "id": "<安装标识>" }`；`type` 白名单为 `skill` / `plugin` / `mcp` / `agentloop` / `sensor` / `graph`。无依赖时为 `[]`。
* **`configSchema`** (可选): 插件可配置项声明（宿主设置面板据此渲染）。

### 命名一致性要求

**文件夹名 = `plugin.json` 的 `id`**

CI 构建时会自动校验。例如插件 `doodle-chat`：

```
plugins/doodle-chat/
├── plugin.json    # ✅ id: "doodle-chat"
└── index.html     # ✅ entry: "index.html"
```

---

## 5. 图片位与上传规范

* 展示图片统一放在仓库根目录的 `images/` 下，命名为 `<plugin-name>.png`（推荐 16:9 或 1:1）。
* 在 `plugin.json` 的 `image` 中填写相对路径 `images/<plugin-name>.png`，构建脚本会自动把它补全为
  `https://raw.githubusercontent.com/PurrPod/ui-plugin/main/images/<plugin-name>.png` 写入注册表条目。
* 暂时没有图片时保持 `image: ""` 即可，市场界面会渲染灰色占位块。**后续要求插件投稿时顺带提交图片。**

---

## 6. 收录方式

1. 在 `plugins/` 目录下新建 `<plugin-name>/` 文件夹，包含：
   * `plugin.json`：包含上述全部必填字段的插件描述文件；
   * `index.html`（或 `plugin.json` 中 `entry` 指向的文件）：插件页面。
   * （可选）`images/<plugin-name>.png`：展示图片。
2. 提交 Pull Request。CI 会自动校验：
   * 文件夹名与 `plugin.json` 的 `id` 一致；
   * `description` / `description-en` / `root` / `entry` 齐备且合法；
   * `entry` 指向的文件真实存在；
   * `dependency` 类型在白名单内。

PR 审核通过并合并后，流水线将自动把所有插件合并为全局注册表 `registry.json`，并重写本文档的插件清单。
