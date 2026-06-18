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


DEFAULT_CONFIG = CardConfig()
