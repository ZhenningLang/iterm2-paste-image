<p align="center">
  <img src="logo.svg" width="128" height="128" alt="Paw">
</p>

<h1 align="center">Paw</h1>
<p align="center">终端文本增强插件 — 中文分词跳转 · 图片粘贴 · Cmd+Z 撤销</p>
<p align="center">Terminal enhancement for macOS — Chinese word segmentation · clipboard image paste · Cmd+Z undo</p>
<p align="center">
  <strong>iTerm2 · Tabby · Ghostty · tmux</strong>
</p>

---

## 功能

| 功能 | 按键 | 实现层 | 终端要求 |
|------|------|--------|----------|
| 中文分词跳转 | Option+←/→ | zsh widget + jieba daemon | 任意终端 (zsh) |
| 中文分词删除 | Option+Delete | zsh widget + jieba daemon | 任意终端 (zsh) |
| 剪贴板图片粘贴 | Cmd+V | iTerm2 Python 插件 / Tabby 插件 | iTerm2 / Tabby |
| 剪贴板图片粘贴 | Ctrl+V / Cmd+V | tmux 按键绑定 + shell 脚本 | 任意终端 + tmux |
| Cmd+Z 撤销 | Cmd+Z | iTerm2 plist 键映射 / Tabby 插件 | iTerm2 / Tabby |

### 中文分词跳转

在终端命令行中按 Option+Arrow 可以按中文词语跳转光标，而非逐字移动。基于 jieba 分词，常驻 daemon 通过 Unix socket 响应。

### 图片粘贴

按 Cmd+V 时自动检测剪贴板中是否有图片，有则保存为文件并粘贴路径，无则正常粘贴文本。适用于 AI 编程助手、Markdown 编辑等场景。

支持三种终端环境：
- **iTerm2**：通过 Python API 插件拦截 Cmd+V
- **Tabby**：通过 Electron 插件拦截粘贴
- **tmux（推荐）**：通过 tmux 按键绑定 + shell 脚本，适用于任意终端（Ghostty、Alacritty 等）

## 安装

```bash
npm install -g github:ZhenningLang/paw
```

或手动安装：

```bash
git clone https://github.com/ZhenningLang/paw.git
cd paw
./install.sh
```

安装完成后运行 `paw` 管理功能。

### 前置条件

- macOS
- zsh（分词功能）
- iTerm2 + Python API 已启用，或 Tabby（图片粘贴 / Cmd+Z 功能），或 tmux（图片粘贴）
- [pngpaste](https://github.com/jcsalterego/pngpaste)：`brew install pngpaste`（图片粘贴必需）
- (可选) Node.js + npm（构建 Tabby 插件）

### 启用 iTerm2 Python API

Settings (Cmd+,) → General → Magic → 勾选 **Enable Python API** → 重启 iTerm2

### Tabby 插件

安装脚本会自动检测 Tabby 并安装 `tabby-paw` 插件到 `~/Library/Application Support/tabby/plugins/`。也可通过 `paw` 交互式界面启停。安装后重启 Tabby 生效。

Tabby 插件提供：
- **Cmd+Z** → 发送 undo 控制字符 (0x1f)
- **Cmd+V** → 检测剪贴板图片，保存后粘贴路径

### tmux 图片粘贴

适用于 Ghostty、Alacritty 等没有插件系统的终端。通过 `paw` CLI 启用后，在 tmux 中按 Ctrl+V 即可粘贴图片路径或普通文本。

启用方式：运行 `paw`，选择 "tmux image paste" 启用。会自动安装脚本并配置 `~/.tmux.conf`。

如果使用 Ghostty 并希望 Cmd+V 触发，在 Ghostty 配置中添加：

```
keybind = cmd+v=text:\x16
```

这会将 Cmd+V 映射为 Ctrl+V，从而被 tmux 拦截处理。

## 使用

### CLI 管理工具

```bash
paw              # 交互式主界面（查看状态、启停功能）
paw status       # 非交互式状态查看
paw diagnose     # 诊断 + 自动修复
paw daemon start|stop|restart|status
```

### 配置文件

`~/.config/paw/config.json`：

```json
{
    "paste_image": {
        "save_directory": "~/.config/paw/images",
        "filename_format": "%Y%m%d_%H%M%S",
        "output_format": "{path}"
    }
}
```

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `save_directory` | 图片保存目录 | `~/.config/paw/images` |
| `filename_format` | 文件名时间格式 (strftime) | `%Y%m%d_%H%M%S` |
| `output_format` | 输出模板，变量：`{path}` `{filename}` `{dir}` | `{path}` |

## 架构

```
~/.config/paw/
├── paw_cli.py          # CLI 管理工具
├── paw_segmenter.py    # jieba 分词 daemon（Unix socket）
├── paw.zsh             # zle widget + 按键绑定
├── paw.py              # iTerm2 图片粘贴插件
├── paw-tmux-paste.sh   # tmux 图片粘贴脚本
├── venv/               # Python 虚拟环境 (jieba)
├── config.json         # 用户配置
├── paw.sock            # daemon socket
├── paw.pid             # daemon PID
└── images/             # 粘贴的图片

~/Library/Application Support/tabby/plugins/node_modules/tabby-paw/
├── package.json        # Tabby 插件描述
└── dist/index.js       # Tabby 插件（Cmd+Z + 图片粘贴）
```

分词功能链路：`按键 → zsh widget → nc -U socket → jieba daemon → 返回新光标位置 → zle 更新`

## 常见问题

**Option+Arrow 没反应？**
运行 `paw diagnose`，自动检测 daemon、zshrc、jieba 状态并修复。

**图片粘贴不工作？**
- iTerm2：确认 Python API 已启用，运行 `paw diagnose` 检查。
- Tabby：确认 tabby-paw 插件已安装（`paw status` 查看），重启 Tabby。
- tmux：确认 `pngpaste` 已安装（`brew install pngpaste`），运行 `paw diagnose` 检查脚本和 tmux.conf 配置。
- Ghostty + tmux：确认 Ghostty 配置中添加了 `keybind = cmd+v=text:\x16`，并重启 Ghostty。

## License

MIT
