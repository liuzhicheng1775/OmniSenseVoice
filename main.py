#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OmniSenseVoice v2.1 (Sherpa-ONNX + SenseVoice)
跨平台语音输入工具：按住 F5/F9 录音，松开自动识别并粘贴
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
# 配置与常量
# ============================================================

OS_TYPE = platform.system()

MODEL_OPTIONS = {
    '1': {
        'name': 'Int8 量化版',
        'file': 'model.int8.onnx',
        'ram': '~230 MB',
        'speed': '⚡ 极快',
        'desc': '推荐，精度几乎无损，速度更快',
    },
    '2': {
        'name': '原版精度',
        'file': 'model.onnx',
        'ram': '~900 MB',
        'speed': '⚡ 快',
        'desc': '最高精度，内存占用较大',
    },
}


# ============================================================
# 路径与配置
# ============================================================

def get_app_data_dir() -> Path:
    """获取用户数据目录"""
    if OS_TYPE == 'Windows':
        base = os.environ.get('APPDATA') or os.path.expanduser('~')
        return Path(base) / 'OmniSenseVoice'
    elif OS_TYPE == 'Darwin':
        return Path.home() / 'Library' / 'Application Support' / 'OmniSenseVoice'
    else:
        return Path.home() / '.OmniSenseVoice'


APP_DATA_DIR = get_app_data_dir()
APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = APP_DATA_DIR / '.sensevoice_config.json'


def load_config():
    """加载配置"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_config(data: dict):
    """保存配置"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f'[警告] 配置保存失败: {e}')


# ============================================================
# 依赖检查
# ============================================================

def ensure_dependencies():
    """确保依赖已安装"""
    required = {
        'pynput': 'pynput',
        'pyperclip': 'pyperclip',
        'sherpa_onnx': 'sherpa-onnx',
        'numpy': 'numpy',
        'soundfile': 'soundfile',
    }
    if OS_TYPE == 'Windows':
        required['sounddevice'] = 'sounddevice'

    missing = []
    for module, package in required.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)

    if missing:
        print(f'[!] 发现缺失组件: {", ".join(missing)}')
        print('[-] 正在自动安装，请稍候...')
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', *missing])
            print('[+] 安装完成，正在重启脚本...')
            os.execv(sys.executable, [sys.executable] + sys.argv)
        except Exception as e:
            print(f'[错误] 自动安装失败: {e}')
            print(f'请手动执行: pip3 install {" ".join(missing)}')
            sys.exit(1)


ensure_dependencies()

# 现在可以导入依赖了
from pynput import keyboard
import pyperclip
import numpy as np
import soundfile as sf
import sherpa_onnx


# ============================================================
# 系统依赖检查
# ============================================================

def check_system_deps():
    """检查系统依赖"""
    if OS_TYPE == 'Windows':
        return

    if OS_TYPE == 'Darwin':
        if not shutil.which('rec') and not Path('/opt/homebrew/bin/rec').exists():
            try:
                from tkinter import messagebox
                messagebox.showerror('缺少依赖', '请先安装 sox：\nbrew install sox')
            except:
                print('\n[!] 缺少系统依赖: sox')
                print('请先安装 Homebrew:')
                print('  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"')
                print('然后执行: brew install sox')
            sys.exit(1)

    elif OS_TYPE == 'Linux':
        needed = ['sox', 'xdotool', 'xclip']
        missing = [b for b in needed if not shutil.which(b)]
        if missing:
            if os.geteuid() != 0:
                try:
                    from tkinter import messagebox
                    messagebox.showerror('缺少依赖', f'请安装系统依赖：\nsudo apt install {" ".join(missing)}')
                except:
                    print(f'\n[!] 缺少系统依赖: {", ".join(missing)}')
                    print('=========================================================')
                    print('⚠️  请使用 sudo 运行一次以自动安装系统依赖:')
                    print(f'   sudo {sys.executable} {__file__}')
                    print('=========================================================')
                sys.exit(1)
            else:
                print('[-] 正在自动安装系统依赖...')
                subprocess.run(
                    'apt-get update && apt-get install -y sox xdotool xclip',
                    shell=True, check=True
                )
                print('[+] 系统依赖安装完成。')


# ============================================================
# 录音控制
# ============================================================

AUDIO_FILE = os.path.join(tempfile.gettempdir(), 'sensevoice_temp.wav')
RECORD_PROCESS = None
SD_STREAM = None
SD_BUFFER = []
IS_RECORDING = False


def start_recording():
    """开始录音"""
    global IS_RECORDING, RECORD_PROCESS, SD_STREAM, SD_BUFFER
    if IS_RECORDING:
        return

    IS_RECORDING = True
    if os.path.exists(AUDIO_FILE):
        try:
            os.remove(AUDIO_FILE)
        except OSError:
            pass

    if OS_TYPE == 'Windows':
        import sounddevice as sd
        SD_BUFFER = []

        def _callback(indata, frames, time_info, status):
            SD_BUFFER.append(indata.copy())

        SD_STREAM = sd.InputStream(
            samplerate=16000,
            channels=1,
            dtype='float32',
            callback=_callback,
        )
        SD_STREAM.start()
    else:
        rec_bin = shutil.which('rec')
        if OS_TYPE == 'Darwin':
            rec_bin = rec_bin or '/opt/homebrew/bin/rec'
        elif OS_TYPE == 'Linux':
            rec_bin = rec_bin or '/usr/bin/rec'

        RECORD_PROCESS = subprocess.Popen(
            [rec_bin, '-q', '-r', '16000', '-c', '1', '-b', '16', AUDIO_FILE, 'rate', '16k'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def stop_recording_and_transcribe(recognizer, callback=None):
    """停止录音并识别"""
    global IS_RECORDING, RECORD_PROCESS, SD_STREAM, SD_BUFFER
    if not IS_RECORDING:
        return

    IS_RECORDING = False

    if OS_TYPE == 'Windows':
        if SD_STREAM is not None:
            try:
                SD_STREAM.stop()
                SD_STREAM.close()
            except Exception:
                pass
            SD_STREAM = None

        if SD_BUFFER:
            audio_concat = np.concatenate(SD_BUFFER, axis=0).reshape(-1).astype(np.float32)
            try:
                sf.write(AUDIO_FILE, audio_concat, 16000, subtype='PCM_16')
            except Exception as e:
                print(f'\n[错误] 写入临时音频失败: {e}')
        SD_BUFFER = []
    else:
        if RECORD_PROCESS:
            RECORD_PROCESS.terminate()
            RECORD_PROCESS.wait()
            RECORD_PROCESS = None

    try:
        if not os.path.exists(AUDIO_FILE):
            return

        audio_data, sr = sf.read(AUDIO_FILE, dtype='float32')

        if len(audio_data) < sr * 0.3:
            return

        if len(audio_data.shape) > 1:
            audio_data = audio_data[:, 0]

        if sr != 16000:
            new_len = int(len(audio_data) * 16000 / sr)
            audio_data = np.interp(
                np.linspace(0, len(audio_data) - 1, new_len),
                np.arange(len(audio_data)),
                audio_data,
            ).astype(np.float32)

        stream = recognizer.create_stream()
        stream.accept_waveform(16000, audio_data)
        recognizer.decode_stream(stream)

        text = stream.result.text.strip()
        clean_text = re.sub(r'<\|[^>]+\|>', '', text).strip()

        if clean_text:
            print(f'[结果] {clean_text}')
            pyperclip.copy(clean_text)

            if OS_TYPE == 'Darwin':
                subprocess.run([
                    'osascript', '-e',
                    'tell application "System Events" to keystroke "v" using command down'
                ])
            elif OS_TYPE == 'Linux':
                subprocess.run(['xdotool', 'key', 'ctrl+v'])
            elif OS_TYPE == 'Windows':
                kb = keyboard.Controller()
                with kb.pressed(keyboard.Key.ctrl):
                    kb.press('v')
                    kb.release('v')

            if callback:
                callback(clean_text)

    except Exception as e:
        print(f'\n[错误]: {e}')
    finally:
        if os.path.exists(AUDIO_FILE):
            try:
                os.remove(AUDIO_FILE)
            except OSError:
                pass


# ============================================================
# 创建识别器
# ============================================================

def create_recognizer(model_path: str, model_file: str):
    """创建识别器"""
    return sherpa_onnx.OfflineRecognizer.from_sense_voice(
        model=os.path.join(model_path, model_file),
        tokens=os.path.join(model_path, 'tokens.txt'),
        num_threads=max(2, (os.cpu_count() or 2) - 2),
        use_itn=True,
        language='auto',
        debug=False,
    )


# ============================================================
# 模型管理
# ============================================================

def check_model_ready(config: dict) -> tuple[bool, Path, str]:
    """检查模型是否准备好"""
    model_dir = config.get('model_dir')
    model_choice = config.get('model_choice')

    if not model_dir or not model_choice:
        return False, Path(), ''

    model_dir = Path(model_dir)
    model_path = model_dir / 'sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17'

    if not model_path.exists():
        return False, model_path, ''

    return True, model_path, MODEL_OPTIONS[model_choice]['file']


# ============================================================
# 控制台模式 (备用)
# ============================================================

def main_console(force_select: bool = False):
    """控制台模式（备用）"""
    print('=' * 52)
    print('  OmniSenseVoice v2.1 (Sherpa-ONNX + SenseVoice)')
    print(f' 平台: {OS_TYPE}')
    print('=' * 52)

    check_system_deps()

    config = load_config()

    # 检查是否需要向导
    model_ready, model_path, model_file = check_model_ready(config)

    if not model_ready or force_select:
        config['model_dir'] = str(APP_DATA_DIR / 'sensevoice-models')
        config['download_source'] = '1'
        config['model_choice'] = '1'
        save_config(config)

        # 下载模型
        model_dir = Path(config['model_dir'])
        model_path = model_dir / 'sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17'

        if not model_path.exists():
            print('\n[*] 需要下载 SenseVoice 模型...')
            download_model_with_progress(model_dir, config)

    # 重新检查
    model_ready, model_path, model_file = check_model_ready(config)
    if not model_ready:
        return

    selected = MODEL_OPTIONS[config['model_choice']]
    print(f'\n[*] 正在加载模型: {selected["name"]}...')
    recognizer = create_recognizer(str(model_path), model_file)
    print('[+] 模型加载完成！')

    print()
    print('┌────────────────────────────────────────────────┐')
    print('│  ✅ 系统就绪                                  │')
    print('│  🎙️ 按住 F5 或 F9 录音，松开自动粘贴文本        │')
    print('│  ❌ 退出: Ctrl+C                                │')
    print('└────────────────────────────────────────────────┘')
    print()

    def on_press(key):
        if key in (keyboard.Key.f9, keyboard.Key.f5):
            start_recording()

    def on_release(key):
        if key in (keyboard.Key.f9, keyboard.Key.f5):
            stop_recording_and_transcribe(recognizer)

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()


def download_model_with_progress(model_dir: Path, config: dict):
    """简单的下载（控制台模式）"""
    import urllib.request
    import tarfile

    model_dir.mkdir(parents=True, exist_ok=True)
    tar_file = model_dir / 'model.tar.bz2'

    # 下载源
    sources = [
        'https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2',
        'https://hf-mirror.com/k2-fsa/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17/resolve/main/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2'
    ]

    try:
        downloaded = False
        for url in sources:
            if downloaded:
                break

            try:
                print(f'\n[*] 正在下载...')

                def _progress_hook(block_num, block_size, total_size):
                    downloaded = block_num * block_size
                    if total_size > 0:
                        percent = downloaded / total_size * 100
                        print(f'\r  进度: {percent:.1f}%', end='', flush=True)

                urllib.request.urlretrieve(url, tar_file, reporthook=_progress_hook)
                downloaded = True

            except Exception:
                continue

        if not downloaded:
            raise Exception('所有下载源都失败，请检查网络')

        print('\n[*] 正在解压模型包...')
        with tarfile.open(tar_file, 'r:bz2') as tar:
            tar.extractall(model_dir)

        try:
            tar_file.unlink()
        except:
            pass

        print('[+] 模型包解压完成！')

    except KeyboardInterrupt:
        print('\n[!] 下载已取消。')
        sys.exit(0)
    except Exception as e:
        print(f'\n[错误] 下载失败: {e}')
        sys.exit(1)


# ============================================================
# GUI 模式入口
# ============================================================

def main_gui(force_select: bool = False):
    """GUI 模式"""
    import tkinter as tk
    from ui.ui.wizard import WelcomeWizard
    from ui.ui.main_window import MainWindow
    from ui.theme.tokens import get_theme

    # 创建根窗口
    root = tk.Tk()
    theme = get_theme()

    # 先隐藏，稍后根据需要显示
    root.withdraw()
    root.configure(bg=theme.colors.background)

    check_system_deps()
    config = load_config()

    # 检查模型是否准备好
    model_ready, model_path, model_file = check_model_ready(config)

    # 如果需要向导，先显示向导
    if not model_ready or force_select:
        wizard_root = tk.Toplevel(root)
        wizard_root.configure(bg=theme.colors.background)
        wizard = WelcomeWizard(wizard_root, config)
        completed = wizard.show()

        if not completed:
            root.destroy()
            return

        # 重新加载配置
        config = load_config()
        wizard_root.destroy()

    # 确保模型存在
    model_ready, model_path, model_file = check_model_ready(config)
    if not model_ready:
        root.destroy()
        return

    # 显示加载中
    loading = tk.Toplevel(root)
    loading.title('加载中')
    loading.geometry('280x120')
    loading.resizable(False, False)
    loading.overrideredirect(True)
    loading.configure(bg=theme.colors.background)

    # 居中
    loading.update_idletasks()
    w = loading.winfo_width()
    h = loading.winfo_height()
    x = (loading.winfo_screenwidth() // 2) - w // 2
    y = (loading.winfo_screenheight() // 2) - h // 2
    loading.geometry(f'{w}x{h}+{x}+{y}')

    tk.Label(loading, text='🎤', bg=theme.colors.background,
             font=(theme.typography.font_family, 40)).pack(pady=(15, 5))
    tk.Label(loading, text='正在加载模型...',
            bg=theme.colors.background, fg=theme.colors.text_secondary,
            font=(theme.typography.font_family, theme.typography.size_base)).pack()
    loading.update()

    # 加载模型
    selected = MODEL_OPTIONS[config['model_choice']]
    try:
        recognizer = create_recognizer(str(model_path), model_file)
    except Exception as e:
        loading.destroy()
        root.destroy()
        from tkinter import messagebox
        messagebox.showerror('错误', f'模型加载失败：\n{e}')
        return

    loading.destroy()
    root.deiconify()

    # 创建主窗口
    main_win = MainWindow(root)
    main_win.set_recognizer(recognizer)

    # 设置键盘监听
    def on_press(key):
        if key in (keyboard.Key.f9, keyboard.Key.f5):
            main_win.set_status_recording()
            start_recording()

    def on_release(key):
        if key in (keyboard.Key.f9, keyboard.Key.f5):
            main_win.set_status_processing()

            def on_result(text):
                main_win.add_result(text)
                main_win.set_status_ready()

            stop_recording_and_transcribe(recognizer, on_result)
            if not IS_RECORDING:
                main_win.set_status_ready()

    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()

    # 运行
    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        listener.stop()


# ============================================================
# 主入口
# ============================================================

def main():
    """主入口"""
    force_select = '--select' in sys.argv
    use_console = '--console' in sys.argv

    # 尝试 GUI 模式（Windows 直接用 GUI，其他平台试 GUI 失败回退控制台）
    if not use_console:
        try:
            main_gui(force_select=force_select)
            return
        except Exception as e:
            print(f'GUI 模式不可用，回退到控制台模式: {e}')
            import traceback
            traceback.print_exc()

    # 控制台模式
    main_console(force_select=force_select)


if __name__ == '__main__':
    main()
