"""
Menu system for Frontwars
"""

import pygame
from typing import Optional, Callable, List, Dict, Any

from config import SCREEN_WIDTH, SCREEN_HEIGHT, Colors, GameSettings
from utils.logger import logger
from game.game_state import GameState, GamePhase, GameSettingsData, Difficulty
from .ui_manager import UIManager, UIElement
from .widgets import Panel, Button, Label, ListBox, Checkbox, Slider


class Menu:
    """Base menu class"""
    
    def __init__(self, screen: pygame.Surface, ui_manager: UIManager):
        self.screen = screen
        self.ui_manager = ui_manager
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT
        self.elements: List[UIElement] = []
        self.background_color = (30, 30, 40)
        self.active = False
    
    def show(self):
        """Show menu"""
        self.active = True
        self._create_elements()
        
        # Add elements to UI manager
        for element in self.elements:
            self.ui_manager.add_element(element)
    
    def hide(self):
        """Hide menu"""
        self.active = False
        
        # Remove elements from UI manager
        for element in self.elements:
            self.ui_manager.remove_element(element)
    
    def _create_elements(self):
        """Create menu elements (to be overridden by subclasses)"""
        pass
    
    def update(self, delta_time: float):
        """Update menu"""
        pass
    
    def render(self):
        """Render menu"""
        # Draw background
        if self.active:
            # Semi-transparent overlay
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            self.screen.blit(overlay, (0, 0))
    
    def handle_event(self, event: pygame.event.Event):
        """Handle event"""
        pass


class MainMenu(Menu):
    """Main menu"""
    
    def __init__(self, screen: pygame.Surface, ui_manager: UIManager,
                 on_play: Optional[Callable] = None,
                 on_settings: Optional[Callable] = None,
                 on_quit: Optional[Callable] = None):
        super().__init__(screen, ui_manager)
        self.on_play = on_play
        self.on_settings = on_settings
        self.on_quit = on_quit
    
    def _create_elements(self):
        """Create main menu elements"""
        # Clear existing elements
        self.elements.clear()
        
        # Create panel
        panel_width = 300
        panel_height = 300
        panel_x = self.width // 2 - panel_width // 2
        panel_y = self.height // 2 - panel_height // 2
        
        panel = Panel(panel_x, panel_y, panel_width, panel_height, "Frontwars")
        self.elements.append(panel)
        
        # Create title label
        title_font = pygame.font.SysFont('Arial', 32, bold=True)
        title_surface = title_font.render("Frontwars", True, Colors.WHITE)
        title_label = Label(
            panel_x + panel_width // 2 - title_surface.get_width() // 2,
            panel_y + 20,
            "Frontwars",
            32,
            Colors.WHITE
        )
        title_label.font = title_font
        title_label.text_surface = title_surface
        panel.add_child(title_label)
        
        # Create buttons
        button_width = 200
        button_height = 40
        button_x = panel_x + panel_width // 2 - button_width // 2
        
        play_button = Button(
            button_x, panel_y + 80,
            button_width, button_height,
            "Play",
            on_click=self._on_play
        )
        panel.add_child(play_button)
        
        settings_button = Button(
            button_x, panel_y + 130,
            button_width, button_height,
            "Settings",
            on_click=self._on_settings
        )
        panel.add_child(settings_button)
        
        quit_button = Button(
            button_x, panel_y + 180,
            button_width, button_height,
            "Quit",
            on_click=self._on_quit
        )
        panel.add_child(quit_button)
        
        # Add panel to elements
        self.elements.append(panel)
    
    def _on_play(self):
        """Handle play button click"""
        if self.on_play:
            self.on_play()
        else:
            # Default behavior: start game
            from game.game_state import game_state
            game_state.set_phase(GamePhase.SETUP)
            game_state.start()
    
    def _on_settings(self):
        """Handle settings button click"""
        if self.on_settings:
            self.on_settings()
    
    def _on_quit(self):
        """Handle quit button click"""
        if self.on_quit:
            self.on_quit()
        else:
            # Default behavior: quit game
            from game.game_state import game_state
            game_state.quit()


class SettingsMenu(Menu):
    """Settings menu"""
    
    def __init__(self, screen: pygame.Surface, ui_manager: UIManager,
                 on_back: Optional[Callable] = None,
                 on_save: Optional[Callable] = None):
        super().__init__(screen, ui_manager)
        self.on_back = on_back
        self.on_save = on_save
        self.settings = GameSettingsData()
    
    def _create_elements(self):
        """Create settings menu elements"""
        # Clear existing elements
        self.elements.clear()
        
        # Create panel
        panel_width = 400
        panel_height = 500
        panel_x = self.width // 2 - panel_width // 2
        panel_y = self.height // 2 - panel_height // 2
        
        panel = Panel(panel_x, panel_y, panel_width, panel_height, "Settings")
        self.elements.append(panel)
        
        # Create tabs or categories
        # For simplicity, we'll just add all settings to the panel
        
        y_offset = 30
        
        # Map size settings
        map_size_label = Label(panel_x + 20, panel_y + y_offset, "Map Size:", 16, Colors.WHITE)
        panel.add_child(map_size_label)
        y_offset += 30
        
        # Difficulty
        difficulty_label = Label(panel_x + 20, panel_y + y_offset, "Difficulty:", 16, Colors.WHITE)
        panel.add_child(difficulty_label)
        
        difficulty_dropdown = ListBox(
            panel_x + 150, panel_y + y_offset - 5,
            150, 25,
            [d.value.capitalize() for d in Difficulty]
        )
        panel.add_child(difficulty_dropdown)
        y_offset += 35
        
        # Number of teams
        teams_label = Label(panel_x + 20, panel_y + y_offset, "Teams:", 16, Colors.WHITE)
        panel.add_child(teams_label)
        
        teams_dropdown = ListBox(
            panel_x + 150, panel_y + y_offset - 5,
            150, 25,
            ["2", "3", "4"]
        )
        panel.add_child(teams_dropdown)
        y_offset += 35
        
        # Fog of war
        fog_check = Checkbox(
            panel_x + 20, panel_y + y_offset,
            checked=True,
            label="Fog of War"
        )
        panel.add_child(fog_check)
        y_offset += 30
        
        # Friendly fire
        friendly_fire_check = Checkbox(
            panel_x + 20, panel_y + y_offset,
            checked=False,
            label="Friendly Fire"
        )
        panel.add_child(friendly_fire_check)
        y_offset += 40
        
        # Buttons
        button_width = 120
        button_height = 35
        
        save_button = Button(
            panel_x + panel_width - button_width - 20, panel_y + panel_height - button_height - 20,
            button_width, button_height,
            "Save",
            on_click=self._on_save
        )
        panel.add_child(save_button)
        
        back_button = Button(
            panel_x + 20, panel_y + panel_height - button_height - 20,
            button_width, button_height,
            "Back",
            on_click=self._on_back
        )
        panel.add_child(back_button)
    
    def _on_back(self):
        """Handle back button click"""
        if self.on_back:
            self.on_back()
        else:
            self.hide()
    
    def _on_save(self):
        """Handle save button click"""
        if self.on_save:
            self.on_save()
        else:
            # Save settings
            self.hide()


class PauseMenu(Menu):
    """Pause menu"""
    
    def __init__(self, screen: pygame.Surface, ui_manager: UIManager,
                 on_resume: Optional[Callable] = None,
                 on_settings: Optional[Callable] = None,
                 on_quit: Optional[Callable] = None):
        super().__init__(screen, ui_manager)
        self.on_resume = on_resume
        self.on_settings = on_settings
        self.on_quit = on_quit
    
    def _create_elements(self):
        """Create pause menu elements"""
        # Clear existing elements
        self.elements.clear()
        
        # Create panel
        panel_width = 300
        panel_height = 250
        panel_x = self.width // 2 - panel_width // 2
        panel_y = self.height // 2 - panel_height // 2
        
        panel = Panel(panel_x, panel_y, panel_width, panel_height, "Paused")
        self.elements.append(panel)
        
        # Create buttons
        button_width = 200
        button_height = 40
        button_x = panel_x + panel_width // 2 - button_width // 2
        
        resume_button = Button(
            button_x, panel_y + 60,
            button_width, button_height,
            "Resume",
            on_click=self._on_resume
        )
        panel.add_child(resume_button)
        
        settings_button = Button(
            button_x, panel_y + 110,
            button_width, button_height,
            "Settings",
            on_click=self._on_settings
        )
        panel.add_child(settings_button)
        
        quit_button = Button(
            button_x, panel_y + 160,
            button_width, button_height,
            "Quit to Menu",
            on_click=self._on_quit
        )
        panel.add_child(quit_button)
    
    def _on_resume(self):
        """Handle resume button click"""
        if self.on_resume:
            self.on_resume()
        else:
            # Default behavior: resume game
            from game.game_state import game_state
            game_state.resume()
            self.hide()
    
    def _on_settings(self):
        """Handle settings button click"""
        if self.on_settings:
            self.on_settings()
    
    def _on_quit(self):
        """Handle quit button click"""
        if self.on_quit:
            self.on_quit()
        else:
            # Default behavior: return to main menu
            from game.game_state import game_state
            game_state.set_phase(GamePhase.MENU)
            self.hide()


class GameOverMenu(Menu):
    """Game over menu"""
    
    def __init__(self, screen: pygame.Surface, ui_manager: UIManager,
                 on_restart: Optional[Callable] = None,
                 on_menu: Optional[Callable] = None,
                 on_quit: Optional[Callable] = None):
        super().__init__(screen, ui_manager)
        self.on_restart = on_restart
        self.on_menu = on_menu
        self.on_quit = on_quit
        self.winner = None
    
    def show(self, winner = None):
        """Show menu with winner information"""
        self.winner = winner
        super().show()
    
    def _create_elements(self):
        """Create game over menu elements"""
        # Clear existing elements
        self.elements.clear()
        
        # Create panel
        panel_width = 400
        panel_height = 300
        panel_x = self.width // 2 - panel_width // 2
        panel_y = self.height // 2 - panel_height // 2
        
        title = "Victory!" if self.winner else "Game Over"
        panel = Panel(panel_x, panel_y, panel_width, panel_height, title)
        self.elements.append(panel)
        
        # Create message label
        if self.winner:
            message = f"{self.winner.name} has won the game!"
        else:
            message = "The game has ended in a draw."
        
        message_label = Label(
            panel_x + 20, panel_y + 40,
            message,
            20,
            Colors.WHITE
        )
        panel.add_child(message_label)
        
        # Create stats label
        stats_label = Label(
            panel_x + 20, panel_y + 80,
            "Final Statistics",
            16,
            Colors.WHITE
        )
        panel.add_child(stats_label)
        
        # Create buttons
        button_width = 120
        button_height = 35
        
        restart_button = Button(
            panel_x + 50, panel_y + panel_height - button_height - 20,
            button_width, button_height,
            "Restart",
            on_click=self._on_restart
        )
        panel.add_child(restart_button)
        
        menu_button = Button(
            panel_x + panel_width - button_width - 50, panel_y + panel_height - button_height - 20,
            button_width, button_height,
            "Main Menu",
            on_click=self._on_menu
        )
        panel.add_child(menu_button)
        
        quit_button = Button(
            panel_x + panel_width // 2 - button_width // 2, panel_y + panel_height - button_height - 60,
            button_width, button_height,
            "Quit",
            on_click=self._on_quit
        )
        panel.add_child(quit_button)
    
    def _on_restart(self):
        """Handle restart button click"""
        if self.on_restart:
            self.on_restart()
        else:
            # Default behavior: restart game
            from game.game_state import game_state
            game_state.set_phase(GamePhase.SETUP)
            game_state.start()
            self.hide()
    
    def _on_menu(self):
        """Handle menu button click"""
        if self.on_menu:
            self.on_menu()
        else:
            # Default behavior: return to main menu
            from game.game_state import game_state
            game_state.set_phase(GamePhase.MENU)
            self.hide()
    
    def _on_quit(self):
        """Handle quit button click"""
        if self.on_quit:
            self.on_quit()
        else:
            # Default behavior: quit game
            from game.game_state import game_state
            game_state.quit()


class GameSetupMenu(Menu):
    """Game setup menu"""
    
    def __init__(self, screen: pygame.Surface, ui_manager: UIManager,
                 on_start: Optional[Callable] = None,
                 on_back: Optional[Callable] = None):
        super().__init__(screen, ui_manager)
        self.on_start = on_start
        self.on_back = on_back
        self.settings = GameSettingsData()
    
    def _create_elements(self):
        """Create game setup menu elements"""
        # Clear existing elements
        self.elements.clear()
        
        # Create panel
        panel_width = 400
        panel_height = 400
        panel_x = self.width // 2 - panel_width // 2
        panel_y = self.height // 2 - panel_height // 2
        
        panel = Panel(panel_x, panel_y, panel_width, panel_height, "Game Setup")
        self.elements.append(panel)
        
        y_offset = 30
        
        # Map size
        map_size_label = Label(panel_x + 20, panel_y + y_offset, "Map Size:", 16, Colors.WHITE)
        panel.add_child(map_size_label)
        y_offset += 30
        
        # Map width
        width_label = Label(panel_x + 20, panel_y + y_offset, "Width:", 14, Colors.WHITE)
        panel.add_child(width_label)
        
        width_slider = Slider(
            panel_x + 100, panel_y + y_offset - 5,
            200, 20,
            min_value=50, max_value=200, value=self.settings.map_width,
            on_change=lambda v: setattr(self.settings, 'map_width', int(v))
        )
        panel.add_child(width_slider)
        y_offset += 35
        
        # Map height
        height_label = Label(panel_x + 20, panel_y + y_offset, "Height:", 14, Colors.WHITE)
        panel.add_child(height_label)
        
        height_slider = Slider(
            panel_x + 100, panel_y + y_offset - 5,
            200, 20,
            min_value=30, max_value=150, value=self.settings.map_height,
            on_change=lambda v: setattr(self.settings, 'map_height', int(v))
        )
        panel.add_child(height_slider)
        y_offset += 35
        
        # Number of teams
        teams_label = Label(panel_x + 20, panel_y + y_offset, "Teams:", 14, Colors.WHITE)
        panel.add_child(teams_label)
        
        teams_dropdown = ListBox(
            panel_x + 100, panel_y + y_offset - 5,
            100, 25,
            ["2", "3", "4"]
        )
        teams_dropdown.selected_index = self.settings.num_teams - 2
        panel.add_child(teams_dropdown)
        y_offset += 35
        
        # Difficulty
        difficulty_label = Label(panel_x + 20, panel_y + y_offset, "Difficulty:", 14, Colors.WHITE)
        panel.add_child(difficulty_label)
        
        difficulty_dropdown = ListBox(
            panel_x + 100, panel_y + y_offset - 5,
            150, 25,
            [d.value.capitalize() for d in Difficulty]
        )
        difficulty_dropdown.selected_index = list(Difficulty).index(self.settings.difficulty)
        panel.add_child(difficulty_dropdown)
        y_offset += 40
        
        # Buttons
        button_width = 120
        button_height = 35
        
        start_button = Button(
            panel_x + panel_width - button_width - 20, panel_y + panel_height - button_height - 20,
            button_width, button_height,
            "Start Game",
            on_click=self._on_start
        )
        panel.add_child(start_button)
        
        back_button = Button(
            panel_x + 20, panel_y + panel_height - button_height - 20,
            button_width, button_height,
            "Back",
            on_click=self._on_back
        )
        panel.add_child(back_button)
    
    def _on_start(self):
        """Handle start button click"""
        if self.on_start:
            self.on_start()
        else:
            # Default behavior: start game with current settings
            from game.game_state import game_state
            game_state.setup_game(self.settings)
            game_state.start()
            self.hide()
    
    def _on_back(self):
        """Handle back button click"""
        if self.on_back:
            self.on_back()
        else:
            from game.game_state import game_state
            game_state.set_phase(GamePhase.MENU)
            self.hide()
