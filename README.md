# iTerm2 Paste Image

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
git clone https://github.com/YOUR_USERNAME/iterm2-paste-image.git
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
