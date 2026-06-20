#!/usr/bin/env python3

"""
=== OmniSenseVoice v2.1 (Sherpa-ONNX + SenseVoice) ===
跨平台语音输入工具：按住 F9 或 F5 录音，松开后自动识别并粘贴到光标位置。
平台：macOS / Linux / Windows 10/11
用法：
  python3 main.py            # 正常启动
  python3 main.py --select   # 重新选择模型
"""

import os
import sys
import subprocess
import time
import re
import platform
import shutil
import json
import tempfile
from pathlib import Path

# ============================================================
#  1. 依赖自检与自动安装
# ============================================================
def ensure_dependencies():
    required = {
        "pynput": "pynput",
        "pyperclip": "pyperclip",
        "sherpa_onnx": "sherpa-onnx",
        "numpy": "numpy",
        "soundfile": "soundfile",
    }
    # Windows 需要额外的纯 Python 录音库（避免依赖 sox）
    if platform.system() == "Windows":
        required["sounddevice"] = "sounddevice"

    missing = []
    for module, package in required.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)

    if missing:
        print(f"[!] 发现缺失组件: {', '.join(missing)}")
        print("[-] 正在自动安装，请稍候...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
            print("[+] 安装完成，正在重启脚本...")
            os.execv(sys.executable, [sys.executable] + sys.argv)
        except Exception as e:
            print(f"[错误] 自动安装失败: {e}")
            print(f"请手动执行: pip3 install {' '.join(missing)}")
            sys.exit(1)

ensure_dependencies()

from pynput import keyboard
import pyperclip
import numpy as np
import soundfile as sf
import sherpa_onnx

# ============================================================
#  2. 平台检测与路径配置
# ============================================================
OS_TYPE = platform.system()


def get_app_data_dir() -> Path:
    """
    返回用户数据目录（跨平台、可写）。
    - Windows: %APPDATA%\\OmniSenseVoice
    - macOS:   ~/Library/Application Support/OmniSenseVoice
    - Linux:   ~/.OmniSenseVoice
    打包成 exe 后，脚本所在目录可能是只读的（OneDir 模式还行，OneFile 模式必读），
    所以模型和配置都放用户目录里。
    """
    if OS_TYPE == "Windows":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        return Path(base) / "OmniSenseVoice"
    elif OS_TYPE == "Darwin":
        return Path.home() / "Library" / "Application Support" / "OmniSenseVoice"
    else:
        return Path.home() / ".OmniSenseVoice"


APP_DATA_DIR = get_app_data_dir()
APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

BASE_DIR = Path(__file__).parent.absolute()
CONFIG_FILE = APP_DATA_DIR / ".sensevoice_config.json"  # 记住上次选择
AUDIO_FILE = os.path.join(tempfile.gettempdir(), "sensevoice_temp.wav")
SAMPLE_RATE = 16000

# 模型路径默认放 APP_DATA_DIR，但用户可以在配置文件里指定自定义位置
# （首次启动会询问，存到 CONFIG_FILE 的 model_dir 字段）

if OS_TYPE == "Darwin":
    REC_BIN = shutil.which("rec") or "/opt/homebrew/bin/rec"
elif OS_TYPE == "Linux":
    REC_BIN = shutil.which("rec") or "/usr/bin/rec"
elif OS_TYPE == "Windows":
    REC_BIN = None  # Windows 用 sounddevice，不依赖 sox
else:
    print("[!] 不支持的操作系统:", OS_TYPE)
    sys.exit(1)

# ============================================================
#  3. 系统依赖检查
# ============================================================
def check_system_deps():
    if OS_TYPE == "Windows":
        # Windows 不需要额外系统依赖，sounddevice 自带 PortAudio
        return

    if OS_TYPE == "Darwin":
        if not shutil.which("rec") and not Path("/opt/homebrew/bin/rec").exists():
            print("\n[!] 缺少系统依赖: sox")
            if not shutil.which("brew"):
                print("请先安装 Homebrew:")
                print('  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"')
            print("然后执行: brew install sox")
            sys.exit(1)

    elif OS_TYPE == "Linux":
        needed = ["sox", "xdotool", "xclip"]
        missing = [b for b in needed if not shutil.which(b)]
        if missing:
            print(f"\n[!] 缺少系统依赖: {', '.join(missing)}")
            if os.geteuid() != 0:
                print("=========================================================")
                print("⚠️  请使用 sudo 运行一次以自动安装系统依赖:")
                print(f"   sudo {sys.executable} {__file__}")
                print("=========================================================")
                sys.exit(1)
            else:
                print("[-] 正在自动安装系统依赖...")
                subprocess.run(
                    "apt-get update && apt-get install -y sox xdotool xclip wget",
                    shell=True, check=True
                )
                print("[+] 系统依赖安装完成。")

# ============================================================
#  4. 模型配置
# ============================================================

MODEL_OPTIONS = {
    "1": {
        "name": "int8 量化版",
        "file": "model.int8.onnx",
        "ram": "~230 MB",
        "speed": "⚡ 极快",
        "desc": "推荐，精度几乎无损，速度最快",
    },
    "2": {
        "name": "原版精度",
        "file": "model.onnx",
        "ram": "~900 MB",
        "speed": "⚡ 快",
        "desc": "最高精度，内存占用较大",
    },
}

# ============================================================
#  5. 配置读写（记住上次选择）
# ============================================================
def load_config():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_config(data: dict):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[警告] 配置保存失败: {e}")

# ============================================================
#  6. 模型下载
# ============================================================
import urllib.request
import tarfile

# 多个下载源（按速度/可用性排序）
# 国内用户推荐 ModelScope（阿里）或 HuggingFace mirror
MODEL_PACKAGE = {
    "subdir": "sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17",
    "sources": [
        {
            "name": "ModelScope（阿里云，国内最快）",
            "url": "https://www.modelscope.cn/models/iic/SenseVoiceSmall/resolve/master/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2",
        },
        {
            "name": "HuggingFace Mirror（国内镜像）",
            "url": "https://hf-mirror.com/k2-fsa/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17/resolve/main/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2",
        },
        {
            "name": "GitHub Releases（原始源，国内可能慢）",
            "url": "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2",
        },
    ],
    "subdir_in_tar": "sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17",
}


def _download_with_progress(url: str, dst: str, timeout: int = 60, start_time: float = None):
    """
    用标准库 urllib 下载文件，带进度条 + 断点续传。
    不依赖 wget/curl，打包成 exe 后也能工作。
    支持断点续传：如果 dst 已存在部分文件，从已下载位置继续。
    """
    if start_time is None:
        start_time = time.time()

    existing_size = os.path.getsize(dst) if os.path.exists(dst) else 0

    headers = {"User-Agent": "OmniSenseVoice/2.1"}
    if existing_size > 0:
        headers["Range"] = f"bytes={existing_size}-"

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        # 206 = Partial Content（断点续传成功）
        # 200 = 服务器不支持 Range，从头下
        if resp.status == 200 and existing_size > 0:
            existing_size = 0  # 服务器忽略 Range，从头开始

        total_header = resp.headers.get("Content-Length")
        total = int(total_header) + existing_size if total_header else 0

        downloaded = existing_size
        chunk = 1024 * 256  # 256 KB（更大块，提高速度）
        last_pct = -1
        mode = "ab" if existing_size > 0 and resp.status == 206 else "wb"

        with open(dst, mode) as f:
            while True:
                try:
                    data = resp.read(chunk)
                except Exception as e:
                    print(f"\n[警告] 网络中断: {e}，已下载 {downloaded / 1024 / 1024:.1f} MB")
                    print("[*] 重试中...（断点续传，不会从头开始）")
                    time.sleep(2)
                    return _download_with_progress(url, dst, timeout, start_time)

                if not data:
                    break
                f.write(data)
                downloaded += len(data)
                if total > 0:
                    pct = downloaded * 100 // total
                    if pct != last_pct:
                        bar_len = 40
                        filled = bar_len * pct // 100
                        bar = "█" * filled + "-" * (bar_len - filled)
                        size_mb = downloaded / 1024 / 1024
                        total_mb = total / 1024 / 1024
                        speed_mb = (downloaded - existing_size) / 1024 / 1024 / max(0.001, time.time() - start_time)
                        print(f"\r[{bar}] {pct:3d}%  {size_mb:.1f}/{total_mb:.1f} MB  {speed_mb:.1f} MB/s", end="", flush=True)
                        last_pct = pct
        print()  # 换行
    return downloaded


def _choose_download_source(config: dict) -> str:
    """让用户选下载源"""
    print("\n[*] 模型包约 999MB，请选择下载源（国内推荐选 1 或 2）：")
    for i, src in enumerate(MODEL_PACKAGE["sources"], 1):
        print(f"  {i}. {src['name']}")

    # 自定义 URL 选项
    print(f"  {len(MODEL_PACKAGE['sources']) + 1}. 自定义 URL（已有镜像/本地 HTTP 服务时用）")

    saved_choice = config.get("download_source")
    if saved_choice:
        print(f"\n[上次选择]: {saved_choice}（直接回车使用上次）")

    while True:
        try:
            raw = input(f"\n请选择 [1-{len(MODEL_PACKAGE['sources']) + 1}]: ").strip()
        except EOFError:
            raw = "1"

        if not raw and saved_choice:
            # 用上次选择
            try:
                idx = int(saved_choice) - 1
                if 0 <= idx < len(MODEL_PACKAGE["sources"]):
                    return MODEL_PACKAGE["sources"][idx]["url"]
            except ValueError:
                pass

        if not raw:
            print("[!] 请输入选项")
            continue

        try:
            idx = int(raw) - 1
            if 0 <= idx < len(MODEL_PACKAGE["sources"]):
                config["download_source"] = raw
                save_config(config)
                return MODEL_PACKAGE["sources"][idx]["url"]
            elif idx == len(MODEL_PACKAGE["sources"]):
                # 自定义 URL
                custom = input("请输入完整 URL（指向 .tar.bz2 文件）: ").strip()
                if custom:
                    config["download_source"] = raw
                    config["custom_download_url"] = custom
                    save_config(config)
                    return custom
                else:
                    print("[!] URL 不能为空")
                    continue
        except ValueError:
            pass
        print("[!] 无效选择")


def _choose_model_dir(config: dict) -> Path:
    """让用户选择模型存储位置（首次运行时询问）"""
    default_dir = APP_DATA_DIR / "sensevoice-models"
    saved_dir = config.get("model_dir")

    if saved_dir and Path(saved_dir).exists():
        return Path(saved_dir)

    print("\n[*] 选择模型存储位置（模型约 1GB，建议放空间充足的盘）")
    print(f"  1. 默认位置: {default_dir}")
    print(f"  2. 自定义位置（输入完整路径）")

    while True:
        try:
            choice = input("\n请选择 [1/2]（回车默认 1）: ").strip()
        except EOFError:
            choice = "1"

        if not choice or choice == "1":
            config["model_dir"] = str(default_dir)
            save_config(config)
            return default_dir
        elif choice == "2":
            try:
                path = input("请输入目录完整路径（如 D:\\Models\\OmniSenseVoice 或 /home/user/models）: ").strip()
            except EOFError:
                path = ""
            if not path:
                print("[!] 路径不能为空")
                continue
            try:
                p = Path(path).expanduser().absolute()
                p.mkdir(parents=True, exist_ok=True)
                # 测试可写
                test_file = p / ".write_test"
                test_file.write_text("test")
                test_file.unlink()
                config["model_dir"] = str(p)
                save_config(config)
                print(f"[+] 已设置模型存储位置: {p}")
                return p
            except Exception as e:
                print(f"[!] 路径无效或不可写: {e}")
                continue
        else:
            print("[!] 无效选择")


def download_model_package(config: dict):
    """下载并解压模型包（含两个模型文件）"""
    model_dir = _choose_model_dir(config)
    model_path = model_dir / MODEL_PACKAGE["subdir"]

    if model_path.exists():
        return model_path

    print(f"\n[*] 需要下载 SenseVoice 模型包（~999MB，含 int8 和原版两个模型）")
    print(f"    存储位置: {model_dir}")
    input("    按 Enter 开始下载，Ctrl+C 取消...")

    os.makedirs(model_dir, exist_ok=True)
    tar_file = str(model_dir / "model.tar.bz2")

    url = _choose_download_source(config)

    try:
        print(f"\n[*] 正在下载...")
        print(f"    URL: {url}")
        _download_with_progress(url, tar_file)

        print("[*] 正在解压模型包...")
        with tarfile.open(tar_file, "r:bz2") as tar:
            tar.extractall(model_dir)
        os.remove(tar_file)
        print("[+] 模型包解压完成！\n")

    except KeyboardInterrupt:
        print("\n[!] 下载已取消。已下载的部分文件保留在：")
        print(f"    {tar_file}")
        print("    下次运行会自动断点续传。")
        sys.exit(0)
    except Exception as e:
        print(f"\n[错误] 下载失败: {e}")
        print(f"\n[建议] 尝试其他下载源：")
        for src in MODEL_PACKAGE["sources"]:
            print(f"  - {src['name']}: {src['url']}")
        print(f"\n或手动下载 .tar.bz2 文件，解压到: {model_dir}")
        sys.exit(1)

    return model_path

# ============================================================
#  7. 模型选择（含记忆功能）
# ============================================================
def show_model_menu():
    """显示模型选择菜单，返回用户选择的 key"""
    print()
    print("╔══════════════════════════════════════════════════╗")
    print("║         选择要加载的 SenseVoice 模型             ║")
    print("║         （两个模型已包含在同一下载包中）          ║")
    print("╠══════════════════════════════════════════════════╣")
    for k, v in MODEL_OPTIONS.items():
        print(f"║  {k}. {v['name']}")
        print(f"║     内存: {v['ram']}  速度: {v['speed']}")
        print(f"║     {v['desc']}")
        print("║")
    print("╚══════════════════════════════════════════════════╝")

    while True:
        choice = input("\n请选择 [1/2]: ").strip()
        if choice in MODEL_OPTIONS:
            return choice
        print("[!] 无效选择，请输入 1 或 2。")

def setup_model(force_select: bool = False):
    """
    模型管理主函数：
    - 首次运行：下载 → 选择 → 记住
    - 后续运行：直接加载上次的选择
    - force_select=True：重新选择（--select 参数触发）
    """
    config = load_config()

    # 确保模型包已下载
    model_path = download_model_package(config)

    # 判断是否需要重新选择
    saved_choice = config.get("model_choice")
    need_select = force_select or (saved_choice not in MODEL_OPTIONS)

    if need_select:
        if force_select:
            print("\n[*] 重新选择模型（--select 模式）")
        else:
            print("\n[*] 首次运行，请选择要加载的模型。")

        choice = show_model_menu()
        config["model_choice"] = choice
        save_config(config)
    else:
        choice = saved_choice
        print(f"[状态]: 加载上次选择的模型 -> {MODEL_OPTIONS[choice]['name']}")
        print(f"        （如需更换，请加 --select 参数重新运行）")

    selected = MODEL_OPTIONS[choice]
    return str(model_path), selected["file"], selected["name"]

# ============================================================
#  8. 创建 Sherpa-ONNX 识别器
# ============================================================
def create_recognizer(model_path: str, model_file: str):
    recognizer = sherpa_onnx.OfflineRecognizer.from_sense_voice(
        model=os.path.join(model_path, model_file),
        tokens=os.path.join(model_path, "tokens.txt"),
        num_threads=max(2, os.cpu_count() - 2),
        use_itn=True,
        language="auto",
        debug=False,
    )
    return recognizer

# ============================================================
#  9. 录音控制
# ============================================================
is_recording = False
record_process = None       # Linux/macOS: sox 子进程
sd_stream = None            # Windows: sounddevice 输入流
sd_buffer = []              # Windows: 录音帧累积

def start_recording():
    global is_recording, record_process, sd_stream, sd_buffer
    if is_recording:
        return
    is_recording = True
    if os.path.exists(AUDIO_FILE):
        try:
            os.remove(AUDIO_FILE)
        except OSError:
            pass
    print("\r🎙️  [录音中...] 松开按键停止          ", end="", flush=True)

    if OS_TYPE == "Windows":
        # Windows 走 sounddevice：开一个输入流，把帧塞到缓冲区
        import sounddevice as sd
        sd_buffer = []

        def _callback(indata, frames, time_info, status):
            sd_buffer.append(indata.copy())

        sd_stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            callback=_callback,
        )
        sd_stream.start()
    else:
        # Linux/macOS 维持原有 sox 流程
        record_process = subprocess.Popen(
            [REC_BIN, "-q", "-r", str(SAMPLE_RATE), "-c", "1", "-b", "16", AUDIO_FILE, "rate", "16k"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

def stop_recording_and_transcribe(recognizer):
    global is_recording, record_process, sd_stream, sd_buffer
    if not is_recording:
        return

    print("\r⏳ [正在识别...]                        ", end="", flush=True)
    is_recording = False

    if OS_TYPE == "Windows":
        # 停流，把累积的帧拼起来写入 wav
        if sd_stream is not None:
            try:
                sd_stream.stop()
                sd_stream.close()
            except Exception:
                pass
            sd_stream = None

        if sd_buffer:
            audio_concat = np.concatenate(sd_buffer, axis=0).reshape(-1).astype(np.float32)
            try:
                sf.write(AUDIO_FILE, audio_concat, SAMPLE_RATE, subtype="PCM_16")
            except Exception as e:
                print(f"\n[错误] 写入临时音频失败: {e}")
        sd_buffer = []
    else:
        if record_process:
            record_process.terminate()
            record_process.wait()
            record_process = None

    try:
        start_t = time.time()

        if not os.path.exists(AUDIO_FILE):
            print("\r[提示]: 未检测到音频文件。              ")
            return

        audio_data, sr = sf.read(AUDIO_FILE, dtype="float32")

        if len(audio_data) < sr * 0.3:
            print("\r[提示]: 录音太短，已跳过。              ")
            return

        # 确保单声道
        if len(audio_data.shape) > 1:
            audio_data = audio_data[:, 0]

        # 重采样（如有需要）
        if sr != SAMPLE_RATE:
            new_len = int(len(audio_data) * SAMPLE_RATE / sr)
            audio_data = np.interp(
                np.linspace(0, len(audio_data) - 1, new_len),
                np.arange(len(audio_data)),
                audio_data,
            ).astype(np.float32)

        # 识别
        stream = recognizer.create_stream()
        stream.accept_waveform(SAMPLE_RATE, audio_data)
        recognizer.decode_stream(stream)

        text = stream.result.text.strip()
        elapsed = time.time() - start_t

        # 清理 SenseVoice 特殊标签（如 <|zh|><|NEUTRAL|><|Speech|>）
        clean_text = re.sub(r'<\|[^>]*\|>', '', text).strip()

        if clean_text:
            print(f"\r[结果]: {clean_text}")
            print(f"[耗时]: {elapsed:.2f} 秒")
            pyperclip.copy(clean_text)
            if OS_TYPE == "Darwin":
                subprocess.run([
                    "osascript", "-e",
                    'tell application "System Events" to keystroke "v" using command down'
                ])
            elif OS_TYPE == "Linux":
                subprocess.run(["xdotool", "key", "ctrl+v"])
            elif OS_TYPE == "Windows":
                # 用 pynput 直接模拟 Ctrl+V，跨平台、零外部依赖
                kb = keyboard.Controller()
                with kb.pressed(keyboard.Key.ctrl):
                    kb.press('v')
                    kb.release('v')
        else:
            print("\r[提示]: 未检测到有效语音。              ")

    except Exception as e:
        print(f"\n[错误]: {e}")
    finally:
        if os.path.exists(AUDIO_FILE):
            try:
                os.remove(AUDIO_FILE)
            except OSError:
                pass

# ============================================================
#  10. 主程序
# ============================================================
def main():
    force_select = "--select" in sys.argv

    print("=" * 52)
    print("  OmniSenseVoice v2.1 (Sherpa-ONNX + SenseVoice)")
    print(f"  平台: {OS_TYPE}")
    print("=" * 52)

    check_system_deps()

    model_path, model_file, model_name = setup_model(force_select=force_select)

    print(f"\n[*] 正在加载模型: {model_name} ...")
    recognizer = create_recognizer(model_path, model_file)
    print("[+] 模型加载完成！")

    # 判断是否打包模式（PyInstaller 打包后 sys.frozen=True）
    is_frozen = getattr(sys, "frozen", False)
    if is_frozen:
        exe_name = os.path.basename(sys.executable)
        select_hint = f"  🔄 换模型: {exe_name} --select   "
    else:
        select_hint = "  🔄 换模型: python3 main.py --select"

    print()
    print("┌────────────────────────────────────────────────┐")
    print("│  ✅ 系统已就绪                                  │")
    print("│  🎙️  按住 F5 或 F9 录音，松开自动粘贴文本         │")
    print(f"│{select_hint:<48}│")
    print("│  ❌ 退出: Ctrl+C                                │")
    print("└────────────────────────────────────────────────┘")
    print()

    def on_press(key):
        # 同时监听 F9 和 F5
        if key in (keyboard.Key.f9, keyboard.Key.f5):
            start_recording()

    def on_release(key):
        # 对应释放逻辑
        if key in (keyboard.Key.f9, keyboard.Key.f5):
            stop_recording_and_transcribe(recognizer)

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

if __name__ == "__main__":
    main()
