"""
Player system for Frontwars
"""

from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import pygame

from config import GameSettings, Team, Colors, KEY_BINDINGS
from utils.vector import Vector2
from utils.helpers import distance, point_in_rect
from utils.logger import logger
from .team import TeamManager, team_manager


class PlayerState(Enum):
    IDLE = "idle"
    SELECTING = "selecting"
    BUILDING = "building"
    COMMANDING = "commanding"
    PAUSED = "paused"


class PlayerType(Enum):
    HUMAN = "human"
    AI = "ai"
    SPECTATOR = "spectator"


@dataclass
class SelectionBox:
    """Selection box for units"""
    start: Vector2
    end: Vector2
    active: bool = True
    
    def get_rect(self) -> Tuple[float, float, float, float]:
        """Get rectangle of selection box"""
        x = min(self.start.x, self.end.x)
        y = min(self.start.y, self.end.y)
        w = abs(self.end.x - self.start.x)
        h = abs(self.end.y - self.start.y)
        return (x, y, w, h)
    
    def contains_point(self, point: Vector2) -> bool:
        """Check if point is inside selection box"""
        rect = self.get_rect()
        return point_in_rect((point.x, point.y), rect)
    
    def is_valid(self) -> bool:
        """Check if selection box is valid (has size)"""
        return self.start != self.end


@dataclass
class BuildPreview:
    """Preview for building placement"""
    building_type: str
    position: Vector2
    valid: bool = True
    color: Tuple[int, int, int] = Colors.GREEN
    
    def get_size(self) -> Tuple[int, int]:
        """Get building size"""
        sizes = {
            "base": (3, 3),
            "barracks": (2, 2),
            "factory": (3, 2),
            "tower": (1, 1),
            "farm": (2, 2),
            "mine": (2, 2)
        }
        return sizes.get(self.building_type, (1, 1))
    
    def get_cost(self) -> int:
        """Get building cost"""
        costs = {
            "base": 1000,
            "barracks": 500,
            "factory": 800,
            "tower": 300,
            "farm": 200,
            "mine": 250
        }
        return costs.get(self.building_type, 100)


class Player:
    """Represents a player in the game"""
    
    def __init__(self, player_id: int = 0, team: Team = None, player_type: PlayerType = PlayerType.HUMAN):
        self.id = player_id
        self.name = f"Player {player_id + 1}"
        self.team = team
        self.player_type = player_type
        self.state = PlayerState.IDLE
        
        # Input state
        self.selected_units: List = []
        self.selection_box: Optional[SelectionBox] = None
        self.build_preview: Optional[BuildPreview] = None
        self.is_dragging = False
        self.drag_start: Optional[Vector2] = None
        
        # Camera control
        self.camera = None
        
        # UI state
        self.show_minimap = True
        self.show_fog_of_war = True
        self.show_unit_info = True
        self.show_stats = False
        
        # Command history
        self.command_history: List[str] = []
        self.max_command_history = 50
        
        # Statistics
        self.actions_per_minute = 0
        self.last_action_time = 0.0
        self.action_count = 0
        
        # Settings
        self.key_bindings = KEY_BINDINGS.copy()
        self.sensitivity = 1.0
        
        # Initialize
        if team:
            self.team_id = team.id
        else:
            self.team_id = None
    
    @property
    def is_human(self) -> bool:
        return self.player_type == PlayerType.HUMAN
    
    @property
    def is_ai(self) -> bool:
        return self.player_type == PlayerType.AI
    
    @property
    def is_spectator(self) -> bool:
        return self.player_type == PlayerType.SPECTATOR
    
    def set_team(self, team: Team):
        """Set player's team"""
        self.team = team
        self.team_id = team.id
    
    def set_camera(self, camera):
        """Set player's camera"""
        self.camera = camera
    
    def select_unit(self, unit, multi_select: bool = False):
        """Select a unit"""
        if not multi_select:
            self.clear_selection()
        
        if unit not in self.selected_units:
            self.selected_units.append(unit)
            self.add_command(f"Selected {unit.unit_type}")
        
        logger.debug(f"Player {self.id} selected unit {unit.unit_type}", "input")
    
    def select_units(self, units: List, clear: bool = True):
        """Select multiple units"""
        if clear:
            self.clear_selection()
        
        for unit in units:
            if unit not in self.selected_units:
                self.selected_units.append(unit)
        
        if units:
            self.add_command(f"Selected {len(units)} units")
    
    def clear_selection(self):
        """Clear unit selection"""
        self.selected_units.clear()
    
    def deselect_unit(self, unit):
        """Deselect a unit"""
        if unit in self.selected_units:
            self.selected_units.remove(unit)
    
    def is_unit_selected(self, unit) -> bool:
        """Check if unit is selected"""
        return unit in self.selected_units
    
    def get_selected_units(self) -> List:
        """Get all selected units"""
        return self.selected_units.copy()
    
    def get_selected_unit_count(self) -> int:
        """Get number of selected units"""
        return len(self.selected_units)
    
    def start_selection_box(self, start_pos: Vector2):
        """Start drawing selection box"""
        self.selection_box = SelectionBox(start_pos, start_pos)
        self.is_dragging = True
        self.drag_start = start_pos
    
    def update_selection_box(self, end_pos: Vector2):
        """Update selection box"""
        if self.selection_box:
            self.selection_box.end = end_pos
    
    def end_selection_box(self, end_pos: Vector2, units: List) -> List:
        """End selection box and return selected units"""
        if not self.selection_box:
            return []
        
        self.selection_box.end = end_pos
        self.selection_box.active = False
        
        # Find units in selection box
        selected = []
        rect = self.selection_box.get_rect()
        
        for unit in units:
            if point_in_rect((unit.position.x, unit.position.y), rect):
                selected.append(unit)
        
        self.is_dragging = False
        self.drag_start = None
        self.selection_box = None
        
        return selected
    
    def start_build_preview(self, building_type: str, position: Vector2):
        """Start building preview"""
        self.build_preview = BuildPreview(
            building_type=building_type,
            position=position
        )
        self.state = PlayerState.BUILDING
    
    def update_build_preview(self, position: Vector2, valid: bool):
        """Update building preview"""
        if self.build_preview:
            self.build_preview.position = position
            self.build_preview.valid = valid
            self.build_preview.color = Colors.GREEN if valid else Colors.RED
    
    def cancel_build_preview(self):
        """Cancel building preview"""
        self.build_preview = None
        self.state = PlayerState.IDLE
    
    def confirm_build(self, position: Vector2):
        """Confirm building placement"""
        if not self.build_preview:
            return False
        
        # Check if team can afford it
        if self.team and self.team.can_afford(self.build_preview.get_cost()):
            self.team.spend_gold(self.build_preview.get_cost())
            self.add_command(f"Built {self.build_preview.building_type}")
            self.cancel_build_preview()
            return True
        
        return False
    
    def command_move(self, target: Vector2):
        """Command selected units to move"""
        if not self.selected_units:
            return
        
        for unit in self.selected_units:
            unit.move_to(target)
        
        self.add_command(f"Move to ({target.x:.0f}, {target.y:.0f})")
        self.record_action()
    
    def command_attack(self, target: Vector2):
        """Command selected units to attack"""
        if not self.selected_units:
            return
        
        for unit in self.selected_units:
            unit.attack_move(target)
        
        self.add_command(f"Attack at ({target.x:.0f}, {target.y:.0f})")
        self.record_action()
    
    def command_hold(self):
        """Command selected units to hold position"""
        if not self.selected_units:
            return
        
        for unit in self.selected_units:
            unit.hold_position()
        
        self.add_command("Hold position")
        self.record_action()
    
    def command_stop(self):
        """Command selected units to stop"""
        if not self.selected_units:
            return
        
        for unit in self.selected_units:
            unit.stop()
        
        self.add_command("Stop")
        self.record_action()
    
    def add_command(self, command: str):
        """Add command to history"""
        self.command_history.append(command)
        if len(self.command_history) > self.max_command_history:
            self.command_history = self.command_history[-self.max_command_history:]
    
    def get_last_commands(self, count: int = 5) -> List[str]:
        """Get last commands"""
        return self.command_history[-count:]
    
    def record_action(self):
        """Record player action"""
        import time
        current_time = time.time()
        
        if self.last_action_time > 0:
            time_diff = current_time - self.last_action_time
            if time_diff < 60:  # Within last minute
                self.action_count += 1
        
        self.last_action_time = current_time
    
    def update_actions_per_minute(self):
        """Update actions per minute"""
        import time
        current_time = time.time()
        
        if current_time - self.last_action_time > 60:
            self.actions_per_minute = self.action_count
            self.action_count = 0
            self.last_action_time = current_time
    
    def handle_event(self, event: pygame.event.Event):
        """Handle pygame event"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                self._handle_left_click(event.pos)
            elif event.button == 3:  # Right click
                self._handle_right_click(event.pos)
        
        elif event.type == pygame.KEYDOWN:
            self._handle_key_down(event.key)
    
    def _handle_left_click(self, screen_pos: Tuple[int, int]):
        """Handle left mouse click"""
        if self.state == PlayerState.BUILDING:
            # Place building
            world_pos = self.camera.screen_to_world(Vector2(screen_pos[0], screen_pos[1]))
            self.confirm_build(world_pos)
        else:
            # Start selection
            world_pos = self.camera.screen_to_world(Vector2(screen_pos[0], screen_pos[1]))
            self.start_selection_box(world_pos)
    
    def _handle_right_click(self, screen_pos: Tuple[int, int]):
        """Handle right mouse click"""
        if self.state == PlayerState.BUILDING:
            # Cancel building
            self.cancel_build_preview()
        else:
            # Command units
            world_pos = self.camera.screen_to_world(Vector2(screen_pos[0], screen_pos[1]))
            self.command_move(world_pos)
    
    def _handle_key_down(self, key: int):
        """Handle key press"""
        if key == pygame.K_ESCAPE:
            if self.state == PlayerState.BUILDING:
                self.cancel_build_preview()
            else:
                self.clear_selection()
        
        elif key == pygame.K_a:
            # Select all units
            if self.team:
                self.select_units(self.team.get_units())
        
        elif key == pygame.K_s:
            # Stop command
            self.command_stop()
        
        elif key == pygame.K_h:
            # Hold position
            self.command_hold()
        
        elif key == pygame.K_b:
            # Start building mode
            self.state = PlayerState.BUILDING
    
    def update(self, delta_time: float):
        """Update player state"""
        self.update_actions_per_minute()
        
        # Update camera if following selected units
        if self.camera and self.selected_units:
            # Calculate average position of selected units
            avg_x = sum(u.position.x for u in self.selected_units) / len(self.selected_units)
            avg_y = sum(u.position.y for u in self.selected_units) / len(self.selected_units)
            
            # Follow with camera
            target = Vector2(avg_x, avg_y)
            self.camera.follow(target, delta_time)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get player statistics"""
        return {
            'id': self.id,
            'name': self.name,
            'team': self.team.name if self.team else None,
            'team_id': self.team_id,
            'type': self.player_type.value,
            'selected_units': len(self.selected_units),
            'actions_per_minute': self.actions_per_minute,
            'commands': len(self.command_history)
        }
    
    def __str__(self) -> str:
        return f"Player({self.id}, {self.name}, team={self.team_id}, type={self.player_type.value})"


class PlayerManager:
    """Manages all players in the game"""
    
    def __init__(self):
        self.players: Dict[int, Player] = {}
        self.local_player: Optional[Player] = None
        self.player_count = 0
    
    def add_player(self, player_type: PlayerType = PlayerType.HUMAN, 
                   team: Team = None) -> Player:
        """Add a new player"""
        player_id = self.player_count
        player = Player(player_id, team, player_type)
        self.players[player_id] = player
        self.player_count += 1
        
        if player_type == PlayerType.HUMAN and self.local_player is None:
            self.local_player = player
        
        logger.info(f"Added player {player_id}: {player_type.value}", "game")
        return player
    
    def remove_player(self, player_id: int):
        """Remove a player"""
        if player_id in self.players:
            del self.players[player_id]
            
            if self.local_player and self.local_player.id == player_id:
                self.local_player = None
            
            logger.info(f"Removed player {player_id}", "game")
    
    def get_player(self, player_id: int) -> Optional[Player]:
        """Get player by ID"""
        return self.players.get(player_id)
    
    def get_local_player(self) -> Optional[Player]:
        """Get local human player"""
        return self.local_player
    
    def get_all_players(self) -> List[Player]:
        """Get all players"""
        return list(self.players.values())
    
    def get_human_players(self) -> List[Player]:
        """Get all human players"""
        return [p for p in self.players.values() if p.is_human]
    
    def get_ai_players(self) -> List[Player]:
        """Get all AI players"""
        return [p for p in self.players.values() if p.is_ai]
    
    def set_local_player(self, player: Player):
        """Set local player"""
        self.local_player = player
    
    def get_player_by_team(self, team: Team) -> Optional[Player]:
        """Get player controlling team"""
        for player in self.players.values():
            if player.team == team:
                return player
        return None
    
    def update(self, delta_time: float):
        """Update all players"""
        for player in self.players.values():
            player.update(delta_time)
    
    def clear(self):
        """Clear all players"""
        self.players.clear()
        self.local_player = None
        self.player_count = 0
    
    def initialize_default_players(self, num_teams: int = 2):
        """Initialize default players"""
        self.clear()
        
        # Create teams first
        team_manager.initialize_default_teams(num_teams)
        
        # Create players for each team
        for team in team_manager.get_all_teams():
            player_type = PlayerType.HUMAN if not team.is_ai else PlayerType.AI
            player = self.add_player(player_type, team)
            player.name = f"Player {len(self.players)}"
        
        # Set first human player as local
        human_players = self.get_human_players()
        if human_players:
            self.local_player = human_players[0]
        
        logger.info(f"Initialized {len(self.players)} default players", "game")


# Global player manager instance
player_manager = PlayerManager()
