from dataclasses import dataclass


@dataclass
class CardConfig:
    card_w: int = 144
    card_h: int = 233
    photo_size: int = 89
    badge_size: int = 89
    avatar_font: int = 34
    spacing: int = 8
    margin: int = 8
    padding: int = 8
    font_name: int = 13
    font_status: int = 13
    font_exit: int = 8
    border_radius: int = 8


PHI_COMPACT = CardConfig(
    card_w=89, card_h=144,
    photo_size=55, badge_size=55, avatar_font=21,
    spacing=4, margin=4, padding=4,
    font_name=8, font_status=8, font_exit=7,
    border_radius=4,
)

PHI_MEDIUM = CardConfig(
    card_w=144, card_h=233,
    photo_size=89, badge_size=89, avatar_font=34,
    spacing=8, margin=8, padding=8,
    font_name=13, font_status=13, font_exit=8,
    border_radius=8,
)

PHI_LARGE = CardConfig(
    card_w=233, card_h=377,
    photo_size=144, badge_size=144, avatar_font=55,
    spacing=13, margin=13, padding=13,
    font_name=21, font_status=21, font_exit=13,
    border_radius=13,
)

CARD_THEMES = {
    'compact': PHI_COMPACT,
    'medium': PHI_MEDIUM,
    'large': PHI_LARGE,
}

DEFAULT_CONFIG = PHI_MEDIUM
