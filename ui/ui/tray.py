#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统托盘
"""

import tkinter as tk
import sys
import threading
from typing import Optional, Callable

# 尝试导入 pystray
try:
    import pystray
    from PIL import Image, ImageDraw
    HAS_PYSTRAY = True
except ImportError:
    HAS_PYSTRAY = False


def _create_icon():
    """创建托盘图标"""
    if HAS_PYSTRAY:
        # 创建一个简单的麦克风图标
        width, height = 64, 64
        image = Image.new('RGB', (width, height), color='#667eea')
        dc = ImageDraw.Draw(image)

        # 画麦克风（简化版）
        center_x, center_y = width // 2, height // 2

        # 麦克风圆形部分
        dc.ellipse([center_x - 16, center_y - 20, center_x + 16, center_y + 8],
                   fill='white')

        # 麦克风手柄
        dc.rectangle([center_x - 4, center_y + 8, center_x + 4, center_y + 24],
                     fill='white')

        # 底座
        dc.rectangle([center_x - 12, center_y + 24, center_x + 12, center_y + 28],
                     fill='white')

        return image
    return None


class TrayIcon:
    """托盘图标"""

    def __init__(self, root: tk.Tk,
                 on_show: Callable = None,
                 on_quit: Callable = None):
        self._root = root
        self._on_show = on_show
        self._on_quit = on_quit
        self._icon: Optional['pystray.Icon'] = None
        self._thread: Optional[threading.Thread] = None

        self._setup_menu()

    def _setup_menu(self):
        """设置菜单"""
        if not HAS_PYSTRAY:
            return

        menu = (
            pystray.MenuItem('🎤 显示', self._on_click_show),
            pystray.MenuItem('❓ 帮助', self._on_click_help),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem('✕ 退出', self._on_click_quit),
        )

        icon = _create_icon()
        if icon:
            self._icon = pystray.Icon('OmniSenseVoice', icon, 'OmniSenseVoice', menu)

    def _on_click_show(self, icon, item):
        """点击显示"""
        if self._on_show:
            self._root.after(0, self._on_show)

    def _on_click_help(self, icon, item):
        """点击帮助"""
        import tkinter.messagebox
        self._root.after(0, lambda: tkinter.messagebox.showinfo(
            '帮助',
            '按住 F5 或 F9 开始录音\n松开自动识别并粘贴'
        ))

    def _on_click_quit(self, icon, item):
        """点击退出"""
        if self._icon:
            self._icon.stop()
        if self._on_quit:
            self._root.after(0, self._on_quit)

    def start(self):
        """启动托盘图标"""
        if not HAS_PYSTRAY or not self._icon:
            return

        def _run():
            self._icon.run()

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()

    def stop(self):
        """停止托盘图标"""
        if self._icon:
            self._icon.stop()

    def notify(self, text: str):
        """显示通知"""
        if self._icon:
            self._icon.notify(text, 'OmniSenseVoice')


# 检测是否支持托盘
def is_tray_supported() -> bool:
    """检查是否支持系统托盘"""
    return HAS_PYSTRAY
