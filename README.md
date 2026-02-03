# iTerm2 Paste Image

[English](#english) | [中文](#中文)

---

<a name="english"></a>

An iTerm2 plugin that automatically detects images in your clipboard when you press `Cmd+V`. Instead of doing nothing (iTerm2's default behavior for images), it saves the image to a local directory and pastes the file path.

Perfect for workflows where you need to reference images by path, such as:
- AI coding assistants (Claude, GPT, etc.) that accept image paths
- Markdown editing
- File management tasks

## Features

- **Zero friction**: Just use `Cmd+V` as usual - the plugin detects if clipboard contains an image
- **Configurable save directory**: Store images wherever you want
- **Customizable output format**: Output just the path, filename, or a custom format
- **Automatic filename**: Timestamps ensure unique filenames

## Requirements

- macOS
- iTerm2 3.x with Python API enabled
- (Recommended) [pngpaste](https://github.com/jcsalterego/pngpaste) for better performance

## Installation

### Quick Install

```bash
git clone https://github.com/ZhenningLang/iterm2-paste-image.git
cd iterm2-paste-image
./install.sh
```

### Manual Install

1. Copy `paste_image.py` to `~/Library/Application Support/iTerm2/Scripts/`
2. Create config directory: `mkdir -p ~/.config/iterm2-paste-image`
3. Copy `config.example.json` to `~/.config/iterm2-paste-image/config.json`

### Enable Python API

1. Open iTerm2 → Preferences → General → Magic
2. Check "Enable Python API"
3. Restart iTerm2

### Start the Plugin

- Go to iTerm2 menu → Scripts → paste_image.py

### Auto-start (Optional)

To run the plugin automatically when iTerm2 starts:

```bash
mkdir -p ~/Library/Application\ Support/iTerm2/Scripts/AutoLaunch
ln -s ~/Library/Application\ Support/iTerm2/Scripts/paste_image.py \
      ~/Library/Application\ Support/iTerm2/Scripts/AutoLaunch/paste_image.py
```

## Configuration

Edit `~/.config/iterm2-paste-image/config.json`:

```json
{
  "save_directory": "~/.iterm2-paste-image/images",
  "filename_format": "%Y%m%d_%H%M%S",
  "output_format": "{path}"
}
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `save_directory` | Where to save images (supports `~`) | `~/.iterm2-paste-image/images` |
| `filename_format` | strftime format for filename | `%Y%m%d_%H%M%S` |
| `output_format` | Output template. Variables: `{path}`, `{filename}`, `{dir}` | `{path}` |

### Output Format Examples

- Full path: `"{path}"` → `/Users/me/.iterm2-paste-image/images/20240101_120000.png`
- Filename only: `"{filename}"` → `20240101_120000.png`
- Markdown: `"![image]({path})"` → `![image](/Users/me/.iterm2-paste-image/images/20240101_120000.png)`

## How It Works

1. Plugin monitors `Cmd+V` keystrokes via iTerm2 Python API
2. When detected, checks if clipboard contains an image (PNG or TIFF)
3. If image found:
   - Saves to configured directory using `pngpaste` or native macOS APIs
   - Sends the file path to the terminal
   - Consumes the keystroke (prevents default paste behavior)
4. If no image, lets iTerm2 handle the paste normally

## Troubleshooting

### Plugin doesn't start
- Ensure Python API is enabled in iTerm2 Preferences
- Check iTerm2 → Scripts menu for errors

### Images not saving
- Install pngpaste: `brew install pngpaste`
- Check write permissions on save directory

### Path not appearing
- Verify the clipboard contains an image (try pasting in Preview first)
- Check console output for errors: iTerm2 → Scripts → Manage → Console

## License

MIT License - see [LICENSE](LICENSE)

## Contributing

Contributions welcome! Please open an issue or PR.

---

<a name="中文"></a>

# iTerm2 Paste Image (中文)

一个 iTerm2 插件，当你按下 `Cmd+V` 时自动检测剪贴板中的图片。与 iTerm2 默认行为（忽略图片）不同，它会将图片保存到本地目录并粘贴文件路径。

适用场景：
- AI 编程助手（Claude、GPT 等）需要图片路径作为输入
- Markdown 编辑
- 文件管理任务

## 功能特性

- **零摩擦**：像往常一样使用 `Cmd+V`，插件自动检测剪贴板是否包含图片
- **可配置保存目录**：自定义图片存储位置
- **自定义输出格式**：输出完整路径、文件名或自定义格式
- **自动命名**：使用时间戳确保文件名唯一

## 系统要求

- macOS
- iTerm2 3.x 并启用 Python API
- （推荐）安装 [pngpaste](https://github.com/jcsalterego/pngpaste) 以获得更好性能

## 安装

### 快速安装

```bash
git clone https://github.com/ZhenningLang/iterm2-paste-image.git
cd iterm2-paste-image
./install.sh
```

### 手动安装

1. 复制 `paste_image.py` 到 `~/Library/Application Support/iTerm2/Scripts/`
2. 创建配置目录：`mkdir -p ~/.config/iterm2-paste-image`
3. 复制 `config.example.json` 到 `~/.config/iterm2-paste-image/config.json`

### 启用 Python API

1. 打开 iTerm2 → Preferences → General → Magic
2. 勾选 "Enable Python API"
3. 重启 iTerm2

### 启动插件

- 进入 iTerm2 菜单 → Scripts → paste_image.py

### 开机自启（可选）

```bash
mkdir -p ~/Library/Application\ Support/iTerm2/Scripts/AutoLaunch
ln -s ~/Library/Application\ Support/iTerm2/Scripts/paste_image.py \
      ~/Library/Application\ Support/iTerm2/Scripts/AutoLaunch/paste_image.py
```

## 配置

编辑 `~/.config/iterm2-paste-image/config.json`：

```json
{
  "save_directory": "~/.iterm2-paste-image/images",
  "filename_format": "%Y%m%d_%H%M%S",
  "output_format": "{path}"
}
```

### 配置项

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `save_directory` | 图片保存目录（支持 `~`） | `~/.iterm2-paste-image/images` |
| `filename_format` | 文件名时间格式（strftime） | `%Y%m%d_%H%M%S` |
| `output_format` | 输出模板，变量：`{path}`、`{filename}`、`{dir}` | `{path}` |

### 输出格式示例

- 完整路径：`"{path}"` → `/Users/me/.iterm2-paste-image/images/20240101_120000.png`
- 仅文件名：`"{filename}"` → `20240101_120000.png`
- Markdown：`"![image]({path})"` → `![image](/Users/me/.iterm2-paste-image/images/20240101_120000.png)`

## 工作原理

1. 插件通过 iTerm2 Python API 监听 `Cmd+V` 按键
2. 检测剪贴板是否包含图片（PNG 或 TIFF）
3. 如果有图片：
   - 使用 `pngpaste` 或原生 macOS API 保存到配置目录
   - 将文件路径发送到终端
   - 拦截按键（阻止默认粘贴行为）
4. 如果没有图片，正常执行粘贴

## 常见问题

### 插件无法启动
- 确保 iTerm2 偏好设置中已启用 Python API
- 检查 iTerm2 → Scripts 菜单是否有错误提示

### 图片未保存
- 安装 pngpaste：`brew install pngpaste`
- 检查保存目录的写入权限

### 路径未显示
- 确认剪贴板中确实有图片（可先在预览中尝试粘贴）
- 查看控制台输出：iTerm2 → Scripts → Manage → Console

## 许可证

MIT License - 详见 [LICENSE](LICENSE)

## 贡献

欢迎提交 Issue 或 PR！
