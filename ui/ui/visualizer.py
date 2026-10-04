#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
波形可视化组件 - 现代设计
"""

import tkinter as tk
import random
import math
from typing import Optional
from ui.theme.tokens import get_theme


class WaveformVisualizer(tk.Canvas):
    """波形可视化器"""

    def __init__(self, parent, height: int = 80, **kwargs):
        theme = get_theme()

        super().__init__(parent, height=height,
                         highlightthickness=0, bg=theme.colors.background, **kwargs)

        self._is_recording = False
        self._is_processing = False
        self._bars = []
        self._num_bars = 20
        self._animating = False
        self._processing_phase = 0

        self._setup_styles()

    def _setup_styles(self):
        pass

    def start_recording(self):
        """开始录音可视化"""
        self._is_recording = True
        self._is_processing = False
        self._start_animation()

    def stop_recording(self):
        """停止录音可视化"""
        self._is_recording = False
        self._stop_animation()

    def start_processing(self):
        """开始处理可视化"""
        self._is_processing = True
        self._is_recording = False
        self._processing_phase = 0
        self._start_animation()

    def stop_processing(self):
        """停止处理可视化"""
        self._is_processing = False
        self._stop_animation()

    def _start_animation(self):
        """开始动画"""
        if self._animating:
            return
        self._animating = True
        self._animate()

    def _stop_animation(self):
        """停止动画"""
        self._animating = False
        self.delete('all')

    def _animate(self):
        """动画帧"""
        if not self._animating:
            return

        if self._is_recording:
            self._draw_recording()
        elif self._is_processing:
            self._draw_processing()
        else:
            self._draw_idle()
            return

        self.after(70, self._animate)

    def _draw_recording(self):
        """画录音波形"""
        theme = get_theme()
        self.delete('all')

        width = max(1, self.winfo_width())
        height = self.winfo_height()

        bar_width = max(4, (width - 40) // self._num_bars)
        spacing = 3

        for i in range(self._num_bars):
            base_height = height * 0.25
            variance = height * 0.4
            bar_height = base_height + random.random() * variance

            # 钟形曲线效果
            center_offset = abs(i - self._num_bars // 2) / (self._num_bars // 2)
            bar_height *= 1 - center_offset * 0.5

            x = 20 + i * (bar_width + spacing)
            y_top = (height - bar_height) // 2
            y_bottom = y_top + bar_height

            self.create_rectangle(x, y_top, x + bar_width, y_bottom,
                                 fill=theme.colors.state_recording,
                                 outline='', width=0)

    def _draw_processing(self):
        """画处理中动画（三个跳动的点）"""
        theme = get_theme()
        self.delete('all')

        width = max(1, self.winfo_width())
        height = self.winfo_height()

        center_y = height // 2
        dot_size = 12
        spacing = 20
        total_width = dot_size * 3 + spacing * 2
        start_x = (width - total_width) // 2

        self._processing_phase = (self._processing_phase + 1) % 40

        for i in range(3):
            phase_offset = i * 12
            phase = (self._processing_phase + phase_offset) % 40

            y_offset = math.sin(phase / 6.36) * 10

            x = start_x + i * (dot_size + spacing)
            y = center_y + y_offset

            self.create_oval(x, y, x + dot_size, y + dot_size,
                           fill=theme.colors.state_processing,
                           outline='')

    def _draw_idle(self):
        """画闲置状态"""
        self.delete('all')
