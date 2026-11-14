"""
Configuration and constants for Frontwars game
"""

import pygame
import os
from dataclasses import dataclass, field
from typing import Dict, Tuple, List
from enum import Enum


# Game constants
GAME_NAME = "Frontwars"
GAME_VERSION = "1.0.0"

# Screen dimensions
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# Colors
class Colors:
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    YELLOW = (255, 255, 0)
    ORANGE = (255, 165, 0)
    PURPLE = (128, 0, 128)
    GRAY = (128, 128, 128)
    LIGHT_GRAY = (200, 200, 200)
    DARK_GRAY = (64, 64, 64)
    TRANSPARENT = (0, 0, 0, 0)
    
    # Team colors
    TEAM_RED = (220, 20, 60)
    TEAM_BLUE = (30, 144, 255)
    TEAM_GREEN = (34, 139, 34)
    TEAM_YELLOW = (255, 215, 0)
    TEAM_PURPLE = (138, 43, 226)
    TEAM_ORANGE = (255, 140, 0)
    
    # Map colors
    GRASS = (34, 139, 34)
    WATER = (65, 105, 225)
    MOUNTAIN = (139, 137, 137)
    FOREST = (34, 85, 34)
    SAND = (245, 222, 179)
    ROAD = (105, 105, 105)
    
    # UI colors
    UI_BACKGROUND = (40, 40, 40)
    UI_PANEL = (60, 60, 60)
    UI_BUTTON = (80, 80, 80)
    UI_BUTTON_HOVER = (100, 100, 100)
    UI_BUTTON_ACTIVE = (120, 120, 120)
    UI_TEXT = (240, 240, 240)
    UI_TEXT_DARK = (200, 200, 200)
    UI_BORDER = (150, 150, 150)
    UI_HEALTH_BAR = (255, 50, 50)
    UI_MANA_BAR = (50, 100, 255)
    UI_GOLD = (255, 215, 0)
    GOLD = (255, 215, 0)


# Game settings
class GameSettings:
    # Map settings
    MAP_WIDTH = 100
    MAP_HEIGHT = 60
    CELL_SIZE = 12
    MINIMAP_SIZE = 200
    
    # Unit settings
    UNIT_SIZE = 16
    UNIT_SPEED = 2.0
    UNIT_ROTATION_SPEED = 3.0
    
    # Camera settings
    CAMERA_SPEED = 5.0
    CAMERA_ZOOM_SPEED = 0.1
    CAMERA_MIN_ZOOM = 0.5
    CAMERA_MAX_ZOOM = 2.0
    
    # Selection settings
    SELECTION_BOX_COLOR = Colors.GREEN
    SELECTION_BOX_ALPHA = 100
    SELECTION_RADIUS = 20
    
    # Fog of war
    FOG_OF_WAR_ENABLED = True
    FOG_OF_WAR_ALPHA = 180
    
    # Pathfinding
    PATHFINDING_MAX_ITERATIONS = 1000
    PATHFINDING_MAX_PATH_LENGTH = 50
    
    # Combat
    COMBAT_DAMAGE_MULTIPLIER = 1.0
    COMBAT_ARMOR_REDUCTION = 0.5
    
    # Economy
    STARTING_GOLD = 1000
    GOLD_INCOME_RATE = 10
    GOLD_INCOME_INTERVAL = 1000  # ms
    
    # Multiplayer
    MAX_PLAYERS = 4
    NETWORK_TICK_RATE = 30
    
    # AI
    AI_DIFFICULTY = "normal"
    AI_THINK_INTERVAL = 1000  # ms


# Team configuration
class Team(Enum):
    RED = 0
    BLUE = 1
    GREEN = 2
    YELLOW = 3
    NEUTRAL = 4


@dataclass
class TeamConfig:
    name: str
    color: Tuple[int, int, int]
    start_position: Tuple[int, int] = (0, 0)
    ai_controlled: bool = False
    gold: int = GameSettings.STARTING_GOLD
    
    def __post_init__(self):
        if isinstance(self.color, str):
            self.color = getattr(Colors, self.color.upper(), Colors.WHITE)


# Default team configurations
DEFAULT_TEAMS = {
    Team.RED: TeamConfig(
        name="Red Team",
        color=Colors.TEAM_RED,
        start_position=(10, 10),
        ai_controlled=False
    ),
    Team.BLUE: TeamConfig(
        name="Blue Team", 
        color=Colors.TEAM_BLUE,
        start_position=(90, 50),
        ai_controlled=True
    ),
    Team.GREEN: TeamConfig(
        name="Green Team",
        color=Colors.TEAM_GREEN,
        start_position=(10, 50),
        ai_controlled=True
    ),
    Team.YELLOW: TeamConfig(
        name="Yellow Team",
        color=Colors.TEAM_YELLOW,
        start_position=(90, 10),
        ai_controlled=True
    ),
    Team.NEUTRAL: TeamConfig(
        name="Neutral",
        color=Colors.GRAY,
        start_position=(0, 0),
        ai_controlled=False
    )
}


# Unit types
class UnitType(Enum):
    SOLDIER = "soldier"
    TANK = "tank"
    SCOUT = "scout"
    ARTILLERY = "artillery"
    ENGINEER = "engineer"
    AIRCRAFT = "aircraft"
    HELICOPTER = "helicopter"


# Terrain types
class TerrainType(Enum):
    GRASS = "grass"
    WATER = "water"
    MOUNTAIN = "mountain"
    FOREST = "forest"
    SAND = "sand"
    ROAD = "road"
    CITY = "city"
    BASE = "base"


# Resource types
class ResourceType(Enum):
    GOLD = "gold"
    OIL = "oil"
    FOOD = "food"
    WOOD = "wood"


# Building types
class BuildingType(Enum):
    BASE = "base"
    BARRACKS = "barracks"
    FACTORY = "factory"
    TOWER = "tower"
    RESEARCH_LAB = "research_lab"
    FARM = "farm"
    MINE = "mine"


# Game difficulty levels
class Difficulty(Enum):
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"
    EXPERT = "expert"


# Control schemes
class ControlScheme(Enum):
    KEYBOARD_MOUSE = "keyboard_mouse"
    GAMEPAD = "gamepad"
    TOUCH = "touch"


# Graphics settings
class GraphicsSettings:
    FULLSCREEN = False
    VSYNC = True
    ANTI_ALIASING = True
    SHADOWS_ENABLED = True
    PARTICLE_EFFECTS_ENABLED = True
    BLOOM_ENABLED = False
    AMBIENT_OCCLUSION = False
    
    # Render distances
    UNIT_RENDER_DISTANCE = 1000
    BUILDING_RENDER_DISTANCE = 1500
    TERRAIN_RENDER_DISTANCE = 2000
    
    # Quality settings
    TEXTURE_QUALITY = "high"
    SHADOW_QUALITY = "medium"
    EFFECT_QUALITY = "high"


# Audio settings
class AudioSettings:
    MASTER_VOLUME = 0.8
    MUSIC_VOLUME = 0.7
    SFX_VOLUME = 0.8
    VOICE_VOLUME = 0.6
    
    # Audio channels
    MUSIC_CHANNELS = 1
    SFX_CHANNELS = 8
    VOICE_CHANNELS = 2


# Key bindings
KEY_BINDINGS = {
    "move_up": [pygame.K_w, pygame.K_UP],
    "move_down": [pygame.K_s, pygame.K_DOWN],
    "move_left": [pygame.K_a, pygame.K_LEFT],
    "move_right": [pygame.K_d, pygame.K_RIGHT],
    "select": [pygame.K_SPACE, pygame.MOUSEBUTTONDOWN],
    "attack": [pygame.K_a, pygame.MOUSEBUTTONDOWN],
    "build": [pygame.K_b],
    "stop": [pygame.K_s],
    "hold": [pygame.K_h],
    "move": [pygame.K_m],
    "camera_zoom_in": [pygame.K_PLUS, pygame.K_EQUALS],
    "camera_zoom_out": [pygame.K_MINUS],
    "camera_rotate_left": [pygame.K_q],
    "camera_rotate_right": [pygame.K_e],
    "toggle_minimap": [pygame.K_TAB],
    "toggle_fog": [pygame.K_f],
    "show_stats": [pygame.K_i],
    "pause": [pygame.K_ESCAPE],
    "menu": [pygame.K_ESCAPE],
    "quit": [pygame.K_ESCAPE],
}


# Mouse buttons
MOUSE_BINDINGS = {
    "select": [1],  # Left click
    "move": [1],    # Left click
    "attack": [3],  # Right click
    "build": [2],    # Middle click / Right click
    "drag": [1],     # Left click drag
    "context_menu": [3],  # Right click
}


# Path configuration
ASSETS_PATH = os.path.join(os.path.dirname(__file__), "assets")
IMAGES_PATH = os.path.join(ASSETS_PATH, "images")
SOUNDS_PATH = os.path.join(ASSETS_PATH, "sounds")
FONTS_PATH = os.path.join(ASSETS_PATH, "fonts")
SAVE_PATH = os.path.join(os.path.dirname(__file__), "saves")
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")


# Performance settings
class PerformanceSettings:
    MAX_FPS = 144
    TARGET_FPS = 60
    PHYSICS_STEPS = 2
    AI_UPDATE_INTERVAL = 500  # ms
    PATHFINDING_CACHE_SIZE = 1000
    
    # Memory limits
    TEXTURE_CACHE_LIMIT = 1000
    SOUND_CACHE_LIMIT = 500
    PARTICLE_POOL_SIZE = 1000
    
    # Threading
    USE_MULTITHREADING = True
    PATHFINDING_THREADS = 2
    AI_THREADS = 1


# Debug settings
class DebugSettings:
    SHOW_FPS = True
    SHOW_DEBUG_INFO = False
    SHOW_PATHFINDING = False
    SHOW_COLLISION_BOXES = False
    SHOW_HITBOXES = False
    SHOW_GRID = False
    SHOW_PERFORMANCE_METRICS = False
    LOG_PATHFINDING = False
    LOG_AI_DECISIONS = False
    LOG_NETWORK = False


# Network settings
class NetworkSettings:
    DEFAULT_PORT = 5555
    MAX_CONNECTIONS = 8
    TIMEOUT = 5.0
    PING_INTERVAL = 1.0
    SYNC_INTERVAL = 0.1
    MAX_LATENCY = 0.5
    
    # Protocol
    PROTOCOL_VERSION = 1
    MAGIC_NUMBER = 0x46524F4E5457415253


# Save/Load settings
class SaveSettings:
    SAVE_FORMAT = "json"
    COMPRESSION = True
    ENCRYPTION = False
    MAX_SAVE_SLOTS = 10
    AUTO_SAVE_INTERVAL = 300  # seconds


# Achievement system
ACHIEVEMENTS = [
    {"id": "first_blood", "name": "First Blood", "description": "Win your first battle"},
    {"id": "conqueror", "name": "Conqueror", "description": "Capture 100 territories"},
    {"id": "tactician", "name": "Tactician", "description": "Win 10 battles"},
    {"id": "general", "name": "General", "description": "Win 50 battles"},
    {"id": "warlord", "name": "Warlord", "description": "Win 100 battles"},
    {"id": "speed_run", "name": "Speed Run", "description": "Win a battle in under 5 minutes"},
    {"id": "perfect_victory", "name": "Perfect Victory", "description": "Win without losing any units"},
    {"id": "resource_master", "name": "Resource Master", "description": "Collect 10000 resources"},
]


def load_config():
    """Load configuration from file"""
    import json
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f:
                config = json.load(f)
                # Apply loaded settings
                for key, value in config.items():
                    if hasattr(GameSettings, key.upper()):
                        setattr(GameSettings, key.upper(), value)
                    elif hasattr(GraphicsSettings, key.upper()):
                        setattr(GraphicsSettings, key.upper(), value)
                    elif hasattr(AudioSettings, key.upper()):
                        setattr(AudioSettings, key.upper(), value)
        except Exception as e:
            print(f"Error loading config: {e}")


def save_config():
    """Save configuration to file"""
    import json
    config = {}
    
    # Save GameSettings
    for key in dir(GameSettings):
        if not key.startswith('_'):
            config[key] = getattr(GameSettings, key)
    
    # Save GraphicsSettings
    for key in dir(GraphicsSettings):
        if not key.startswith('_'):
            config[f"graphics_{key}"] = getattr(GraphicsSettings, key)
    
    # Save AudioSettings
    for key in dir(AudioSettings):
        if not key.startswith('_'):
            config[f"audio_{key}"] = getattr(AudioSettings, key)
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    
    try:
        with open(CONFIG_PATH, 'w') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"Error saving config: {e}")


# Load config on startup
load_config()
