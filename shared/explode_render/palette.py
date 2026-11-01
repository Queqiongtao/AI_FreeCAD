# -*- coding: utf-8 -*-
"""爆炸图配色与材质（风格 A：工业极简）。

颜色按 sRGB 0-1 给出，只用于渲染，不写回 FCStd。
`role_of()` 根据对象名把 FCStd 对象映射到材质角色。
"""

MATERIALS = {
    # 打印件
    "shell_light": {
        "color": (0.855, 0.843, 0.822),   # #DAD7D2 暖白
        "ambient": 0.34, "diffuse": 0.62, "specular": 0.14, "specular_power": 22,
        "opacity": 1.0,
    },
    "shell_dark": {
        "color": (0.280, 0.298, 0.320),   # #474C52 石墨
        "ambient": 0.40, "diffuse": 0.62, "specular": 0.18, "specular_power": 28,
        "opacity": 1.0,
    },
    # 金属紧固件
    "metal": {
        "color": (0.725, 0.745, 0.765),   # #B9BDC3 拉丝钢
        "ambient": 0.38, "diffuse": 0.54, "specular": 0.78, "specular_power": 90,
        "opacity": 1.0,
    },
    "metal_warm": {
        "color": (0.784, 0.647, 0.482),   # #C8A57B 香槟铜（备用）
        "ambient": 0.24, "diffuse": 0.62, "specular": 0.70, "specular_power": 75,
        "opacity": 1.0,
    },
    # 深色塑料与电子件
    "speaker": {
        "color": (0.122, 0.129, 0.141),   # #1F2124
        "ambient": 0.34, "diffuse": 0.62, "specular": 0.34, "specular_power": 40,
        "opacity": 1.0,
    },
    "pcb": {
        "color": (0.110, 0.125, 0.145),   # #1C2025 屏幕玻璃
        "ambient": 0.32, "diffuse": 0.55, "specular": 0.65, "specular_power": 110,
        "opacity": 1.0,
    },
    "battery": {
        "color": (0.180, 0.196, 0.220),   # #2E3238
        "ambient": 0.36, "diffuse": 0.62, "specular": 0.40, "specular_power": 55,
        "opacity": 1.0,
    },
    "cable": {
        "color": (0.200, 0.212, 0.227),   # #33363A
        "ambient": 0.36, "diffuse": 0.62, "specular": 0.42, "specular_power": 50,
        "opacity": 1.0,
    },
    "plug": {
        "color": (0.165, 0.176, 0.192),   # #2A2D31
        "ambient": 0.36, "diffuse": 0.62, "specular": 0.36, "specular_power": 45,
        "opacity": 1.0,
    },
    # 泡棉胶带
    "tape": {
        "color": (0.820, 0.575, 0.200),   # #D19333 泡棉橙
        "ambient": 0.44, "diffuse": 0.56, "specular": 0.20, "specular_power": 22,
        "opacity": 0.92,
    },
}

# 对象名关键字 → 材质角色；顺序敏感，先匹配先返回。
_RULES = [
    ("speaker_tape", "tape"),
    ("Speaker_Tape", "tape"),
    ("Speaker_Radiating", "speaker"),
    ("Speaker_Diaphragm", "speaker"),
    ("Speaker_Reference", "speaker"),
    ("Speaker", "speaker"),
    ("Battery", "battery"),
    ("Cable_Route", "cable"),
    ("USB_Plug", "plug"),
    ("Module_Reference", "pcb"),
    ("M25", "metal"),
    ("M3_Heat", "metal"),
    ("M3_Heads", "metal"),
    ("M3_Shafts", "metal"),
    ("Lock_Heads", "metal"),
    ("Lock_Shafts", "metal"),
    ("Lock_Inserts", "metal"),
    ("Original_Heads", "metal"),
    ("rear_cover", "shell_light"),
    ("Rear_Cover", "shell_light"),
    ("main_shell", "shell_dark"),
    ("Mount_Carrier", "shell_dark"),
]

FALLBACK = "shell_dark"


def role_of(name):
    """对象名 → 材质角色。"""
    for needle, role in _RULES:
        if needle.lower() in name.lower():
            return role
    return FALLBACK
