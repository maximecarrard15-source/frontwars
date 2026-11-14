"""
Game state management for Frontwars
"""

import pygame
import time
from typing import List, Dict, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto
import json
import os

from config import GameSettings, Team, Colors, ASSETS_PATH, SAVE_PATH
from utils.vector import Vector2
from utils.helpers import get_time_ms, get_time_sec, clamp
from utils.logger import logger
from game.map import GameMap, MapGenerator, map_generator
from game.camera import Camera, CameraController
from game.team import TeamManager, team_manager
from game.player import PlayerManager, player_manager
from entities.unit import Unit, UnitFactory, ConfigUnitType
from entities.building import Building, BuildingFactory, ConfigBuildingType
from entities.projectile import Projectile, ProjectileManager, projectile_manager
from entities.effect import Effect, EffectManager, effect_manager, EffectType


class GamePhase(Enum):
    LOADING = auto()
    MENU = auto()
    SETUP = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()
    VICTORY = auto()
    DEFEAT = auto()


class Difficulty(Enum):
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"
    EXPERT = "expert"


@dataclass
class GameSettingsData:
    """Game settings data"""
    map_width: int = GameSettings.MAP_WIDTH
    map_height: int = GameSettings.MAP_HEIGHT
    num_teams: int = 2
    difficulty: Difficulty = Difficulty.NORMAL
    starting_gold: int = GameSettings.STARTING_GOLD
    fog_of_war: bool = True
    friendly_fire: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'map_width': self.map_width,
            'map_height': self.map_height,
            'num_teams': self.num_teams,
            'difficulty': self.difficulty.value,
            'starting_gold': self.starting_gold,
            'fog_of_war': self.fog_of_war,
            'friendly_fire': self.friendly_fire
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameSettingsData':
        return cls(
            map_width=data.get('map_width', GameSettings.MAP_WIDTH),
            map_height=data.get('map_height', GameSettings.MAP_HEIGHT),
            num_teams=data.get('num_teams', 2),
            difficulty=Difficulty(data.get('difficulty', 'normal')),
            starting_gold=data.get('starting_gold', GameSettings.STARTING_GOLD),
            fog_of_war=data.get('fog_of_war', True),
            friendly_fire=data.get('friendly_fire', False)
        )


@dataclass
class GameStats:
    """Game statistics"""
    start_time: float = 0.0
    play_time: float = 0.0
    total_units_created: int = 0
    total_units_destroyed: int = 0
    total_buildings_created: int = 0
    total_buildings_destroyed: int = 0
    total_projectiles_fired: int = 0
    
    def get_play_time_formatted(self) -> str:
        """Get formatted play time"""
        minutes = int(self.play_time // 60)
        seconds = int(self.play_time % 60)
        return f"{minutes:02d}:{seconds:02d}"


class GameState:
    """Main game state class"""
    
    def __init__(self):
        # Game state
        self.phase = GamePhase.LOADING
        self.running = True
        self.paused = False
        
        # Settings
        self.settings = GameSettingsData()
        
        # Game components
        self.game_map: Optional[GameMap] = None
        self.camera: Optional[Camera] = None
        self.camera_controller: Optional[CameraController] = None
        
        # Managers
        self.unit_factory = UnitFactory()
        self.building_factory = BuildingFactory()
        
        # Time tracking
        self.start_time = 0.0
        self.last_update_time = 0.0
        self.delta_time = 0.0
        self.play_time = 0.0
        
        # Statistics
        self.stats = GameStats()
        
        # Event callbacks
        self.event_callbacks: Dict[str, List[Callable]] = {}
        
        # Initialize
        self._initialize()
    
    def _initialize(self):
        """Initialize game state"""
        # Initialize managers
        self.team_manager = TeamManager()
        self.player_manager = PlayerManager()
        
        # Set up event callbacks
        self._setup_event_callbacks()
        
        logger.info("Game state initialized", "game")
    
    def _setup_event_callbacks(self):
        """Set up event callbacks"""
        self.event_callbacks = {
            'unit_created': [],
            'unit_destroyed': [],
            'building_created': [],
            'building_destroyed': [],
            'team_defeated': [],
            'game_started': [],
            'game_ended': [],
            'player_joined': [],
            'player_left': []
        }
    
    def register_callback(self, event_name: str, callback: Callable):
        """Register event callback"""
        if event_name in self.event_callbacks:
            self.event_callbacks[event_name].append(callback)
    
    def trigger_callback(self, event_name: str, *args, **kwargs):
        """Trigger event callback"""
        if event_name in self.event_callbacks:
            for callback in self.event_callbacks[event_name]:
                callback(*args, **kwargs)
    
    def set_phase(self, phase: GamePhase):
        """Set game phase"""
        self.phase = phase
        logger.info(f"Game phase changed to {phase.name}", "game")
        
        if phase == GamePhase.PLAYING:
            self._start_game()
        elif phase == GamePhase.GAME_OVER:
            self._end_game()
    
    def _start_game(self):
        """Start the game"""
        self.start_time = get_time_sec()
        self.stats.start_time = self.start_time
        self.paused = False
        
        # Initialize game components
        self._initialize_game()
        
        # Trigger callbacks
        self.trigger_callback('game_started')
        
        logger.info("Game started", "game")
    
    def _initialize_game(self):
        """Initialize game components"""
        # Create game map
        self._create_map()
        
        # Initialize teams
        self._initialize_teams()
        
        # Initialize players
        self._initialize_players()
        
        # Initialize camera
        self._initialize_camera()
        
        # Start tracking time
        self.last_update_time = get_time_ms()
    
    def _create_map(self):
        """Create the game map"""
        # Set seed for reproducible generation
        map_generator.set_seed(int(get_time_ms()))
        
        # Generate map
        self.game_map = map_generator.generate(
            self.settings.map_width,
            self.settings.map_height,
            list(self.team_manager.teams.keys())
        )
        
        logger.info(f"Created map {self.settings.map_width}x{self.settings.map_height}", "game")
    
    def _initialize_teams(self):
        """Initialize teams"""
        self.team_manager.initialize_default_teams(self.settings.num_teams)
        
        # Set starting gold
        for team in self.team_manager.get_all_teams():
            team.gold = self.settings.starting_gold
        
        logger.info(f"Initialized {self.settings.num_teams} teams", "game")
    
    def _initialize_players(self):
        """Initialize players"""
        self.player_manager.initialize_default_players(self.settings.num_teams)
        
        # Set up player cameras
        for player in self.player_manager.get_all_players():
            if player.is_human:
                # Create camera for human player
                if player.team:
                    start_pos = self.game_map.get_start_position(player.team.id)
                    if start_pos:
                        camera = Camera(position=start_pos.copy(), zoom=1.0)
                        player.set_camera(camera)
        
        # Set local player camera as main camera
        local_player = self.player_manager.get_local_player()
        if local_player and local_player.camera:
            self.camera = local_player.camera
            self.camera_controller = CameraController(self.camera)
        
        logger.info(f"Initialized {self.settings.num_teams} players", "game")
    
    def _initialize_camera(self):
        """Initialize camera"""
        if not self.camera and self.game_map:
            # Create default camera at map center
            center = self.game_map.get_center()
            self.camera = Camera(position=center.copy(), zoom=1.0)
            self.camera_controller = CameraController(self.camera)
    
    def _end_game(self):
        """End the game"""
        self.paused = True
        self.play_time = get_time_sec() - self.start_time
        self.stats.play_time = self.play_time
        
        # Trigger callbacks
        self.trigger_callback('game_ended')
        
        logger.info(f"Game ended after {self.play_time:.1f} seconds", "game")
    
    def setup_game(self, settings: GameSettingsData):
        """Setup game with settings"""
        self.settings = settings
        self.set_phase(GamePhase.SETUP)
        
        logger.info("Game setup with custom settings", "game")
    
    def start(self):
        """Start the game"""
        self.set_phase(GamePhase.PLAYING)
    
    def pause(self):
        """Pause the game"""
        self.paused = True
        logger.info("Game paused", "game")
    
    def resume(self):
        """Resume the game"""
        self.paused = False
        logger.info("Game resumed", "game")
    
    def toggle_pause(self):
        """Toggle pause state"""
        self.paused = not self.paused
        if self.paused:
            logger.info("Game paused", "game")
        else:
            logger.info("Game resumed", "game")
    
    def end(self, winner: Optional[Team] = None):
        """End the game"""
        if winner:
            self.set_phase(GamePhase.VICTORY)
        else:
            self.set_phase(GamePhase.GAME_OVER)
    
    def update(self):
        """Update game state"""
        if self.paused or self.phase != GamePhase.PLAYING:
            return
        
        # Calculate delta time
        current_time = get_time_ms()
        self.delta_time = (current_time - self.last_update_time) / 1000.0
        self.last_update_time = current_time
        
        # Clamp delta time to prevent physics issues
        self.delta_time = clamp(self.delta_time, 0.0, 0.1)
        
        # Update game time
        self.play_time = get_time_sec() - self.start_time
        self.stats.play_time = self.play_time
        
        # Update managers
        self._update_managers()
        
        # Update camera
        if self.camera_controller:
            self.camera_controller.update(self.delta_time)
        
        # Check for game over
        self._check_game_over()
    
    def _update_managers(self):
        """Update all game managers"""
        # Update teams
        self.team_manager.update(self.delta_time * 1000)  # Convert to ms
        
        # Update players
        self.player_manager.update(self.delta_time)
        
        # Update projectiles
        projectile_manager.update(self.delta_time)
        
        # Update effects
        effect_manager.update(self.delta_time)
        
        # Update units and buildings (through teams)
        for team in self.team_manager.get_all_teams():
            for unit in team.get_units():
                unit.update(self.delta_time)
            for building in team.get_buildings():
                building.update(self.delta_time)
    
    def _check_game_over(self):
        """Check if game is over"""
        if self.team_manager.check_game_over():
            winner = self.team_manager.get_winning_team()
            self.end(winner)
    
    def handle_event(self, event: pygame.event.Event):
        """Handle pygame event"""
        if event.type == pygame.QUIT:
            self.running = False
        
        elif event.type == pygame.KEYDOWN:
            self._handle_key_down(event.key)
        
        elif event.type == pygame.KEYUP:
            self._handle_key_up(event.key)
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self._handle_mouse_down(event.button, event.pos)
        
        elif event.type == pygame.MOUSEBUTTONUP:
            self._handle_mouse_up(event.button, event.pos)
        
        elif event.type == pygame.MOUSEMOTION:
            self._handle_mouse_motion(event.pos, event.rel)
        
        # Pass event to camera controller
        if self.camera_controller:
            self.camera_controller.handle_event(event)
        
        # Pass event to players
        for player in self.player_manager.get_all_players():
            player.handle_event(event)
    
    def _handle_key_down(self, key: int):
        """Handle key press"""
        if key == pygame.K_ESCAPE:
            if self.phase == GamePhase.PLAYING:
                self.toggle_pause()
        
        elif key == pygame.K_SPACE:
            if self.paused and self.phase == GamePhase.PLAYING:
                self.resume()
        
        elif key == pygame.K_p:
            self.toggle_pause()
        
        elif key == pygame.K_f:
            # Toggle fog of war
            self.settings.fog_of_war = not self.settings.fog_of_war
            logger.info(f"Fog of war {'enabled' if self.settings.fog_of_war else 'disabled'}", "game")
    
    def _handle_key_up(self, key: int):
        """Handle key release"""
        pass
    
    def _handle_mouse_down(self, button: int, pos: Tuple[int, int]):
        """Handle mouse button down"""
        pass
    
    def _handle_mouse_up(self, button: int, pos: Tuple[int, int]):
        """Handle mouse button up"""
        pass
    
    def _handle_mouse_motion(self, pos: Tuple[int, int], rel: Tuple[int, int]):
        """Handle mouse motion"""
        pass
    
    def create_unit(self, unit_type: ConfigUnitType, team: Team, position: Vector2) -> Optional[Unit]:
        """Create a new unit"""
        if not self.game_map or not team:
            return None
        
        unit = self.unit_factory.create_unit(unit_type, team, position, self.game_map)
        self.stats.total_units_created += 1
        
        # Trigger callback
        self.trigger_callback('unit_created', unit)
        
        return unit
    
    def create_building(self, building_type: ConfigBuildingType, team: Team, position: Vector2) -> Optional[Building]:
        """Create a new building"""
        if not self.game_map or not team:
            return None
        
        building = self.building_factory.create_building(building_type, team, position, self.game_map)
        self.stats.total_buildings_created += 1
        
        # Trigger callback
        self.trigger_callback('building_created', building)
        
        return building
    
    def fire_projectile(self, projectile_type, source: Vector2, target: Vector2,
                       damage: float = 0.0, shooter: Unit = None, target_unit: Unit = None) -> Projectile:
        """Fire a projectile"""
        projectile = projectile_manager.create_projectile(
            projectile_type, source, target, damage, shooter, target_unit
        )
        self.stats.total_projectiles_fired += 1
        return projectile
    
    def create_effect(self, effect_type: EffectType, position: Vector2, target: Any = None) -> Effect:
        """Create an effect"""
        return effect_manager.create_effect(effect_type, position, target)
    
    def get_local_player(self) -> Optional['Player']:
        """Get local player"""
        return self.player_manager.get_local_player()
    
    def get_game_map(self) -> Optional[GameMap]:
        """Get game map"""
        return self.game_map
    
    def get_camera(self) -> Optional[Camera]:
        """Get camera"""
        return self.camera
    
    def get_team_manager(self) -> TeamManager:
        """Get team manager"""
        return self.team_manager
    
    def get_player_manager(self) -> PlayerManager:
        """Get player manager"""
        return self.player_manager
    
    def get_game_stats(self) -> Dict[str, Any]:
        """Get game statistics"""
        return {
            'play_time': self.play_time,
            'play_time_formatted': self.stats.get_play_time_formatted(),
            'total_units_created': self.stats.total_units_created,
            'total_units_destroyed': self.stats.total_units_destroyed,
            'total_buildings_created': self.stats.total_buildings_created,
            'total_buildings_destroyed': self.stats.total_buildings_destroyed,
            'total_projectiles_fired': self.stats.total_projectiles_fired,
            'teams': [t.get_stats() for t in self.team_manager.get_all_teams()]
        }
    
    def save_game(self, filename: str = None) -> bool:
        """Save game state to file"""
        if not filename:
            filename = f"save_{int(get_time_ms())}.json"
        
        # Ensure save directory exists
        os.makedirs(SAVE_PATH, exist_ok=True)
        filepath = os.path.join(SAVE_PATH, filename)
        
        try:
            data = self._serialize()
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Game saved to {filepath}", "game")
            return True
        except Exception as e:
            logger.error(f"Failed to save game: {e}", "game")
            return False
    
    def load_game(self, filename: str) -> bool:
        """Load game state from file"""
        filepath = os.path.join(SAVE_PATH, filename)
        
        if not os.path.exists(filepath):
            logger.error(f"Save file not found: {filepath}", "game")
            return False
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            self._deserialize(data)
            logger.info(f"Game loaded from {filepath}", "game")
            return True
        except Exception as e:
            logger.error(f"Failed to load game: {e}", "game")
            return False
    
    def _serialize(self) -> Dict[str, Any]:
        """Serialize game state to dictionary"""
        data = {
            'version': '1.0',
            'phase': self.phase.name,
            'settings': self.settings.to_dict(),
            'stats': {
                'start_time': self.start_time,
                'play_time': self.play_time,
                'total_units_created': self.stats.total_units_created,
                'total_units_destroyed': self.stats.total_units_destroyed,
                'total_buildings_created': self.stats.total_buildings_created,
                'total_buildings_destroyed': self.stats.total_buildings_destroyed,
                'total_projectiles_fired': self.stats.total_projectiles_fired
            }
        }
        
        # Serialize game map
        if self.game_map:
            data['map'] = self.game_map.save()
        
        # Serialize teams
        data['teams'] = []
        for team in self.team_manager.get_all_teams():
            team_data = {
                'id': team.id.value,
                'name': team.name,
                'color': list(team.color),
                'gold': team.gold,
                'ai_controlled': team.is_ai,
                'stats': {
                    'units_killed': team.stats.units_killed,
                    'units_lost': team.stats.units_lost,
                    'buildings_destroyed': team.stats.buildings_destroyed,
                    'buildings_lost': team.stats.buildings_lost,
                    'resources_collected': team.stats.resources_collected,
                    'territories_captured': team.stats.territories_captured,
                    'territories_lost': team.stats.territories_lost
                }
            }
            data['teams'].append(team_data)
        
        # Serialize players
        data['players'] = []
        for player in self.player_manager.get_all_players():
            player_data = {
                'id': player.id,
                'name': player.name,
                'team_id': player.team_id.value if player.team_id else None,
                'type': player.player_type.value
            }
            data['players'].append(player_data)
        
        return data
    
    def _deserialize(self, data: Dict[str, Any]):
        """Deserialize game state from dictionary"""
        # Restore settings
        if 'settings' in data:
            self.settings = GameSettingsData.from_dict(data['settings'])
        
        # Restore stats
        if 'stats' in data:
            stats_data = data['stats']
            self.start_time = stats_data.get('start_time', 0.0)
            self.play_time = stats_data.get('play_time', 0.0)
            self.stats.start_time = self.start_time
            self.stats.play_time = self.play_time
            self.stats.total_units_created = stats_data.get('total_units_created', 0)
            self.stats.total_units_destroyed = stats_data.get('total_units_destroyed', 0)
            self.stats.total_buildings_created = stats_data.get('total_buildings_created', 0)
            self.stats.total_buildings_destroyed = stats_data.get('total_buildings_destroyed', 0)
            self.stats.total_projectiles_fired = stats_data.get('total_projectiles_fired', 0)
        
        # Restore phase
        if 'phase' in data:
            self.phase = GamePhase[data['phase']]
        
        # Restore map
        if 'map' in data and data['map']:
            self.game_map = GameMap(data['map']['width'], data['map']['height'])
            self.game_map.load(data['map'])
        
        # Restore teams
        if 'teams' in data:
            self.team_manager.clear()
            for team_data in data['teams']:
                team_id = Team(team_data['id'])
                from config import TeamConfig
                config = TeamConfig(
                    name=team_data['name'],
                    color=tuple(team_data['color']),
                    ai_controlled=team_data.get('ai_controlled', False),
                    gold=team_data.get('gold', GameSettings.STARTING_GOLD)
                )
                team = self.team_manager.add_team(team_id, config)
                
                # Restore team stats
                if 'stats' in team_data:
                    stats_data = team_data['stats']
                    team.stats.units_killed = stats_data.get('units_killed', 0)
                    team.stats.units_lost = stats_data.get('units_lost', 0)
                    team.stats.buildings_destroyed = stats_data.get('buildings_destroyed', 0)
                    team.stats.buildings_lost = stats_data.get('buildings_lost', 0)
                    team.stats.resources_collected = stats_data.get('resources_collected', 0.0)
                    team.stats.territories_captured = stats_data.get('territories_captured', 0)
                    team.stats.territories_lost = stats_data.get('territories_lost', 0)
        
        # Restore players
        if 'players' in data:
            self.player_manager.clear()
            for player_data in data['players']:
                player_type = PlayerType(player_data.get('type', 'human'))
                team_id = player_data.get('team_id')
                team = self.team_manager.get_team(Team(team_id)) if team_id else None
                player = self.player_manager.add_player(player_type, team)
                player.id = player_data.get('id', player.id)
                player.name = player_data.get('name', player.name)
        
        # Set up camera
        self._initialize_camera()
        
        logger.info("Game state deserialized", "game")
    
    def quit(self):
        """Quit the game"""
        self.running = False
        logger.info("Game quit", "game")


# Global game state instance
game_state = GameState()
