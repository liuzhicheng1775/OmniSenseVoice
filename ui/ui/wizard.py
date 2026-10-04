#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
首次启动向导 - 现代设计
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox
from typing import Dict, Any
from pathlib import Path
import threading
import time
import urllib.request
import tarfile

from ui.theme.tokens import get_theme
from ui.ui.components import (
    TitleBar, ProgressBar, OptionCard
)

# 模型包名
MODEL_SUBDIR = 'sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17'


def get_app_data_dir() -> Path:
    """获取应用数据目录"""
    OS_TYPE = sys.platform
    if OS_TYPE == 'win32':
        base = os.environ.get('APPDATA') or os.path.expanduser('~')
        return Path(base) / 'OmniSenseVoice'
    elif OS_TYPE == 'darwin':
        return Path.home() / 'Library' / 'Application Support' / 'OmniSenseVoice'
    else:
        return Path.home() / '.OmniSenseVoice'


# 下载源
DOWNLOAD_SOURCES = [
    {
        'name': 'GitHub (官方源)',
        'url': 'https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2',
    },
    {
        'name': 'HuggingFace 镜像',
        'url': 'https://hf-mirror.com/k2-fsa/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17/resolve/main/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2',
    },
]


class WelcomeStep:
    """欢迎页"""

    def __init__(self, wizard):
        self.wizard = wizard
        self.frame = None

    def build(self, parent):
        theme = get_theme()
        frame = tk.Frame(parent, bg=theme.colors.background)
        self.frame = frame

        # 大图标
        tk.Label(frame, text='🎤', bg=theme.colors.background,
                 font=(theme.typography.font_family, 56)).pack(pady=(60, 20))

        # 标题
        tk.Label(frame, text='OmniSenseVoice',
                bg=theme.colors.background, fg=theme.colors.text_primary,
                font=(theme.typography.font_family, 22, 'bold')).pack(pady=(0, 8))

        # 副标题
        tk.Label(frame, text='本地离线语音输入工具',
                bg=theme.colors.background, fg=theme.colors.text_secondary,
                font=(theme.typography.font_family, 13)).pack(pady=(0, 30))

        # 功能点
        features = [
            '🔒  完全本地运行，保护隐私',
            '⚡  响应极快，无需联网',
            '🌍  支持中英日韩粤多语言',
            '📝  一键语音转文字，自动粘贴'
        ]

        for feature in features:
            tk.Label(frame, text=feature,
                    bg=theme.colors.background, fg=theme.colors.text_secondary,
                    font=(theme.typography.font_family, 12)).pack(pady=3)


class ModelChoiceStep:
    """模型选择页"""

    def __init__(self, wizard):
        self.wizard = wizard
        self.frame = None
        self._model_choice = '1'
        self._card_int8 = None
        self._card_full = None

    def build(self, parent):
        theme = get_theme()
        frame = tk.Frame(parent, bg=theme.colors.background)
        self.frame = frame

        # Int8 模型
        self._card_int8 = OptionCard(
            frame,
            title='Int8 量化版 (推荐)',
            desc='约 230MB，精度几乎无损，加载和运行更快',
            icon='⚡',
            selected=True,
            command=lambda: self._select('1')
        )
        self._card_int8.pack(fill='x', pady=(20, 8), padx=4)

        # 原版模型
        self._card_full = OptionCard(
            frame,
            title='原版精度',
            desc='约 900MB，最高精度，内存占用较大',
            icon='🎯',
            selected=False,
            command=lambda: self._select('2')
        )
        self._card_full.pack(fill='x', pady=(8, 0), padx=4)

    def _select(self, choice: str):
        self._model_choice = choice
        if self._card_int8:
            self._card_int8.set_selected(choice == '1')
        if self._card_full:
            self._card_full.set_selected(choice == '2')

    def on_next(self):
        self.wizard.config['model_choice'] = self._model_choice
        return True


class DownloadStep:
    """下载页"""

    def __init__(self, wizard):
        self.wizard = wizard
        self.frame = None
        self._started = False
        self._success = False
        self._error = None
        self._status_label = None
        self._detail_label = None
        self._progress = None

    def build(self, parent):
        theme = get_theme()
        frame = tk.Frame(parent, bg=theme.colors.background)
        self.frame = frame

        # 下载图标
        tk.Label(frame, text='📥', bg=theme.colors.background,
                 font=(theme.typography.font_family, 42)).pack(pady=(50, 16))

        # 状态文字
        self._status_label = tk.Label(frame, text='准备开始下载...',
                                     bg=theme.colors.background, fg=theme.colors.text_primary,
                                     font=(theme.typography.font_family, 14))
        self._status_label.pack(pady=(0, 16))

        # 进度条
        self._progress = ProgressBar(frame, show_percent=True)
        self._progress.pack(fill='x', padx=20, pady=(0, 8))

        # 详情文字
        self._detail_label = tk.Label(frame, text='',
                                     bg=theme.colors.background, fg=theme.colors.text_secondary,
                                     font=(theme.typography.font_family, 11))
        self._detail_label.pack()

    def start_download(self):
        """开始下载"""
        if self._started:
            return
        self._started = True

        # 设置默认配置
        self.wizard.config['model_dir'] = str(get_app_data_dir() / 'sensevoice-models')

        from main import save_config
        save_config(self.wizard.config)

        # 开始下载线程
        thread = threading.Thread(target=self._do_download, daemon=True)
        thread.start()

    def _do_download(self):
        """执行下载"""
        try:
            model_dir = Path(self.wizard.config['model_dir'])
            model_dir.mkdir(parents=True, exist_ok=True)
            tar_file = model_dir / 'model.tar.bz2'

            self.wizard.root.after(0, lambda: self._status_label.config(text='正在下载模型...'))

            # 尝试多个源
            downloaded = False
            last_error = None

            for source in DOWNLOAD_SOURCES:
                if downloaded:
                    break

                try:
                    url = source['url']
                    self.wizard.root.after(0, lambda n=source['name']: self._detail_label.config(text=f'下载源: {n}'))

                    req = urllib.request.Request(url, headers={'User-Agent': 'OmniSenseVoice/2.1'})
                    with urllib.request.urlopen(req, timeout=60) as resp:
                        total_size = int(resp.headers.get('Content-Length', 0))
                        downloaded_bytes = 0
                        start_time = time.time()

                        with open(tar_file, 'wb') as f:
                            while True:
                                chunk = resp.read(256 * 1024)
                                if not chunk:
                                    break

                                f.write(chunk)
                                downloaded_bytes += len(chunk)

                                if total_size > 0:
                                    progress = downloaded_bytes / total_size * 100
                                    speed = downloaded_bytes / 1024 / 1024 / max(0.001, time.time() - start_time)
                                    self.wizard.root.after(0, lambda p=progress, d=downloaded_bytes, t=total_size, s=speed:
                                        (self._progress.set_value(p),
                                         self._detail_label.config(text=f'{d/1024/1024:.1f} / {t/1024/1024:.1f} MB  |  {s:.1f} MB/s')))

                    downloaded = True

                except Exception as e:
                    last_error = e
                    continue

            if not downloaded:
                raise Exception(f'下载失败，请检查网络: {last_error}')

            # 解压
            self.wizard.root.after(0, lambda: self._status_label.config(text='正在解压模型...'))
            self.wizard.root.after(0, lambda: self._progress.set_value(100))
            self.wizard.root.after(0, lambda: self._detail_label.config(text='请稍候...'))

            with tarfile.open(tar_file, 'r:bz2') as tar:
                tar.extractall(model_dir)

            try:
                tar_file.unlink()
            except:
                pass

            self._success = True
            self.wizard.root.after(0, self.wizard._download_complete)

        except Exception as e:
            self._error = str(e)
            self.wizard.root.after(0, lambda: messagebox.showerror('下载失败', f'下载出错：\n{e}\n\n请检查网络后重试。'))
            self.wizard.root.after(0, lambda: self._status_label.config(text='下载失败'))


class CompleteStep:
    """完成页"""

    def __init__(self, wizard):
        self.wizard = wizard
        self.frame = None

    def build(self, parent):
        theme = get_theme()
        frame = tk.Frame(parent, bg=theme.colors.background)
        self.frame = frame

        # 成功图标
        tk.Label(frame, text='🎉', bg=theme.colors.background,
                 font=(theme.typography.font_family, 42)).pack(pady=(50, 16))

        # 标题
        tk.Label(frame, text='设置完成',
                bg=theme.colors.background, fg=theme.colors.text_primary,
                font=(theme.typography.font_family, 22, 'bold')).pack(pady=(0, 16))

        # 使用说明
        tips = [
            '•  按住 F5 或 F9 开始录音',
            '•  松开按键自动识别',
            '•  识别结果自动粘贴到光标位置'
        ]

        for tip in tips:
            tk.Label(frame, text=tip,
                    bg=theme.colors.background, fg=theme.colors.text_secondary,
                    font=(theme.typography.font_family, 12)).pack(pady=3)


class WelcomeWizard:
    """首次启动向导"""

    def __init__(self, root: tk.Tk, config: Dict[str, Any]):
        self.root = root
        self.config = config
        self._finished = False

        # 创建步骤
        self._welcome_step = WelcomeStep(self)
        self._model_step = ModelChoiceStep(self)
        self._download_step = DownloadStep(self)
        self._complete_step = CompleteStep(self)

        self._steps = [
            self._welcome_step,
            self._model_step,
            self._download_step,
            self._complete_step,
        ]
        self._current_step_idx = 0

        self._setup_window()
        self._setup_ui()

    @property
    def finished(self) -> bool:
        return self._finished

    def _setup_window(self):
        theme = get_theme()

        self.root.title('OmniSenseVoice - 欢迎')
        self.root.geometry('420x560')
        self.root.resizable(False, False)
        self.root.configure(bg=theme.colors.background)

        self._center_window()

    def _center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def _setup_ui(self):
        theme = get_theme()

        main_frame = tk.Frame(self.root, bg=theme.colors.background)
        main_frame.pack(fill='both', expand=True)

        # 标题栏
        TitleBar(main_frame, title='OmniSenseVoice',
                show_minimize=False, show_close=True,
                on_close=self._on_close).pack(fill='x')

        # 进度指示器
        progress_frame = tk.Frame(main_frame, bg=theme.colors.background, pady=16)
        progress_frame.pack(fill='x')

        self._dots = []
        for i in range(len(self._steps)):
            dot = tk.Canvas(progress_frame, width=24, height=24,
                          highlightthickness=0, bg=theme.colors.background)
            dot.pack(side='left', padx=8)
            self._dots.append(dot)

            if i < len(self._steps) - 1:
                tk.Frame(progress_frame, width=60, height=2,
                        bg=theme.colors.border).pack(side='left', padx=4)

        self._update_progress_dots()

        # 内容区域
        self._content_frame = tk.Frame(main_frame, bg=theme.colors.background)
        self._content_frame.pack(fill='both', expand=True, padx=20)

        # 按钮区域
        button_frame = tk.Frame(main_frame, bg=theme.colors.background,
                               padx=20, pady=20)
        button_frame.pack(fill='x', side='bottom')

        self._prev_btn = tk.Button(
            button_frame, text='上一步',
            bg=theme.colors.background_card,
            fg=theme.colors.text_primary,
            font=(theme.typography.font_family, 12, 'bold'),
            relief='flat', padx=20, pady=8,
            cursor='hand2', command=self._on_prev
        )
        self._prev_btn.pack(side='left')

        self._next_btn = tk.Button(
            button_frame, text='开始',
            bg=theme.colors.brand_primary,
            fg='white',
            font=(theme.typography.font_family, 12, 'bold'),
            relief='flat', padx=20, pady=8,
            cursor='hand2', command=self._on_next
        )
        self._next_btn.pack(side='right')

        # 按钮悬停效果
        self._bind_button_hover(self._prev_btn,
                               theme.colors.background_card,
                               theme.colors.background_card_hover)
        self._bind_button_hover(self._next_btn,
                               theme.colors.brand_primary,
                               '#5568d3')

        # 显示第一步
        self._show_current_step()

    def _bind_button_hover(self, btn, normal_bg, hover_bg):
        def on_enter(e):
            btn.config(bg=hover_bg)
        def on_leave(e):
            btn.config(bg=normal_bg)
        btn.bind('<Enter>', on_enter)
        btn.bind('<Leave>', on_leave)

    def _update_progress_dots(self):
        theme = get_theme()
        for i, dot in enumerate(self._dots):
            dot.delete('all')
            if i < self._current_step_idx:
                dot.create_oval(2, 2, 22, 22, fill=theme.colors.brand_primary, outline='')
                dot.create_text(12, 12, text='✓', fill='white',
                               font=(theme.typography.font_family, 10, 'bold'))
            elif i == self._current_step_idx:
                dot.create_oval(2, 2, 22, 22, fill=theme.colors.brand_primary, outline='')
                dot.create_text(12, 12, text=str(i + 1), fill='white',
                               font=(theme.typography.font_family, 11, 'bold'))
            else:
                dot.create_oval(2, 2, 22, 22, fill='', outline=theme.colors.border, width=2)
                dot.create_text(12, 12, text=str(i + 1), fill=theme.colors.text_secondary,
                               font=(theme.typography.font_family, 11))

    def _show_current_step(self):
        theme = get_theme()

        for widget in self._content_frame.winfo_children():
            widget.destroy()

        step = self._steps[self._current_step_idx]
        step.build(self._content_frame)

        # 更新按钮
        self._update_buttons()

    def _update_buttons(self):
        theme = get_theme()

        if self._current_step_idx == 0:
            self._prev_btn.pack_forget()
        else:
            self._prev_btn.pack(side='left')

        if self._current_step_idx == len(self._steps) - 1:
            self._next_btn.config(text='开始使用', command=self._on_complete)
        elif self._current_step_idx == 2:  # 下载步骤
            self._next_btn.config(text='开始下载', command=self._start_download)
        else:
            self._next_btn.config(text='下一步', command=self._on_next)

        self._update_progress_dots()

    def _on_prev(self):
        if self._current_step_idx > 0:
            self._current_step_idx -= 1
            self._show_current_step()

    def _on_next(self):
        step = self._steps[self._current_step_idx]

        if hasattr(step, 'on_next'):
            if not step.on_next():
                return

        if self._current_step_idx < len(self._steps) - 1:
            self._current_step_idx += 1
            self._show_current_step()

    def _start_download(self):
        """开始下载"""
        step = self._model_step
        step.on_next()

        self._prev_btn.config(state='disabled')
        self._next_btn.config(state='disabled')
        self._download_step.start_download()

    def _download_complete(self):
        """下载完成"""
        self._current_step_idx += 1
        self._prev_btn.config(state='normal')
        self._next_btn.config(state='normal')
        self._show_current_step()

    def _on_complete(self):
        """完成设置"""
        self._finished = True
        self.root.destroy()

    def _on_close(self):
        """关闭窗口"""
        if messagebox.askokcancel('退出', '确定要退出设置吗？'):
            self._finished = False
            self.root.destroy()

    def show(self) -> bool:
        """显示向导"""
        self.root.mainloop()
        return self._finished
