"""
HUD (Heads-Up Display) for Frontwars
"""

import pygame
from typing import Optional, List

from config import SCREEN_WIDTH, SCREEN_HEIGHT, Colors, GameSettings
from utils.logger import logger
from game.game_state import GameState, game_state
from game.camera import Camera
from game.map import GameMap
from .ui_manager import UIManager
from .widgets import Panel, Label, ProgressBar, Button, Minimap


class HUD:
    """Heads-Up Display for the game"""
    
    def __init__(self, screen: pygame.Surface, ui_manager: UIManager):
        self.screen = screen
        self.ui_manager = ui_manager
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT
        
        # Create HUD elements
        self._create_hud_elements()
        
        logger.info("HUD initialized", "ui")
    
    def _create_hud_elements(self):
        """Create HUD elements"""
        # Top panel (for game info)
        self.top_panel = Panel(0, 0, self.width, 40, border_width=0)
        self.top_panel.color = (*Colors.UI_BACKGROUND, 200)
        
        # Minimap
        minimap_size = 150
        self.minimap = Minimap(
            self.width - minimap_size - 10,
            10,
            minimap_size,
            minimap_size
        )
        
        # Bottom panel (for unit info)
        self.bottom_panel = Panel(0, self.height - 120, self.width, 120)
        self.bottom_panel.title = "Unit Info"
        
        # Left panel (for team info)
        self.left_panel = Panel(10, 50, 200, self.height - 170)
        self.left_panel.title = "Team Info"
        
        # Right panel (for stats)
        self.right_panel = Panel(self.width - 220, 50, 200, self.height - 170)
        self.right_panel.title = "Stats"
        
        # Add elements to UI manager
        self.ui_manager.add_element(self.top_panel)
        self.ui_manager.add_element(self.minimap)
        self.ui_manager.add_element(self.bottom_panel)
        self.ui_manager.add_element(self.left_panel)
        self.ui_manager.add_element(self.right_panel)
        
        # Create labels for top panel
        self.time_label = Label(10, 10, "Time: 00:00", 16, Colors.WHITE)
        self.fps_label = Label(self.width - 100, 10, "FPS: 0", 16, Colors.WHITE)
        
        # Add labels to top panel
        self.top_panel.add_child(self.time_label)
        self.top_panel.add_child(self.fps_label)
        
        # Create labels for left panel
        self.team_name_label = Label(15, 75, "Team: None", 14, Colors.WHITE)
        self.gold_label = Label(15, 95, "Gold: 0", 14, Colors.GOLD)
        self.units_label = Label(15, 115, "Units: 0", 14, Colors.WHITE)
        self.buildings_label = Label(15, 135, "Buildings: 0", 14, Colors.WHITE)
        
        # Add labels to left panel
        self.left_panel.add_child(self.team_name_label)
        self.left_panel.add_child(self.gold_label)
        self.left_panel.add_child(self.units_label)
        self.left_panel.add_child(self.buildings_label)
        
        # Create labels for right panel
        self.kills_label = Label(self.width - 195, 75, "Kills: 0", 14, Colors.WHITE)
        self.deaths_label = Label(self.width - 195, 95, "Deaths: 0", 14, Colors.WHITE)
        self.resources_label = Label(self.width - 195, 115, "Resources: 0", 14, Colors.WHITE)
        
        # Add labels to right panel
        self.right_panel.add_child(self.kills_label)
        self.right_panel.add_child(self.deaths_label)
        self.right_panel.add_child(self.resources_label)
        
        # Create labels for bottom panel
        self.unit_name_label = Label(15, self.height - 110, "Unit: None", 16, Colors.WHITE)
        self.unit_health_label = Label(15, self.height - 90, "Health: 100/100", 16, Colors.WHITE)
        self.unit_state_label = Label(15, self.height - 70, "State: IDLE", 16, Colors.WHITE)
        
        # Add labels to bottom panel
        self.bottom_panel.add_child(self.unit_name_label)
        self.bottom_panel.add_child(self.unit_health_label)
        self.bottom_panel.add_child(self.unit_state_label)
    
    def render(self, camera: Camera, game_map: GameMap):
        """Render HUD"""
        # Update minimap
        self.minimap.set_game_map(game_map)
        self.minimap.set_camera(camera)
        
        # Update top panel
        self._update_top_panel()
        
        # Update left panel
        self._update_left_panel()
        
        # Update right panel
        self._update_right_panel()
        
        # Update bottom panel
        self._update_bottom_panel()
        
        # Render UI
        self.ui_manager.render()
    
    def _update_top_panel(self):
        """Update top panel information"""
        # Update time
        game_stats = self.game_state.get_game_stats()
        time_text = f"Time: {game_stats['play_time_formatted']}"
        self.time_label.set_text(time_text)
        
        # Update FPS (handled separately in game loop)
    
    def _update_left_panel(self):
        """Update left panel (team info)"""
        local_player = self.game_state.get_local_player()
        
        if local_player and local_player.team:
            team = local_player.team
            
            # Update team name
            self.team_name_label.set_text(f"Team: {team.name}")
            
            # Update gold
            self.gold_label.set_text(f"Gold: {int(team.gold)}")
            
            # Update unit count
            self.units_label.set_text(f"Units: {team.get_unit_count()}")
            
            # Update building count
            self.buildings_label.set_text(f"Buildings: {team.get_building_count()}")
        else:
            self.team_name_label.set_text("Team: None")
            self.gold_label.set_text("Gold: 0")
            self.units_label.set_text("Units: 0")
            self.buildings_label.set_text("Buildings: 0")
    
    def _update_right_panel(self):
        """Update right panel (stats)"""
        local_player = self.game_state.get_local_player()
        
        if local_player and local_player.team:
            team = local_player.team
            
            # Update kills
            self.kills_label.set_text(f"Kills: {team.stats.units_killed}")
            
            # Update deaths
            self.deaths_label.set_text(f"Deaths: {team.stats.units_lost}")
            
            # Update resources
            self.resources_label.set_text(f"Resources: {int(team.stats.resources_collected)}")
        else:
            self.kills_label.set_text("Kills: 0")
            self.deaths_label.set_text("Deaths: 0")
            self.resources_label.set_text("Resources: 0")
    
    def _update_bottom_panel(self):
        """Update bottom panel (unit info)"""
        local_player = self.game_state.get_local_player()
        
        if local_player:
            selected_units = local_player.get_selected_units()
            
            if len(selected_units) == 1:
                # Single unit selected
                unit = selected_units[0]
                unit_info = unit.get_unit_info()
                
                self.unit_name_label.set_text(f"Unit: {unit_info['name']}")
                self.unit_health_label.set_text(f"Health: {int(unit_info['health'])}/{int(unit_info['max_health'])}")
                self.unit_state_label.set_text(f"State: {unit_info['state']}")
            elif len(selected_units) > 1:
                # Multiple units selected
                self.unit_name_label.set_text(f"Units: {len(selected_units)} selected")
                self.unit_health_label.set_text("")
                self.unit_state_label.set_text("")
            else:
                # No unit selected
                self.unit_name_label.set_text("Unit: None")
                self.unit_health_label.set_text("Health: 0/0")
                self.unit_state_label.set_text("State: IDLE")
        else:
            self.unit_name_label.set_text("Unit: None")
            self.unit_health_label.set_text("Health: 0/0")
            self.unit_state_label.set_text("State: IDLE")
    
    def update(self, delta_time: float):
        """Update HUD"""
        pass
    
    def handle_event(self, event: pygame.event.Event):
        """Handle event"""
        pass


class MinimapHUD:
    """Minimap-specific HUD elements"""
    
    def __init__(self, screen: pygame.Surface, ui_manager: UIManager):
        self.screen = screen
        self.ui_manager = ui_manager
        
    def render(self, camera: Camera, game_map: GameMap):
        """Render minimap HUD"""
        pass
