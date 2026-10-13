#!/usr/bin/env python3
"""构建 ui-plugin 的 registry.json 并同步 README.md

目录约定:
  plugins/<plugin-name>/plugin.json  每个插件一个独立文件夹，plugin.json 是插件的描述文件
  plugins/<plugin-name>/...          其余文件（index.html 等）随插件一起安装

统一字段: 注册表条目由各插件文件夹的 plugin.json 派生
  name          = 文件夹名（必须与 plugin.json 的 id 一致）
  description   = plugin.json 的 description-en（英文，市场用）
  description-zh= plugin.json 的 description（中文，宿主设置面板用）
  image         = plugin.json 的 image（可为空串；相对路径自动补全为 raw 绝对 URL）
  enabled       = 固定 true（UI 插件无启用开关，宿主扫描即生效）
  root          = plugin.json 的 root（期望放置位置：user / sandbox / builtin）
  files         = 插件文件夹内全部文件的相对路径（递归、posix 风格）
  dependency    = plugin.json 的 dependency 归一化后 [{type,id}]（白名单见 DEP_TYPES）
"""
import json
import os
import sys

REGISTRY_FILE = "registry.json"
README_FILE = "README.md"
REPO_URL = "https://github.com/PurrPod/ui-plugin"
RAW_BASE = "https://raw.githubusercontent.com/PurrPod/ui-plugin/main"

PLUGINS_DIR = "plugins"

# 依赖类型白名单，与极简宿主 webmin.py 的 DEP_TYPES 完全一致
DEP_TYPES = ("skill", "plugin", "mcp", "agentloop", "sensor", "graph")
ROOTS = ("user", "sandbox", "builtin")


def fail(msg):
    print(f"[Error] {msg}")
    sys.exit(1)


def load_json(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        fail(f"无法读取或解析 {filepath}: {e}")


def list_plugin_files(folder):
    """列出插件文件夹内全部文件的相对路径（posix 风格，排序）。"""
    rels = []
    for root, _dirs, files in os.walk(folder):
        for name in files:
            if name.startswith("."):
                continue
            rel = os.path.relpath(os.path.join(root, name), folder)
            rels.append(rel.replace("\\", "/"))
    return sorted(rels)


def normalize_dependency(raw, folder):
    out = []
    if raw is None:
        return out
    if not isinstance(raw, list):
        fail(f"[{folder}/plugin.json] 'dependency' 必须是数组")
    for item in raw:
        if not isinstance(item, dict):
            fail(f"[{folder}/plugin.json] 'dependency' 元素必须是对象 {{type,id}}")
        dep_type = str(item.get("type") or "").strip()
        dep_id = str(item.get("id") or "").strip()
        if dep_type not in DEP_TYPES:
            fail(
                f"[{folder}/plugin.json] 'dependency.type' ('{dep_type}') 非法，"
                f"仅支持 {', '.join(DEP_TYPES)}"
            )
        if not dep_id:
            fail(f"[{folder}/plugin.json] 'dependency.id' 不能为空")
        out.append({"type": dep_type, "id": dep_id})
    return out


def resolve_image(image, folder):
    image = str(image or "").strip()
    if not image:
        return ""
    if image.startswith(("http://", "https://")):
        return image
    return f"{RAW_BASE}/{image.lstrip('/')}"


def build_entry(folder_name):
    """由 plugins/<folder_name>/plugin.json 派生注册表条目。"""
    folder = os.path.join(PLUGINS_DIR, folder_name)
    desc_file = os.path.join(folder, "plugin.json")
    if not os.path.isfile(desc_file):
        return None  # 不是插件文件夹，跳过

    desc = load_json(desc_file)
    if not isinstance(desc, dict):
        fail(f"[{folder}/plugin.json] 内容必须是一个 JSON 对象")

    pid = str(desc.get("id") or "").strip()
    if not pid:
        fail(f"[{folder}/plugin.json] 缺少 'id'")
    if pid != folder_name:
        fail(f"[{folder}/plugin.json] 'id' ('{pid}') 必须与文件夹名 ('{folder_name}') 一致")

    if not str(desc.get("description", "")).strip():
        fail(f"[{folder}/plugin.json] 'description' (中文) 不能为空")
    if not str(desc.get("description-en", "")).strip():
        fail(f"[{folder}/plugin.json] 'description-en' (英文) 不能为空")

    root = str(desc.get("root") or "").strip()
    if root not in ROOTS:
        fail(f"[{folder}/plugin.json] 'root' 必须是 {', '.join(ROOTS)} 之一")

    if not str(desc.get("entry") or "").strip():
        fail(f"[{folder}/plugin.json] 缺少 'entry'")

    files = list_plugin_files(folder)
    if "plugin.json" not in files:
        fail(f"[{folder}] 插件文件夹缺少 plugin.json")
    if not str(desc.get("entry", "")).replace("\\", "/") in files:
        fail(f"[{folder}] 'entry' 指向的文件不存在: {desc.get('entry')}")

    return {
        "name": pid,
        "description": desc["description-en"],
        "description-zh": desc["description"],
        "image": resolve_image(desc.get("image"), folder),
        "enabled": True,
        "root": root,
        "files": files,
        "dependency": normalize_dependency(desc.get("dependency"), folder),
    }


def scan_plugins():
    entries = []
    if not os.path.isdir(PLUGINS_DIR):
        return entries
    for item in sorted(os.listdir(PLUGINS_DIR)):
        if item.startswith("."):
            continue
        folder = os.path.join(PLUGINS_DIR, item)
        if not os.path.isdir(folder):
            continue
        entry = build_entry(item)
        if entry:
            entries.append(entry)
    return entries


def generate_markdown_table(entries):
    lines = [
        "| 插件名 (Install ID) | 描述 | 图片 |",
        "| :--- | :--- | :--- |",
    ]
    if not entries:
        lines.append("| *(虚位以待)* | 期待您的收录！ |  |")
        return "\n".join(lines) + "\n"

    for info in entries:
        name = info["name"]
        desc = str(info["description-zh"]).replace("|", "\\|")
        image = "✅" if info["image"] else "—"
        lines.append(f"| `{name}` | {desc} | {image} |")
    return "\n".join(lines) + "\n"


def replace_between_tags(text, start_tag, end_tag, new_content):
    start_idx = text.find(start_tag)
    end_idx = text.find(end_tag)
    if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
        head = text[: start_idx + len(start_tag)]
        tail = text[end_idx:]
        return f"{head}\n{new_content}{tail}"
    return text


def update_readme(entries):
    if not os.path.exists(README_FILE):
        return
    with open(README_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    content = replace_between_tags(
        content,
        "<!-- PLUGINS:START -->",
        "<!-- PLUGINS:END -->",
        generate_markdown_table(entries),
    )
    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    print(f"扫描 {PLUGINS_DIR}/ 下的 UI 插件 ...")
    entries = scan_plugins()

    names = [e["name"] for e in entries]
    duplicates = sorted({n for n in names if names.count(n) > 1})
    if duplicates:
        fail(f"存在同名插件: {', '.join(duplicates)}")

    registry = {
        "version": "1.0",
        "repository": REPO_URL,
        "plugins": entries,
    }

    print(f"生成 {REGISTRY_FILE} ...")
    with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print("更新 README.md ...")
    update_readme(entries)

    print(f"构建与校验完成！共 {len(entries)} 个 UI 插件。")


if __name__ == "__main__":
    main()
