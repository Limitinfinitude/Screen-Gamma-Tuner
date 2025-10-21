# ScreenGamma Tuner

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)

一个简单高效的 Windows 屏幕 Gamma 调整工具！使用 Tkinter 构建 GUI，支持实时调整 Gamma、亮度、对比度。最小化到系统托盘，支持配置保存/加载，并在退出时自动恢复原设置。核心通过 ctypes 调用 Windows API。

## 功能亮点
- **实时调整**：拖动滑块即时应用 Gamma (0.3-4.0)、亮度 (-1~1)、对比度 (0.1-3.0)。
- **系统托盘**：最小化后右键托盘菜单（加载配置、重置、显示窗口、退出）。
- **配置管理**：保存/加载 JSON 配置（默认 `config.json`）。
- **安全恢复**：崩溃/退出时自动还原原 Gamma Ramp。

## 安装 & 使用

### 1. 克隆仓库
```bash
git clone https://github.com/yourusername/ScreenGammaTuner.git
cd ScreenGammaTuner
```

### 2. 安装依赖

```
pip install -r requirements.txt
```

### 3. 运行

```
python gui.py  
```

- （可选）：打包 EXE，用 PyInstaller生成 dist/gui.exe。

  ```
  pip install pyinstaller
  pyinstaller --onefile --windowed gui.py
  ```

### 4. 用法

- **滑块调整**：拖动或用 +/- 按钮实时预览效果。
- **保存/加载**：点击 “Save/Load” 按钮管理配置。
- **重置**：点击 “Reset” 恢复默认 (G=1.0, B=0.0, C=1.0)。
- **托盘**：关闭窗口进入托盘，右键菜单操作。
- **退出**：托盘 > Quit，或 Ctrl+C（命令行）。

## 系统要求

- **OS**：Windows 10/11（依赖 GDI API）。
- **Python**：3.8+。
- **依赖**：pillow>=10.0.0、pystray==0.19.0。

感谢使用 ScreenGamma Tuner！🌟