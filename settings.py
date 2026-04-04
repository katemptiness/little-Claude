"""Settings persistence and UI for Claudy."""

import json
import os
import AppKit
import objc
from phrases import set_language

SETTINGS_DIR = os.path.expanduser("~/.claudy")
SETTINGS_FILE = os.path.join(SETTINGS_DIR, "settings.json")

DEFAULTS = {
    "terminal": "Terminal",
    "schedule": "owl",
    "language": "en",
    "speech_interval": "1m",
    "user_name": "",
    "dev_mode": False,
    "gift_duration": "5m",
    "gift_limit": 3,
}

TERMINAL_OPTIONS = ["Terminal", "iTerm2", "Warp"]
LANGUAGE_OPTIONS = [("ru", "Русский"), ("en", "English")]

# Cooldown ranges in ms for each speech interval
SPEECH_COOLDOWNS = {
    "10s": (8000, 12000),
    "1m": (45000, 75000),
    "10m": (500000, 700000),
    "30m": (1500000, 2100000),
    "1h": (3000000, 4200000),
}

# Duration in seconds for each gift duration option
GIFT_DURATIONS = {
    "10s": 10, "1m": 60, "5m": 300,
    "15m": 900, "30m": 1800, "1h": 3600,
}

# Localized option lists: (key, EN title, RU title)
_SCHEDULE_OPTIONS = [
    ("owl", "Night Owl", "Сова"),
    ("lark", "Early Bird", "Жаворонок"),
]
_SPEECH_OPTIONS = [
    ("10s", "Often (10s)", "Часто (10с)"),
    ("1m", "Normal (1 min)", "Обычно (1 мин)"),
    ("10m", "Rarely (10 min)", "Редко (10 мин)"),
    ("30m", "Very rarely (30 min)", "Оч. редко (30 мин)"),
    ("1h", "Almost never (1 hr)", "Почти никогда (1 ч)"),
]
_GIFT_DURATION_OPTIONS = [
    ("10s", "10 sec", "10 сек"),
    ("1m", "1 min", "1 мин"),
    ("5m", "5 min", "5 мин"),
    ("15m", "15 min", "15 мин"),
    ("30m", "30 min", "30 мин"),
    ("1h", "1 hour", "1 час"),
]
_GIFT_LIMIT_OPTIONS = [
    (1, "1", "1"),
    (3, "3", "3"),
    (5, "5", "5"),
    (10, "10", "10"),
    (0, "Unlimited", "Безлимит"),
]

# Labels: (EN, RU)
_LABELS = {
    "terminal": ("Open Claude Code in:", "Открывать Claude Code в:"),
    "schedule": ("Schedule mode:", "Режим расписания:"),
    "language": ("Language:", "Язык / Language:"),
    "name": ("Your name:", "Ваше имя:"),
    "speech": ("Speech frequency:", "Частота фраз:"),
    "gift_dur": ("Gift duration:", "Время подарка:"),
    "gift_lim": ("Gifts per day:", "Подарков в день:"),
    "dev": ("Developer mode", "Режим разработчика"),
    "save": ("Save", "Сохранить"),
    "title": ("Claudy — Settings", "Claudy — Настройки"),
}


def _loc(options, lang):
    """Get (key, title) pairs for the current language from trilingual options."""
    idx = 1 if lang == "en" else 2
    return [(o[0], o[idx]) for o in options]


def _l(key, lang):
    """Get a label in the current language."""
    en, ru = _LABELS[key]
    return en if lang == "en" else ru


class Settings:
    """Load, save, and access settings."""

    _instance = None

    @classmethod
    def shared(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._data = dict(DEFAULTS)
        self._load()
        set_language(self._data["language"])

    def _load(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r") as f:
                    saved = json.load(f)
                for k in DEFAULTS:
                    if k in saved:
                        self._data[k] = saved[k]
            except (json.JSONDecodeError, IOError):
                pass

    def save(self):
        os.makedirs(SETTINGS_DIR, exist_ok=True)
        with open(SETTINGS_FILE, "w") as f:
            json.dump(self._data, f, indent=2)

    @property
    def terminal(self):
        return self._data["terminal"]

    @terminal.setter
    def terminal(self, value):
        self._data["terminal"] = value

    @property
    def schedule(self):
        return self._data["schedule"]

    @schedule.setter
    def schedule(self, value):
        self._data["schedule"] = value

    @property
    def language(self):
        return self._data["language"]

    @language.setter
    def language(self, value):
        self._data["language"] = value
        set_language(value)

    @property
    def speech_interval(self):
        return self._data["speech_interval"]

    @speech_interval.setter
    def speech_interval(self, value):
        self._data["speech_interval"] = value

    @property
    def user_name(self):
        return self._data.get("user_name", "")

    @user_name.setter
    def user_name(self, value):
        self._data["user_name"] = value

    @property
    def dev_mode(self):
        return self._data.get("dev_mode", False)

    @dev_mode.setter
    def dev_mode(self, value):
        self._data["dev_mode"] = value

    @property
    def gift_duration(self):
        return self._data.get("gift_duration", "5m")

    @gift_duration.setter
    def gift_duration(self, value):
        self._data["gift_duration"] = value

    @property
    def gift_limit(self):
        return self._data.get("gift_limit", 3)

    @gift_limit.setter
    def gift_limit(self, value):
        self._data["gift_limit"] = value


class SettingsWindow(AppKit.NSObject):
    """A simple settings panel."""

    def init(self):
        self = objc.super(SettingsWindow, self).init()
        if self is None:
            return None
        self.window = None
        self.settings = Settings.shared()
        self.terminal_popup = None
        self.schedule_popup = None
        self.lang_popup = None
        self.name_field = None
        self.speech_popup = None
        self.gift_dur_popup = None
        self.gift_lim_popup = None
        self.dev_check = None
        return self

    def show(self):
        if self.window and self.window.isVisible():
            self.window.makeKeyAndOrderFront_(None)
            return

        lang = self.settings.language
        w, h = 320, 580
        self.window = AppKit.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            ((200, 200), (w, h)),
            AppKit.NSWindowStyleMaskTitled
            | AppKit.NSWindowStyleMaskClosable,
            AppKit.NSBackingStoreBuffered,
            False,
        )
        self.window.setReleasedWhenClosed_(False)
        self.window.setTitle_(_l("title", lang))
        self.window.center()

        content = self.window.contentView()
        y = h - 50

        # Terminal
        self._add_label(content, _l("terminal", lang), 20, y)
        y -= 28
        self.terminal_popup = self._add_popup(
            content, TERMINAL_OPTIONS, 20, y, 270)
        idx = TERMINAL_OPTIONS.index(self.settings.terminal) \
            if self.settings.terminal in TERMINAL_OPTIONS else 0
        self.terminal_popup.selectItemAtIndex_(idx)
        y -= 40

        # Schedule
        self._add_label(content, _l("schedule", lang), 20, y)
        y -= 28
        sched = _loc(_SCHEDULE_OPTIONS, lang)
        self.schedule_popup = self._add_popup(
            content, [t for _, t in sched], 20, y, 270)
        sched_keys = [k for k, _ in sched]
        idx = sched_keys.index(self.settings.schedule) \
            if self.settings.schedule in sched_keys else 0
        self.schedule_popup.selectItemAtIndex_(idx)
        y -= 40

        # Language (always bilingual so user can find it)
        self._add_label(content, _l("language", lang), 20, y)
        y -= 28
        lang_titles = [title for _, title in LANGUAGE_OPTIONS]
        self.lang_popup = self._add_popup(
            content, lang_titles, 20, y, 270)
        lang_keys = [key for key, _ in LANGUAGE_OPTIONS]
        idx = lang_keys.index(self.settings.language) \
            if self.settings.language in lang_keys else 0
        self.lang_popup.selectItemAtIndex_(idx)
        y -= 40

        # Name
        self._add_label(content, _l("name", lang), 20, y)
        y -= 28
        self.name_field = AppKit.NSTextField.alloc().initWithFrame_(
            ((20, y), (270, 24)))
        self.name_field.setFont_(AppKit.NSFont.systemFontOfSize_(13))
        self.name_field.setStringValue_(self.settings.user_name or "")
        content.addSubview_(self.name_field)
        y -= 40

        # Speech frequency
        self._add_label(content, _l("speech", lang), 20, y)
        y -= 28
        speech = _loc(_SPEECH_OPTIONS, lang)
        self.speech_popup = self._add_popup(
            content, [t for _, t in speech], 20, y, 270)
        speech_keys = [k for k, _ in speech]
        idx = speech_keys.index(self.settings.speech_interval) \
            if self.settings.speech_interval in speech_keys else 1
        self.speech_popup.selectItemAtIndex_(idx)
        y -= 40

        # Gift duration
        self._add_label(content, _l("gift_dur", lang), 20, y)
        y -= 28
        gdur = _loc(_GIFT_DURATION_OPTIONS, lang)
        self.gift_dur_popup = self._add_popup(
            content, [t for _, t in gdur], 20, y, 270)
        gdur_keys = [k for k, _ in gdur]
        idx = gdur_keys.index(self.settings.gift_duration) \
            if self.settings.gift_duration in gdur_keys else 2
        self.gift_dur_popup.selectItemAtIndex_(idx)
        y -= 40

        # Gifts per day
        self._add_label(content, _l("gift_lim", lang), 20, y)
        y -= 28
        glim = _loc(_GIFT_LIMIT_OPTIONS, lang)
        self.gift_lim_popup = self._add_popup(
            content, [t for _, t in glim], 20, y, 270)
        glim_keys = [k for k, _ in glim]
        idx = glim_keys.index(self.settings.gift_limit) \
            if self.settings.gift_limit in glim_keys else 1
        self.gift_lim_popup.selectItemAtIndex_(idx)
        y -= 35

        # Dev mode
        self.dev_check = AppKit.NSButton.alloc().initWithFrame_(
            ((20, y), (270, 20)))
        self.dev_check.setButtonType_(AppKit.NSSwitchButton)
        self.dev_check.setTitle_(_l("dev", lang))
        self.dev_check.setFont_(AppKit.NSFont.systemFontOfSize_(12))
        self.dev_check.setState_(
            AppKit.NSControlStateValueOn if self.settings.dev_mode
            else AppKit.NSControlStateValueOff)
        content.addSubview_(self.dev_check)

        # Save
        save_btn = AppKit.NSButton.alloc().initWithFrame_(((110, 12), (100, 32)))
        save_btn.setTitle_(_l("save", lang))
        save_btn.setBezelStyle_(AppKit.NSBezelStyleRounded)
        save_btn.setTarget_(self)
        save_btn.setAction_("saveSettings:")
        content.addSubview_(save_btn)

        self.window.makeKeyAndOrderFront_(None)
        AppKit.NSApp.activateIgnoringOtherApps_(True)

    def saveSettings_(self, sender):
        self.settings.terminal = TERMINAL_OPTIONS[
            self.terminal_popup.indexOfSelectedItem()]

        sched_keys = [o[0] for o in _SCHEDULE_OPTIONS]
        self.settings.schedule = sched_keys[
            self.schedule_popup.indexOfSelectedItem()]

        lang_keys = [key for key, _ in LANGUAGE_OPTIONS]
        self.settings.language = lang_keys[
            self.lang_popup.indexOfSelectedItem()]

        self.settings.user_name = str(self.name_field.stringValue()).strip()

        speech_keys = [o[0] for o in _SPEECH_OPTIONS]
        self.settings.speech_interval = speech_keys[
            self.speech_popup.indexOfSelectedItem()]

        gdur_keys = [o[0] for o in _GIFT_DURATION_OPTIONS]
        self.settings.gift_duration = gdur_keys[
            self.gift_dur_popup.indexOfSelectedItem()]

        glim_keys = [o[0] for o in _GIFT_LIMIT_OPTIONS]
        self.settings.gift_limit = glim_keys[
            self.gift_lim_popup.indexOfSelectedItem()]

        self.settings.dev_mode = (
            self.dev_check.state() == AppKit.NSControlStateValueOn)

        self.settings.save()
        self.window.close()

    def _add_label(self, parent, text, x, y):
        label = AppKit.NSTextField.alloc().initWithFrame_(((x, y), (270, 20)))
        label.setStringValue_(text)
        label.setEditable_(False)
        label.setSelectable_(False)
        label.setBordered_(False)
        label.setDrawsBackground_(False)
        label.setFont_(AppKit.NSFont.systemFontOfSize_(13))
        parent.addSubview_(label)
        return label

    def _add_popup(self, parent, items, x, y, width):
        popup = AppKit.NSPopUpButton.alloc().initWithFrame_pullsDown_(
            ((x, y), (width, 26)), False)
        for item in items:
            popup.addItemWithTitle_(item)
        parent.addSubview_(popup)
        return popup
