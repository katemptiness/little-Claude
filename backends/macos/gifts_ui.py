"""macOS gifts collection window (AppKit UI)."""

import AppKit
import objc
from memory import Memory
from settings import Settings
from gift_stories import get_story
from phrases import get_language


class GiftsWindow(AppKit.NSObject):
    """An AppKit window showing the user's gift collection."""

    def init(self):
        self = objc.super(GiftsWindow, self).init()
        if self is None:
            return None
        self.window = None
        return self

    def show(self):
        if self.window and self.window.isVisible():
            self.window.makeKeyAndOrderFront_(None)
            return

        ru = get_language() == "ru"
        gifts = Memory.shared().get_collected_gifts()
        user_name = Settings.shared().user_name or ""

        title = "Подарки" if ru else "Gifts"
        w = 360
        h = 460

        self.window = AppKit.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            ((200, 200), (w, h)),
            AppKit.NSWindowStyleMaskTitled
            | AppKit.NSWindowStyleMaskClosable
            | AppKit.NSWindowStyleMaskResizable,
            AppKit.NSBackingStoreBuffered,
            False,
        )
        self.window.setReleasedWhenClosed_(False)
        self.window.setTitle_(title)
        self.window.setMinSize_((320, 300))
        self.window.center()

        # --- Scroll view with flipped document ---
        scroll = AppKit.NSScrollView.alloc().initWithFrame_(
            ((0, 0), (w, h)))
        scroll.setHasVerticalScroller_(True)
        scroll.setHasHorizontalScroller_(False)
        scroll.setAutoresizingMask_(
            AppKit.NSViewWidthSizable | AppKit.NSViewHeightSizable)

        doc = _FlippedView.alloc().initWithFrame_(((0, 0), (w, 0)))
        doc.setAutoresizingMask_(AppKit.NSViewWidthSizable)
        y = 16  # top padding (flipped coords: y goes downward)

        # Header: gift count
        count = len(gifts)
        if ru:
            header_text = f"  {count} {_pluralize_ru(count)}"
        else:
            header_text = f"  {count} gift{'s' if count != 1 else ''} collected"

        header = _make_label(header_text, 16, y, w - 32, bold=True, size=16)
        doc.addSubview_(header)
        y += 32

        # Separator line
        sep = AppKit.NSBox.alloc().initWithFrame_(((16, y), (w - 32, 1)))
        sep.setBoxType_(AppKit.NSBoxSeparator)
        doc.addSubview_(sep)
        y += 12

        if not gifts:
            empty_text = ("Пока нет подарков. Скоро найду что-нибудь!" if ru
                          else "No gifts yet. I'll find something soon!")
            empty = _make_label(empty_text, 16, y + 20, w - 32, size=13, alpha=0.5)
            doc.addSubview_(empty)
            y += 80
        else:
            for i, gift in enumerate(gifts):
                y = self._add_gift_row(doc, gift, user_name, ru, y, w)
                if i < len(gifts) - 1:
                    sep = AppKit.NSBox.alloc().initWithFrame_(
                        ((20, y), (w - 40, 1)))
                    sep.setBoxType_(AppKit.NSBoxSeparator)
                    doc.addSubview_(sep)
                    y += 8

        y += 16  # bottom padding
        doc.setFrameSize_((w, max(y, h)))
        scroll.setDocumentView_(doc)
        self.window.setContentView_(scroll)
        self.window.makeKeyAndOrderFront_(None)
        AppKit.NSApp.activateIgnoringOtherApps_(True)

    def _add_gift_row(self, parent, gift, user_name, ru, y, w):
        """Add a gift row to the document view. Returns new y position."""
        # Emoji
        emoji_label = _make_label(gift["emoji"], 16, y, 30, size=20)
        parent.addSubview_(emoji_label)

        # Type name
        type_name = _gift_type_name(gift.get("type", ""), ru)
        type_label = _make_label(type_name, 48, y + 2, 150, bold=True, size=13)
        parent.addSubview_(type_label)

        # Date
        date_text = _format_date(gift.get("date", ""), ru)
        date_label = _make_label(date_text, w - 120, y + 3, 100, size=11, alpha=0.5)
        date_label.setAlignment_(AppKit.NSTextAlignmentRight)
        parent.addSubview_(date_label)

        y += 28

        # Story text (wrapping)
        story_id = gift.get("story_id", 0)
        story_text = get_story(gift.get("type", "fish"), story_id, name=user_name)

        story_label = _make_label(story_text, 20, y, w - 44, size=12, alpha=0.7)
        # Calculate height needed for wrapping text
        text_storage = AppKit.NSTextStorage.alloc().initWithString_attributes_(
            story_text, {AppKit.NSFontAttributeName: AppKit.NSFont.systemFontOfSize_(12)})
        layout = AppKit.NSLayoutManager.alloc().init()
        text_container = AppKit.NSTextContainer.alloc().initWithContainerSize_(
            (w - 44, 10000))
        text_container.setLineFragmentPadding_(0)
        layout.addTextContainer_(text_container)
        text_storage.addLayoutManager_(layout)
        layout.glyphRangeForTextContainer_(text_container)
        text_rect = layout.usedRectForTextContainer_(text_container)
        text_h = max(18, int(text_rect.size.height) + 4)

        story_label.setFrame_(((20, y), (w - 44, text_h)))
        parent.addSubview_(story_label)

        y += text_h + 12
        return y


# --- Helpers ---

class _FlippedView(AppKit.NSView):
    """NSView subclass with flipped coordinates (origin at top-left)."""
    def isFlipped(self):
        return True


def _make_label(text, x, y, width, bold=False, size=13, alpha=1.0):
    """Create a non-editable text field label."""
    label = AppKit.NSTextField.alloc().initWithFrame_(((x, y), (width, 20)))
    label.setStringValue_(text)
    label.setEditable_(False)
    label.setSelectable_(False)
    label.setBordered_(False)
    label.setDrawsBackground_(False)
    if bold:
        label.setFont_(AppKit.NSFont.boldSystemFontOfSize_(size))
    else:
        label.setFont_(AppKit.NSFont.systemFontOfSize_(size))
    if alpha < 1.0:
        label.setTextColor_(
            AppKit.NSColor.labelColor().colorWithAlphaComponent_(alpha))
    return label


def _gift_type_name(gift_type, ru):
    """Human-readable gift type name."""
    names = {
        "fish":  ("Улов", "Catch"),
        "magic": ("Магия", "Magic"),
        "star":  ("Звезда", "Star"),
        "shell": ("Ракушка", "Shell"),
        "test":  ("Тест", "Test"),
    }
    pair = names.get(gift_type, ("Подарок", "Gift"))
    return pair[0] if ru else pair[1]


def _format_date(date_str, ru):
    """Format ISO date string for display."""
    if not date_str:
        return ""
    try:
        parts = date_str.split("-")
        day, month, year = int(parts[2]), int(parts[1]), parts[0]
        months_ru = ["", "янв", "фев", "мар", "апр", "май", "июн",
                     "июл", "авг", "сен", "окт", "ноя", "дек"]
        months_en = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        if ru:
            return f"{day} {months_ru[month]} {year}"
        else:
            return f"{months_en[month]} {day}, {year}"
    except (IndexError, ValueError):
        return date_str


def _pluralize_ru(n):
    """Russian pluralization for 'gift'."""
    if 11 <= n % 100 <= 19:
        return "подарков собрано"
    mod = n % 10
    if mod == 1:
        return "подарок собран"
    elif 2 <= mod <= 4:
        return "подарка собрано"
    else:
        return "подарков собрано"
