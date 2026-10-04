"""Colors and fonts of the emails: the design tokens of the interface mockups.

Source: ``context/mockups.md`` (the Lovable prototype, https://sweet-screen-dreams.lovable.app/),
whose stylesheet defines them in OKLCH. Email clients do not understand OKLCH or CSS
variables, so they are kept here already converted to hexadecimal; a test converts the
original values again and fails if one of these drifts from the mockup.

``LIGHT`` is the default look. ``DARK`` is applied by clients that honor
``prefers-color-scheme`` (Apple Mail, iOS, Outlook.com…); the others show ``LIGHT``.
"""

LIGHT = {
    "background": "#f8fafe",  # --background  oklch(98.5% .005 265)
    "foreground": "#101828",  # --foreground  oklch(21% .035 265)
    "card": "#ffffff",  # --card        oklch(100% 0 0)
    "primary": "#3b5bd4",  # --primary     oklch(52% .19 268)
    "primary_foreground": "#fafcff",  # --primary-foreground oklch(99% .005 265)
    "muted": "#ecf0f9",  # --muted       oklch(95.5% .012 265)
    "muted_foreground": "#60697b",  # --muted-foreground oklch(52% .03 265)
    "border": "#dce0e8",  # --border      oklch(90.5% .012 265)
}

DARK = {
    "background": "#0c111e",  # --background  oklch(18% .028 268)
    "foreground": "#f2f5fb",  # --foreground  oklch(97% .008 265)
    "card": "#151b2b",  # --card        oklch(22.5% .032 268)
    "primary": "#7290fa",  # --primary     oklch(68% .16 270)
    "primary_foreground": "#0a0f1d",  # --primary-foreground oklch(17% .03 268)
    "muted": "#21283a",  # --muted       oklch(28% .035 268)
    "muted_foreground": "#9da5b5",  # --muted-foreground oklch(72% .025 265)
    "border": "#313644",  # --border      oklch(100% 0 0 / .12) over the card
}

# Plus Jakarta Sans (titles) and Inter (text), as in the mockups. Email clients cannot
# download web fonts reliably, so each stack falls back to the system fonts.
_SYSTEM_FONTS = "-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"
FONTS = {
    "heading": f"'Plus Jakarta Sans','Inter',{_SYSTEM_FONTS}",
    "body": f"'Inter',{_SYSTEM_FONTS}",
}
