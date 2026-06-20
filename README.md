# 🎙️ OmniSenseVoice

> 在 [EasySenseVoice](https://github.com/fanweichu/EasySenseVoice) 基础上改造的**全平台**版本，新增 Windows 10/11 支持，并简化了系统依赖。

**OmniSenseVoice** 是一款基于 [SenseVoice](https://github.com/FunAudioLLM/SenseVoice) 和 [Sherpa-ONNX](https://github.com/k2-fsa/sherpa-onnx) 打造的**极速、纯本地、跨平台**语音输入工具。

只需运行一个脚本，即可将你的电脑变成高效的语音输入设备：**按住 `F9` 说话，松开即刻识别并自动粘贴文本到当前光标处**。

## ✨ 核心特性

- 🌍 **全平台支持**：macOS / Linux 桌面 / **Windows 10 & 11**。
- 🔒 **纯本地离线**：模型完全在本地运行，断网可用，**100% 保护隐私**，语音数据绝不上云。
- ⚡ **极速响应**：`int8 量化版` 和 `原版精度` 均可实现**亚秒级**解析，真正做到"即说即出"。
- 🤖 **傻瓜式操作**：脚本自带自检系统，自动安装 Python 依赖、自动下载模型并解压。
- ⌨️ **全局快捷键**：全局监听，无缝嵌入任何软件（浏览器、IDE、聊天软件、Office 等）。
- 🪟 **Windows 零系统依赖**：不需要装 sox/xdotool 之类的外部工具，纯 Python 包搞定。

---

## 🚀 安装与运行

### 🪟 Windows 10 / 11 用户（推荐：直接下载 .exe）

1. 去 [Releases 页面](https://github.com/liuzhicheng1775/OmniSenseVoice/releases) 下载最新的 `OmniSenseVoice-vX.X.X-win64.zip`
2. 解压到任意目录
3. 双击 `OmniSenseVoice.exe` 运行

首次启动会自动下载模型（约 999MB，存到 `%APPDATA%\OmniSenseVoice\`，只下一次），并让你选择模型精度。

**首次按 F9 录音时若 Windows 要求麦克风权限**，去「设置 → 隐私 → 麦克风」打开"允许桌面应用访问麦克风"。

> 💡 如果某些以管理员身份运行的软件（如管理员模式的 cmd）粘贴失效，请右键 `OmniSenseVoice.exe` 选择**「以管理员身份运行」**。这是 Windows UAC 的隔离机制，不是程序问题。
>
> ⚠️ 杀软可能误报（因为 PyInstaller 打包 + 全局键盘监听），把 exe 加白名单即可。

### 💻 开发者：从源码运行

克隆本仓库到本地：
```bash
git clone https://github.com/liuzhicheng1775/OmniSenseVoice.git
cd OmniSenseVoice
```

#### 🪟 Windows（源码模式）

**前置要求**：Python 3.9 ~ 3.12（[python.org](https://www.python.org/downloads/windows/) 下载，安装时务必勾选 "Add Python to PATH"）。

```powershell
python -m pip install -r requirements.txt
python main.py
```

#### 🐧 Linux 用户指南

需要调用底层工具实现录音和键盘模拟，**首次运行需要 `sudo` 自动安装系统依赖**（`sox`、`xdotool`、`xclip`）。

**第 1 步：安装系统依赖（仅限首次）**
```bash
sudo python3 main.py
```
*(系统会自动执行 `apt-get` 安装所需组件)*

**第 2 步：日常启动（切勿使用 sudo）**
```bash
python3 main.py
```

#### 🍎 macOS 用户指南

macOS 需要 `sox` 进行录音。

```bash
brew install sox
python3 main.py
```

---

### 🐧 Linux 用户指南

Linux 需要调用底层工具来实现录音和键盘模拟，**首次运行需要 `sudo` 自动安装系统依赖**（`sox`、`xdotool`、`xclip`）。

**第 1 步：安装系统依赖（仅限首次）**
```bash
sudo python3 main.py
```
*(系统会自动执行 `apt-get` 安装所需组件)*

**第 2 步：日常启动（切勿使用 sudo）**
```bash
python3 main.py
```

---

### 🍎 macOS 用户指南

macOS 需要 `sox` 进行录音。

**第 1 步：安装系统依赖**
确保已安装 [Homebrew](https://brew.sh/)，然后：
```bash
brew install sox
```

**第 2 步：启动程序**
```bash
python3 main.py
```

---

## 🎮 使用说明

1. 保持终端中 `python main.py` 处于运行状态。
2. 将光标放置在任何你想输入文字的地方（Word、微信、IDE、浏览器…）。
3. **按住 `F9`（或 `F5`）键** 开始说话。
4. **松开按键**，程序在亚秒级完成识别，并自动粘贴文字到光标位置。
5. 退出程序：在终端中按 `Ctrl + C`。

### 🔄 切换模型精度

模型包内含两个版本，速度都极快，差别在内存占用：

- **int8 量化版**：~230MB，推荐日常后台常驻。
- **原版精度**：~900MB，最高精度。

切换模型：
```bash
python main.py --select
```

---

## 🛠️ 技术栈

| 层 | 技术 |
|---|---|
| 推理引擎 | [Sherpa-ONNX](https://github.com/k2-fsa/sherpa-onnx)（K2 团队） |
| ASR 模型 | [SenseVoice Small](https://github.com/FunAudioLLM/SenseVoice)（阿里通义实验室，支持中英日韩粤） |
| 录音 | macOS / Linux: `sox`；**Windows: `sounddevice`（纯 Python，免装系统软件）** |
| 全局键盘监听 | `pynput` |
| 模拟粘贴 | macOS: `osascript` / Linux: `xdotool` / **Windows: `pynput.keyboard.Controller`** |

## 🔄 与原版 [EasySenseVoice](https://github.com/fanweichu/EasySenseVoice) 的差异

- ✅ 新增 Windows 10/11 完整支持
- ✅ Windows 端使用 `sounddevice` 录音，无需安装 sox 等外部工具
- ✅ Windows 端使用 `pynput.keyboard.Controller` 模拟 Ctrl+V，零外部依赖
- ✅ 临时音频文件路径改为 `tempfile.gettempdir()`，跨平台兼容
- ✅ Linux / macOS 行为完全保持不变，原版功能不受影响

## 📝 License

MIT License。本项目衍生自 [EasySenseVoice](https://github.com/fanweichu/EasySenseVoice)，鸣谢原作者 [@fanweichu](https://github.com/fanweichu) 与上游 [SenseVoice](https://github.com/FunAudioLLM/SenseVoice)、[Sherpa-ONNX](https://github.com/k2-fsa/sherpa-onnx) 团队。

---

## 🛠️ 维护者：构建 .exe

本项目已配置 GitHub Actions，**推 `v*` 开头的 tag 会自动在 Windows 环境构建 .exe 并发布到 Release**：

```bash
git tag v1.0.0
git push origin v1.0.0
# 等 ~10 分钟，去 Release 页面看 zip
```

本地手动构建（需要在 Windows 上）：

```powershell
pip install -r requirements.txt
pip install pyinstaller
pyinstaller build.spec --noconfirm
# 产物在 dist\OmniSenseVoice\
```

打包关键点：
- `build.spec` 用 `collect_all` 收集 sherpa_onnx / sounddevice / numpy 等带原生库的依赖
- 模型**不打包**进 exe（999MB 太大），首次运行自动下载到 `%APPDATA%\OmniSenseVoice\`
- 用 OneDir 模式（不是 OneFile），启动快、调试方便
