#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用 UI 组件 - 现代化设计
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable, Any
from ui.theme.tokens import get_theme, Theme


class ModernButton(tk.Frame):
    """现代化按钮"""

    def __init__(self, parent, text: str = '', command: Callable = None,
                 style: str = 'primary', **kwargs):
        theme = get_theme()

        super().__init__(parent, bg=theme.colors.background, **kwargs)

        self._style = style
        self._command = command
        self._is_hovered = False

        # 颜色配置
        if style == 'primary':
            self._bg_normal = theme.colors.brand_primary
            self._fg_normal = '#ffffff'
            self._bg_hover = '#5568d3'
        elif style == 'secondary':
            self._bg_normal = theme.colors.background_card
            self._fg_normal = theme.colors.text_primary
            self._bg_hover = theme.colors.background_card_hover
        else:
            self._bg_normal = theme.colors.background_card
            self._fg_normal = theme.colors.text_secondary
            self._bg_hover = theme.colors.background_card_hover

        # 创建按钮
        self._canvas = tk.Canvas(
            self,
            height=40,
            highlightthickness=0,
            bg=self._bg_normal,
            cursor='hand2'
        )
        self._canvas.pack(fill='both', expand=True)

        self._text_id = self._canvas.create_text(
            20, 20, text=text,
            fill=self._fg_normal,
            font=(theme.typography.font_family, theme.typography.size_base, theme.typography.weight_bold),
            anchor='w'
        )

        # 绑定事件
        self._canvas.bind('<Button-1>', self._on_click)
        self._canvas.bind('<Enter>', self._on_enter)
        self._canvas.bind('<Leave>', self._on_leave)

    def _on_click(self, event):
        if self._command:
            self._command()

    def _on_enter(self, event):
        self._is_hovered = True
        self._canvas.config(bg=self._bg_hover)

    def _on_leave(self, event):
        self._is_hovered = False
        self._canvas.config(bg=self._bg_normal)


class Card(tk.Frame):
    """卡片组件"""

    def __init__(self, parent, padding: int = None, **kwargs):
        theme = get_theme()
        padding = padding or theme.spacing.lg

        super().__init__(parent, bg=theme.colors.background_card,
                         padx=padding, pady=padding, **kwargs)


class StatusIndicator(tk.Frame):
    """状态指示器 - 现代设计"""

    STATUS_READY = 'ready'
    STATUS_RECORDING = 'recording'
    STATUS_PROCESSING = 'processing'
    STATUS_WARNING = 'warning'

    def __init__(self, parent, initial_status: str = 'ready', **kwargs):
        theme = get_theme()

        super().__init__(parent, bg=theme.colors.background, **kwargs)

        self._status = initial_status
        self._animating = False

        # 状态圆点
        self._dot_canvas = tk.Canvas(
            self, width=16, height=16,
            highlightthickness=0, bg=theme.colors.background
        )
        self._dot_canvas.pack(side='left', padx=(0, theme.spacing.sm))

        # 状态文字
        self._label = tk.Label(
            self, text='系统就绪',
            bg=theme.colors.background,
            fg=theme.colors.text_secondary,
            font=(theme.typography.font_family, theme.typography.size_base)
        )
        self._label.pack(side='left')

        self._update_display()

    def _get_status_color(self):
        theme = get_theme()
        return {
            self.STATUS_READY: theme.colors.state_ready,
            self.STATUS_RECORDING: theme.colors.state_recording,
            self.STATUS_PROCESSING: theme.colors.state_processing,
            self.STATUS_WARNING: theme.colors.state_warning,
        }.get(self._status, theme.colors.text_muted)

    def _get_status_text(self):
        return {
            self.STATUS_READY: '系统就绪',
            self.STATUS_RECORDING: '正在录音',
            self.STATUS_PROCESSING: '识别中',
            self.STATUS_WARNING: '警告',
        }.get(self._status, '未知')

    def _update_display(self):
        theme = get_theme()
        color = self._get_status_color()
        text = self._get_status_text()

        # 清除并画圆
        self._dot_canvas.delete('all')
        self._dot_canvas.create_oval(2, 2, 14, 14, fill=color, outline='')
        self._label.config(text=text, fg=theme.colors.text_secondary)

    def set_status(self, status: str):
        """设置状态"""
        self._status = status
        self._update_display()

        if status == self.STATUS_RECORDING:
            self._start_pulse()
        else:
            self._stop_pulse()

    def _start_pulse(self):
        """开始脉冲动画"""
        if self._animating:
            return
        self._animating = True
        self._pulse_phase = 0
        self._pulse()

    def _stop_pulse(self):
        """停止脉冲动画"""
        self._animating = False

    def _pulse(self):
        """脉冲动画"""
        if not self._animating:
            return

        self._pulse_phase = (self._pulse_phase + 1) % 30
        scale = 1.0 + 0.4 * abs(15 - self._pulse_phase) / 15

        color = self._get_status_color()
        self._dot_canvas.delete('all')

        center = 8
        radius = 6 * scale
        # 外圈（渐变效果）
        self._dot_canvas.create_oval(
            center - radius - 2, center - radius - 2,
            center + radius + 2, center + radius + 2,
            fill='', outline=color, stipple='gray25'
        )
        # 内圈
        self._dot_canvas.create_oval(
            center - radius, center - radius,
            center + radius, center + radius,
            fill=color, outline=''
        )

        self.after(60, self._pulse)


class ProgressBar(tk.Frame):
    """进度条 - 现代设计"""

    def __init__(self, parent, show_percent: bool = True, **kwargs):
        theme = get_theme()

        super().__init__(parent, bg=theme.colors.background, **kwargs)

        self._show_percent = show_percent
        self._value = 0.0

        # 背景轨道
        self._canvas = tk.Canvas(
            self, height=8,
            highlightthickness=0,
            bg=theme.colors.background
        )
        self._canvas.pack(fill='x', pady=(theme.spacing.sm, theme.spacing.sm))

        # 百分比文字
        if show_percent:
            self._percent_label = tk.Label(
                self, text='0%',
                bg=theme.colors.background,
                fg=theme.colors.text_secondary,
                font=(theme.typography.font_family, theme.typography.size_sm)
            )
            self._percent_label.pack()

    def set_value(self, value: float):
        """设置进度 (0-100)"""
        self._value = max(0, min(100, value))
        self._draw()

    def _draw(self):
        theme = get_theme()
        self._canvas.delete('all')

        width = max(1, self._canvas.winfo_width())
        height = 8

        # 背景轨道
        self._canvas.create_rectangle(
            0, 0, width, height,
            fill='#e2e8f0', outline='', width=0
        )

        # 进度
        progress_width = (self._value / 100) * width
        if progress_width > 0:
            self._canvas.create_rectangle(
                0, 0, progress_width, height,
                fill=theme.colors.brand_primary, outline='', width=0
            )

        # 更新文字
        if self._show_percent:
            self._percent_label.config(text=f'{int(self._value)}%')


class TitleBar(tk.Frame):
    """标题栏 - 现代设计"""

    def __init__(self, parent, title: str = '',
                 on_minimize: Callable = None,
                 on_close: Callable = None,
                 on_to_tray: Callable = None,
                 **kwargs):
        theme = get_theme()

        super().__init__(parent, height=48,
                         bg=theme.colors.background_card, **kwargs)

        self._on_minimize = on_minimize
        self._on_close = on_close
        self._on_to_tray = on_to_tray

        self._drag_data = {'x': 0, 'y': 0}
        self._is_dragging = False

        # 图标
        icon_label = tk.Label(
            self, text='🎤',
            bg=theme.colors.background_card,
            font=(theme.typography.font_family, theme.typography.size_xl)
        )
        icon_label.pack(side='left', padx=(theme.spacing.lg, theme.spacing.sm))

        # 标题
        title_label = tk.Label(
            self, text=title,
            bg=theme.colors.background_card,
            fg=theme.colors.text_primary,
            font=(theme.typography.font_family, theme.typography.size_base, theme.typography.weight_bold)
        )
        title_label.pack(side='left', fill='both', expand=True)

        # 按钮容器
        buttons_frame = tk.Frame(self, bg=theme.colors.background_card)
        buttons_frame.pack(side='right', padx=(0, theme.spacing.sm))

        # 托盘按钮
        if on_to_tray:
            tray_btn = self._create_button(buttons_frame, '📥', on_to_tray, theme)
            tray_btn.pack(side='left', padx=theme.spacing.xs)

        # 最小化按钮
        if on_minimize:
            min_btn = self._create_button(buttons_frame, '−', on_minimize, theme)
            min_btn.pack(side='left', padx=theme.spacing.xs)

        # 关闭按钮
        if on_close:
            close_btn = self._create_button(buttons_frame, '✕', on_close, theme, is_close=True)
            close_btn.pack(side='left', padx=theme.spacing.xs)

        # 绑定拖动
        for widget in [self, icon_label, title_label]:
            widget.bind('<Button-1>', self._on_drag_start)
            widget.bind('<B1-Motion>', self._on_drag_motion)
            widget.bind('<ButtonRelease-1>', self._on_drag_end)

    def _create_button(self, parent, icon, command, theme, is_close=False):
        """创建标题栏按钮"""
        btn = tk.Canvas(
            parent, width=32, height=32,
            highlightthickness=0,
            bg=theme.colors.background_card,
            cursor='hand2'
        )
        btn.create_text(16, 16, text=icon,
                       font=(theme.typography.font_family, theme.typography.size_lg))

        def on_enter(event):
            if is_close:
                btn.config(bg='#ef4444')
            else:
                btn.config(bg=theme.colors.background_card_hover)

        def on_leave(event):
            btn.config(bg=theme.colors.background_card)

        def on_click(event):
            if command:
                command()

        btn.bind('<Enter>', on_enter)
        btn.bind('<Leave>', on_leave)
        btn.bind('<Button-1>', on_click)

        return btn

    def _on_drag_start(self, event):
        self._drag_data['x'] = event.x_root
        self._drag_data['y'] = event.y_root
        self._is_dragging = True

    def _on_drag_motion(self, event):
        if not self._is_dragging:
            return

        dx = event.x_root - self._drag_data['x']
        dy = event.y_root - self._drag_data['y']

        root = self.winfo_toplevel()
        x = root.winfo_x() + dx
        y = root.winfo_y() + dy
        root.geometry(f'+{x}+{y}')

        self._drag_data['x'] = event.x_root
        self._drag_data['y'] = event.y_root

    def _on_drag_end(self, event):
        self._is_dragging = False


class OptionCard(tk.Frame):
    """选项卡片 - 用于选择"""

    def __init__(self, parent, title: str, desc: str = '',
                 icon: str = '', selected: bool = False,
                 command: Callable = None, **kwargs):
        theme = get_theme()

        super().__init__(parent, bg=theme.colors.background, **kwargs)

        self._title = title
        self._desc = desc
        self._icon = icon
        self._selected = selected
        self._command = command

        # 主容器
        self._container = tk.Frame(self, bg=theme.colors.background_card,
                                    padx=theme.spacing.lg, pady=theme.spacing.lg)
        self._container.pack(fill='both', expand=True)

        # 图标
        if icon:
            icon_label = tk.Label(
                self._container, text=icon,
                bg=theme.colors.background_card,
                font=(theme.typography.font_family, theme.typography.size_2xl)
            )
            icon_label.pack(side='left', padx=(0, theme.spacing.lg))

        # 文字内容
        text_frame = tk.Frame(self._container, bg=theme.colors.background_card)
        text_frame.pack(side='left', fill='both', expand=True)

        tk.Label(
            text_frame, text=title,
            bg=theme.colors.background_card,
            fg=theme.colors.text_primary,
            font=(theme.typography.font_family, theme.typography.size_lg, theme.typography.weight_bold),
            anchor='w'
        ).pack(fill='x')

        if desc:
            tk.Label(
                text_frame, text=desc,
                bg=theme.colors.background_card,
                fg=theme.colors.text_secondary,
                font=(theme.typography.font_family, theme.typography.size_base),
                anchor='w', wraplength=280
            ).pack(fill='x', pady=(theme.spacing.xs, 0))

        # 选择指示器
        self._indicator = tk.Canvas(
            self._container, width=24, height=24,
            highlightthickness=0, bg=theme.colors.background_card
        )
        self._indicator.pack(side='right')

        self._update_indicator()

        # 绑定事件
        for widget in [self, self._container, text_frame] + text_frame.winfo_children():
            widget.bind('<Button-1>', self._on_click)
            widget.bind('<Enter>', self._on_enter)
            widget.bind('<Leave>', self._on_leave)

    def _on_click(self, event):
        if self._command:
            self._command()

    def _on_enter(self, event):
        theme = get_theme()
        self._container.config(bg=theme.colors.background_card_hover)
        for widget in self._container.winfo_children():
            widget.config(bg=theme.colors.background_card_hover)

    def _on_leave(self, event):
        theme = get_theme()
        self._container.config(bg=theme.colors.background_card)
        for widget in self._container.winfo_children():
            widget.config(bg=theme.colors.background_card)

    def _update_indicator(self):
        theme = get_theme()
        self._indicator.delete('all')

        if self._selected:
            self._indicator.create_oval(2, 2, 22, 22,
                                       fill=theme.colors.brand_primary, outline='')
            self._indicator.create_text(12, 12, text='✓', fill='white',
                                       font=(theme.typography.font_family, theme.typography.size_base, theme.typography.weight_bold))
        else:
            self._indicator.create_oval(2, 2, 22, 22,
                                       fill='', outline=theme.colors.border, width=2)

    def set_selected(self, selected: bool):
        self._selected = selected
        self._update_indicator()
