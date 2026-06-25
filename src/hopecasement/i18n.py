"""Lightweight localization: a flat string table keyed by id, selected by language.

Language is chosen once at startup (see run_ui) from, in order: the saved config,
the installer's recorded choice, then the system UI language. There is no in-app
switcher, so strings are looked up directly with t() when widgets are built.
"""
import ctypes
import winreg

_DEFAULT = "zh"

APP_NAME = {"zh": "来日窗笺", "en": "HopeCasement"}

# Font filename → display name. The filename is what gets stored in config, so it
# stays stable across languages; only the shown name is localized.
FONT_NAMES = {
    "zh": {"msyh.ttc": "微软雅黑", "simhei.ttf": "黑体", "simsun.ttc": "宋体",
           "simkai.ttf": "楷体", "simfang.ttf": "仿宋", "Deng.ttf": "等线"},
    "en": {"msyh.ttc": "Microsoft YaHei", "simhei.ttf": "SimHei", "simsun.ttc": "SimSun",
           "simkai.ttf": "KaiTi", "simfang.ttf": "FangSong", "Deng.ttf": "DengXian"},
}

_TR = {
    "zh": {
        # tabs / main buttons
        "tab_quotes": "句子库", "tab_images": "背景图", "tab_schedule": "换壁纸设置",
        "change_now": "立即换壁纸", "changing": "更换中…", "save": "保存设置",
        "status_saved": "✓ 已保存", "status_changed": "✓ 已更换壁纸",
        # app dialogs
        "dlg_save_failed": "保存失败",
        "dlg_schedule_failed": "计划更新失败",
        "dlg_schedule_failed_body": "设置已保存。\n换壁纸计划未能更新：\n{err}",
        "dlg_error": "出错了", "dlg_nobg": "没有背景图",
        "dlg_unsaved": "未保存的修改",
        "dlg_unsaved_body": "有未保存的修改，是否保存后退出？\n\n【是】保存并退出，【否】直接退出。",
        # quotes tab
        "q_import": "导入（.txt/.md）", "q_open_file": "打开文件",
        "q_len_hint": "建议每句少于 60 字", "q_count": "共 {n} 句",
        "q_restore": "恢复默认句子",
        "q_placeholder": "可直接输入、粘贴，或点左下角导入",
        "q_ft_textmd": "文本 / Markdown", "q_ft_all": "所有文件",
        "q_large_title": "文件较大", "q_large_body": "文件共 {n} 行，确认导入？",
        "q_import_done": "导入完成",
        "q_import_done_body": "共识别 {total} 句，新增 {new} 句，去重 {dup} 句。",
        # images tab
        "img_solid": "纯色背景", "img_add_color": "添加颜色",
        "img_image": "图片背景", "img_add_image": "添加图片", "img_change_folder": "更换文件夹",
        "img_count": "共 {n} 张",
        "img_folder_hint": "壁纸从下面文件夹随机选取，把图片放进去即可：",
        "open_folder": "打开文件夹", "delete": "删除",
        "img_pick_images": "选择背景图", "img_ft_images": "图片文件",
        "img_pick_folder": "选择图片文件夹",
        "cp_title": "添加背景颜色", "cp_recommended": "推荐配色", "cp_hex": "十六进制：",
        "cp_add": "添加", "cp_format_error": "格式错误",
        "cp_custom": "自定义颜色…", "cp_custom_title": "自定义颜色",
        "color_midnight": "深夜蓝", "color_ocean": "深洋蓝", "color_teal": "深青碧",
        "color_emerald": "深祖母绿", "color_indigo": "皇家靛紫", "color_amethyst": "深紫晶",
        "color_espresso": "深焙咖", "color_charcoal": "炭岩灰",
        # schedule tab
        "s_text_style": "文字样式", "s_reset": "恢复默认", "s_show_text": "显示文字",
        "s_size": "字号", "s_line_spacing": "行间距", "s_text_width": "文本宽度",
        "s_font": "字体", "s_font_color": "文字颜色", "s_shadow_color": "阴影颜色",
        "s_text_bg": "文字背景", "s_opacity": "不透明度", "s_align": "对齐方式",
        "align_left": "左对齐", "align_center": "居中", "align_right": "右对齐",
        "s_position": "文字位置", "s_pos_x": "横", "s_pos_y": "纵",
        "s_pos_hint": "%（左上为0）",
        "s_schedule": "换壁纸计划", "s_multi": "  （可多选）", "s_startup": "开机时换",
        "s_every": "每", "s_hours": "小时", "s_minutes": "分钟换一次",
        "s_min_hint": "（至少 1 分钟）", "s_daily": "每天", "s_daily_suffix": "换一次",
        "s_save_history": "保存每次生成的壁纸",
        "s_pick_text": "文字颜色", "s_pick_shadow": "阴影颜色", "s_pick_textbg": "文字背景颜色",
    },
    "en": {
        "tab_quotes": "Quotes", "tab_images": "Background", "tab_schedule": "Wallpaper",
        "change_now": "Change Now", "changing": "Changing…", "save": "Save",
        "status_saved": "✓ Saved", "status_changed": "✓ Wallpaper changed",
        "dlg_save_failed": "Save failed",
        "dlg_schedule_failed": "Schedule update failed",
        "dlg_schedule_failed_body": "Settings saved.\nThe schedule could not be updated:\n{err}",
        "dlg_error": "Something went wrong", "dlg_nobg": "No background",
        "dlg_unsaved": "Unsaved changes",
        "dlg_unsaved_body": "You have unsaved changes. Save before exiting?\n\n[Yes] Save and exit, [No] Exit without saving.",
        "q_import": "Import (.txt/.md)", "q_open_file": "Open file",
        "q_len_hint": "≤ 60 chars / line", "q_count": "{n} quotes",
        "q_restore": "Restore defaults",
        "q_placeholder": "Type, paste, or use Import (bottom-left)",
        "q_ft_textmd": "Text / Markdown", "q_ft_all": "All files",
        "q_large_title": "Large file", "q_large_body": "The file has {n} lines. Import anyway?",
        "q_import_done": "Import complete",
        "q_import_done_body": "Recognized {total}, added {new}, skipped {dup} duplicates.",
        "img_solid": "Solid color", "img_add_color": "Add color",
        "img_image": "Image", "img_add_image": "Add images", "img_change_folder": "Change folder",
        "img_count": "{n} images",
        "img_folder_hint": "Wallpapers are picked at random from this folder — just drop images in:",
        "open_folder": "Open folder", "delete": "Delete",
        "img_pick_images": "Choose images", "img_ft_images": "Image files",
        "img_pick_folder": "Choose image folder",
        "cp_title": "Add background color", "cp_recommended": "Recommended", "cp_hex": "Hex:",
        "cp_add": "Add", "cp_format_error": "Invalid format",
        "cp_custom": "Custom color…", "cp_custom_title": "Custom color",
        "color_midnight": "Midnight Blue", "color_ocean": "Deep Ocean", "color_teal": "Dark Teal",
        "color_emerald": "Emerald", "color_indigo": "Royal Indigo", "color_amethyst": "Amethyst",
        "color_espresso": "Espresso", "color_charcoal": "Charcoal",
        "s_text_style": "Text Style", "s_reset": "Reset", "s_show_text": "Show text",
        "s_size": "Size", "s_line_spacing": "Line spacing", "s_text_width": "Width",
        "s_font": "Font", "s_font_color": "Text color", "s_shadow_color": "Shadow color",
        "s_text_bg": "Text background", "s_opacity": "Opacity", "s_align": "Alignment",
        "align_left": "Left", "align_center": "Center", "align_right": "Right",
        "s_position": "Position", "s_pos_x": "X", "s_pos_y": "Y",
        "s_pos_hint": "% (top-left = 0)",
        "s_schedule": "Change Schedule", "s_multi": "  (multiple)", "s_startup": "On startup",
        "s_every": "Every", "s_hours": "h", "s_minutes": "min",
        "s_min_hint": "(at least 1 min)", "s_daily": "Daily at", "s_daily_suffix": "",
        "s_save_history": "Save each generated wallpaper",
        "s_pick_text": "Text color", "s_pick_shadow": "Shadow color", "s_pick_textbg": "Text background color",
    },
}

_lang = _DEFAULT


def set_language(lang: str) -> None:
    global _lang
    _lang = lang if lang in _TR else _DEFAULT


def get_language() -> str:
    return _lang


def t(key: str) -> str:
    table = _TR.get(_lang, _TR[_DEFAULT])
    if key in table:  # an explicit "" is a valid translation, not a miss
        return table[key]
    return _TR[_DEFAULT].get(key, key)


def app_name() -> str:
    return APP_NAME.get(_lang, APP_NAME[_DEFAULT])


def quote_count(n: int) -> str:
    if _lang == "en":
        return f"{n} quote" if n == 1 else f"{n} quotes"
    return t("q_count").format(n=n)


def font_name(font_file: str) -> str:
    return FONT_NAMES.get(_lang, FONT_NAMES[_DEFAULT]).get(font_file, font_file)


def system_language() -> str:
    """'zh' if the Windows UI language is Chinese, else 'en'."""
    try:
        if (ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0xFF) == 0x04:  # LANG_CHINESE
            return "zh"
    except Exception:
        pass
    return "en"


def installer_language() -> str:
    """Language the installer recorded under HKCU, or '' if none/not installed."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\HopeCasement") as key:
            value, _ = winreg.QueryValueEx(key, "Language")
        return value if value in _TR else ""
    except OSError:
        return ""
