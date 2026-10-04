"""The email colors are the mockup's design tokens (context/mockups.md).

The mockup defines them in OKLCH; emails need hexadecimal. These tests convert the
original values again, so a hex that drifts from the mockup fails here.
"""

import math
import re

import pytest

from agilina_api.shared.infrastructure.mail.renderer import JinjaEmailRenderer
from agilina_api.shared.infrastructure.mail.theme import DARK, LIGHT
from agilina_shared.enums import Language

# Copied from the mockup's stylesheet (:root and .dark).
LIGHT_OKLCH = {
    "background": "oklch(98.5% .005 265)",
    "foreground": "oklch(21% .035 265)",
    "card": "oklch(100% 0 0)",
    "primary": "oklch(52% .19 268)",
    "primary_foreground": "oklch(99% .005 265)",
    "muted": "oklch(95.5% .012 265)",
    "muted_foreground": "oklch(52% .03 265)",
    "border": "oklch(90.5% .012 265)",
}
DARK_OKLCH = {
    "background": "oklch(18% .028 268)",
    "foreground": "oklch(97% .008 265)",
    "card": "oklch(22.5% .032 268)",
    "primary": "oklch(68% .16 270)",
    "primary_foreground": "oklch(17% .03 268)",
    "muted": "oklch(28% .035 268)",
    "muted_foreground": "oklch(72% .025 265)",
    "border": "oklch(100% 0 0/.12)",  # white at 12 % over the card
}


def _oklch_to_rgb(value: str, over: tuple[float, ...] | None = None) -> tuple[float, ...]:
    parsed = re.match(r"oklch\(([\d.]+)%\s+([\d.]+)\s+([\d.]+)(?:/([\d.]+))?\)", value)
    assert parsed, value
    lightness, chroma, hue, alpha = parsed.groups()
    lum, c, h = float(lightness) / 100, float(chroma), math.radians(float(hue))
    a, b = c * math.cos(h), c * math.sin(h)
    l_, m_, s_ = (
        lum + 0.3963377774 * a + 0.2158037573 * b,
        lum - 0.1055613458 * a - 0.0638541728 * b,
        lum - 0.0894841775 * a - 1.2914855480 * b,
    )
    l3, m3, s3 = l_**3, m_**3, s_**3
    linear = (
        4.0767416621 * l3 - 3.3077115913 * m3 + 0.2309699292 * s3,
        -1.2684380046 * l3 + 2.6097574011 * m3 - 0.3413193965 * s3,
        -0.0041960863 * l3 - 0.7034186147 * m3 + 1.7076147010 * s3,
    )

    def gamma(x: float) -> float:
        x = min(max(x, 0.0), 1.0)
        return 12.92 * x if x <= 0.0031308 else 1.055 * x ** (1 / 2.4) - 0.055

    rgb = tuple(gamma(x) for x in linear)
    if alpha and over:
        k = float(alpha)
        rgb = tuple(k * v + (1 - k) * o for v, o in zip(rgb, over, strict=True))
    return rgb


def _hex(rgb: tuple[float, ...]) -> str:
    return "#" + "".join(f"{round(v * 255):02x}" for v in rgb)


def _luminance(color: str) -> float:
    channels = [int(color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast(foreground: str, background: str) -> float:
    lighter, darker = sorted((_luminance(foreground), _luminance(background)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


@pytest.mark.parametrize(
    ("theme", "sources"), [(LIGHT, LIGHT_OKLCH), (DARK, DARK_OKLCH)], ids=["light", "dark"]
)
def test_every_color_is_the_mockup_token_converted_to_hex(theme, sources):
    card = _oklch_to_rgb(sources["card"])
    for name, source in sources.items():
        assert theme[name] == _hex(_oklch_to_rgb(source, over=card)), name


@pytest.mark.parametrize("theme", [LIGHT, DARK], ids=["light", "dark"])
@pytest.mark.parametrize(
    ("foreground", "background"),
    [
        ("foreground", "card"),
        ("muted_foreground", "card"),
        ("muted_foreground", "muted"),
        ("foreground", "muted"),
        ("primary", "muted"),
        ("primary_foreground", "primary"),
    ],
)
def test_text_stays_readable_in_both_themes(theme, foreground, background):
    """WCAG AA asks for 4.5:1 on normal text."""
    assert _contrast(theme[foreground], theme[background]) >= 4.5


def test_the_html_uses_the_light_theme_inline_and_ships_the_dark_one_as_a_media_query():
    html = (
        JinjaEmailRenderer()
        .render("test", Language.ES, server="x:1", security="none", sender="a")
        .html_body
    )

    assert LIGHT["primary"] in html and LIGHT["background"] in html
    assert "prefers-color-scheme: dark" in html
    assert DARK["background"] in html and DARK["primary"] in html
