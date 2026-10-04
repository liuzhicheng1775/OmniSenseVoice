#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Design Tokens - 设计令牌系统
"""

import tkinter as tk

# 品牌渐变
BRAND_GRADIENT = {
    'from': '#667eea',
    'to': '#764ba2',
    'accent': '#00d2ff',
}


class ThemeColors:
    """主题颜色"""

    def __init__(self, is_dark: bool = False):
        self.is_dark = is_dark

    @property
    def background(self):
        """背景色"""
        if self.is_dark:
            return '#0f172a'  # 深蓝灰
        return '#ffffff'  # 纯白

    @property
    def background_card(self):
        """卡片背景（半透明）"""
        if self.is_dark:
            return '#1e293b'
        return '#f8fafc'

    @property
    def background_card_hover(self):
        """卡片悬停"""
        if self.is_dark:
            return '#334155'
        return '#e2e8f0'

    @property
    def text_primary(self):
        """主要文字"""
        if self.is_dark:
            return '#f1f5f9'
        return '#1e293b'

    @property
    def text_secondary(self):
        """次要文字"""
        if self.is_dark:
            return '#94a3b8'
        return '#64748b'

    @property
    def text_muted(self):
        """辅助文字"""
        if self.is_dark:
            return '#64748b'
        return '#94a3b8'

    @property
    def text_inverse(self):
        """反色文字"""
        if self.is_dark:
            return '#0f172a'
        return '#ffffff'

    @property
    def state_ready(self):
        """就绪状态：绿色"""
        return '#22c55e'

    @property
    def state_recording(self):
        """录音状态：红色"""
        return '#ef4444'

    @property
    def state_processing(self):
        """处理中：蓝色"""
        return '#3b82f6'

    @property
    def state_warning(self):
        """警告：橙色"""
        return '#f59e0b'

    @property
    def border(self):
        """边框色"""
        if self.is_dark:
            return '#334155'
        return '#e2e8f0'

    @property
    def border_focus(self):
        """聚焦边框"""
        return '#667eea'

    @property
    def brand_primary(self):
        """品牌主色"""
        return '#667eea'

    @property
    def brand_secondary(self):
        """品牌辅色"""
        return '#764ba2'


class ThemeTypography:
    """排版系统"""

    @property
    def font_family(self):
        """字体族"""
        import platform
        system = platform.system()
        if system == 'Windows':
            return ('Segoe UI', 'Microsoft YaHei UI', 'Microsoft YaHei', 'sans-serif')
        elif system == 'Darwin':
            return ('SF Pro Display', 'PingFang SC', 'Helvetica Neue', 'sans-serif')
        return ('system-ui', 'sans-serif')

    @property
    def size_xs(self):
        return 10

    @property
    def size_sm(self):
        return 11

    @property
    def size_base(self):
        return 13

    @property
    def size_lg(self):
        return 14

    @property
    def size_xl(self):
        return 18

    @property
    def size_2xl(self):
        return 24

    @property
    def weight_normal(self):
        return 'normal'

    @property
    def weight_bold(self):
        return 'bold'


class ThemeSpacing:
    """间距系统"""

    @property
    def xs(self):
        return 4

    @property
    def sm(self):
        return 8

    @property
    def md(self):
        return 12

    @property
    def lg(self):
        return 16

    @property
    def xl(self):
        return 20

    @property
    def xxl(self):
        return 28


class ThemeBorderRadius:
    """圆角系统"""

    @property
    def sm(self):
        return 6

    @property
    def md(self):
        return 10

    @property
    def lg(self):
        return 16

    @property
    def xl(self):
        return 24

    @property
    def full(self):
        return 9999


class Theme:
    """完整主题"""

    def __init__(self, is_dark: bool = False):
        self.is_dark = is_dark
        self.colors = ThemeColors(is_dark)
        self.typography = ThemeTypography()
        self.spacing = ThemeSpacing()
        self.border_radius = ThemeBorderRadius()

    def toggle(self):
        """切换明暗主题"""
        return Theme(not self.is_dark)


# 默认主题
_current_theme = Theme(is_dark=False)


def get_theme() -> Theme:
    """获取当前主题"""
    return _current_theme


def set_theme(theme: Theme):
    """设置当前主题"""
    global _current_theme
    _current_theme = theme


def toggle_theme() -> Theme:
    """切换主题"""
    global _current_theme
    _current_theme = _current_theme.toggle()
    return _current_theme
