#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口 - 现代设计
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable, Any, Dict
from pathlib import Path

from ui.theme.tokens import get_theme
from ui.ui.components import (
    TitleBar, StatusIndicator
)
from ui.ui.visualizer import WaveformVisualizer


class MainWindow:
    """主窗口 - 现代简洁设计"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self._recognizer = None
        self._recent_results = []

        self._setup_window()
        self._setup_ui()

    def _setup_window(self):
        theme = get_theme()

        self.root.title('OmniSenseVoice')
        self.root.geometry('360x480')
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
        title_bar = TitleBar(main_frame, title='OmniSenseVoice',
                             on_minimize=self._on_minimize,
                             on_to_tray=self._on_to_tray,
                             on_close=self._on_close)
        title_bar.pack(fill='x')

        # 内容区
        content = tk.Frame(main_frame, bg=theme.colors.background)
        content.pack(fill='both', expand=True, padx=theme.spacing.lg, pady=theme.spacing.lg)

        # 状态卡片
        status_card = tk.Frame(content, bg=theme.colors.background_card,
                               padx=theme.spacing.lg, pady=theme.spacing.lg)
        status_card.pack(fill='x', pady=(0, theme.spacing.md))

        # 大状态图标
        self._status_icon = tk.Label(
            status_card, text='🎙️',
            bg=theme.colors.background_card,
            font=(theme.typography.font_family, 48)
        )
        self._status_icon.pack(pady=(0, theme.spacing.sm))

        # 状态文字
        self._status_text = tk.Label(
            status_card, text='系统就绪',
            bg=theme.colors.background_card,
            fg=theme.colors.text_primary,
            font=(theme.typography.font_family, theme.typography.size_lg, theme.typography.weight_bold)
        )
        self._status_text.pack(pady=(0, theme.spacing.xs))

        # 提示文字
        self._hint_text = tk.Label(
            status_card, text='按住 F5 或 F9 开始录音',
            bg=theme.colors.background_card,
            fg=theme.colors.text_secondary,
            font=(theme.typography.font_family, theme.typography.size_base)
        )
        self._hint_text.pack()

        # 状态指示器（小圆点）
        status_bar = tk.Frame(status_card, bg=theme.colors.background_card)
        status_bar.pack(pady=(theme.spacing.sm, 0))

        self._status_indicator = StatusIndicator(status_bar, initial_status='ready')
        self._status_indicator.pack()

        # 可视化区域卡片
        visual_card = tk.Frame(content, bg=theme.colors.background_card,
                               padx=theme.spacing.lg, pady=theme.spacing.lg)
        visual_card.pack(fill='x', pady=(0, theme.spacing.md))

        tk.Label(
            visual_card, text='实时可视化',
            bg=theme.colors.background_card,
            fg=theme.colors.text_secondary,
            font=(theme.typography.font_family, theme.typography.size_sm)
        ).pack(anchor='w', pady=(0, theme.spacing.sm))

        self._visualizer = WaveformVisualizer(visual_card, height=70)
        self._visualizer.pack(fill='x')

        # 最近识别结果卡片
        recent_card = tk.Frame(content, bg=theme.colors.background_card,
                              padx=theme.spacing.lg, pady=theme.spacing.lg)
        recent_card.pack(fill='both', expand=True)

        tk.Label(
            recent_card, text='最近识别',
            bg=theme.colors.background_card,
            fg=theme.colors.text_secondary,
            font=(theme.typography.font_family, theme.typography.size_sm)
        ).pack(anchor='w', pady=(0, theme.spacing.sm))

        # 最近结果文本
        self._recent_text = tk.Text(
            recent_card, height=5,
            bg=theme.colors.background,
            fg=theme.colors.text_secondary,
            font=(theme.typography.font_family, theme.typography.size_base),
            relief='flat', bd=0, padx=theme.spacing.sm, pady=theme.spacing.sm,
            state='disabled', wrap=tk.WORD
        )
        self._recent_text.pack(fill='both', expand=True)

        # 底部提示
        bottom_hint = tk.Label(
            content, text='F5 / F9 录音 · 松开自动粘贴',
            bg=theme.colors.background,
            fg=theme.colors.text_muted,
            font=(theme.typography.font_family, theme.typography.size_sm)
        )
        bottom_hint.pack(pady=(theme.spacing.lg, 0))

    def set_recognizer(self, recognizer):
        """设置识别器"""
        self._recognizer = recognizer

    def set_status_ready(self):
        """设置就绪状态"""
        theme = get_theme()
        self._status_indicator.set_status(StatusIndicator.STATUS_READY)
        self._status_icon.config(text='🎙️')
        self._status_text.config(text='系统就绪', fg=theme.colors.text_primary)
        self._hint_text.config(text='按住 F5 或 F9 开始录音')
        self._visualizer.stop_recording()
        self._visualizer.stop_processing()

    def set_status_recording(self):
        """设置录音状态"""
        theme = get_theme()
        self._status_indicator.set_status(StatusIndicator.STATUS_RECORDING)
        self._status_icon.config(text='🔴')
        self._status_text.config(text='正在录音', fg=theme.colors.state_recording)
        self._hint_text.config(text='松开按键识别并粘贴')
        self._visualizer.start_recording()

    def set_status_processing(self):
        """设置处理状态"""
        theme = get_theme()
        self._status_indicator.set_status(StatusIndicator.STATUS_PROCESSING)
        self._status_icon.config(text='⚡')
        self._status_text.config(text='正在识别', fg=theme.colors.state_processing)
        self._hint_text.config(text='请稍候...')
        self._visualizer.stop_recording()
        self._visualizer.start_processing()

    def add_result(self, text: str):
        """添加识别结果"""
        if not text:
            return

        self._recent_results.insert(0, text)
        if len(self._recent_results) > 5:
            self._recent_results.pop()

        self._recent_text.config(state='normal')
        self._recent_text.delete('1.0', tk.END)
        for i, result in enumerate(self._recent_results):
            prefix = '✓ ' if i == 0 else '  '
            self._recent_text.insert(tk.END, f'{prefix}{result}\n')
        self._recent_text.config(state='disabled')

    def _on_minimize(self):
        """最小化"""
        self.root.iconify()

    def _on_to_tray(self):
        """最小化到托盘"""
        self.root.withdraw()

    def _on_close(self):
        """关闭窗口"""
        if messagebox.askokcancel('退出', '确定要退出 OmniSenseVoice 吗？'):
            self.root.quit()
            self.root.destroy()
            import os
            os._exit(0)
