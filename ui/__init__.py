"""
UI module for Frontwars
"""

from .ui_manager import UIManager
from .hud import HUD
from .menu import MainMenu, PauseMenu, GameOverMenu
from .widgets import *

__all__ = [
    'UIManager',
    'HUD',
    'MainMenu', 'PauseMenu', 'GameOverMenu'
]
