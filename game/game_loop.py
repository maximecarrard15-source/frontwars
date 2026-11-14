"""
Game loop for Frontwars
"""

import pygame
import sys
import time
from typing import Optional, Callable, List

from config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, GAME_NAME, GAME_VERSION
from utils.logger import logger
from game.game_state import GameState, GamePhase, game_state
from ui.ui_manager import UIManager
from ui.hud import HUD
from ui.menu import MainMenu, PauseMenu, GameOverMenu


class GameLoop:
    """Main game loop"""
    
    def __init__(self):
        # Initialize pygame
        self._initialize_pygame()
        
        # Game components
        self.game_state = game_state
        self.ui_manager: Optional[UIManager] = None
        self.hud: Optional[HUD] = None
        self.main_menu: Optional[MainMenu] = None
        self.pause_menu: Optional[PauseMenu] = None
        self.game_over_menu: Optional[GameOverMenu] = None
        
        # Timing
        self.clock = pygame.time.Clock()
        self.last_frame_time = time.time()
        self.frame_count = 0
        self.fps = 0
        
        # Initialize
        self._initialize()
    
    def _initialize_pygame(self):
        """Initialize pygame"""
        pygame.init()
        pygame.display.set_caption(f"{GAME_NAME} v{GAME_VERSION}")
        
        # Set up display
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        
        # Enable alpha channel for surfaces
        pygame.display.get_surface().set_colorkey((0, 0, 0))
        
        # Initialize fonts
        pygame.font.init()
        
        logger.info("Pygame initialized", "system")
    
    def _initialize(self):
        """Initialize game components"""
        # Initialize UI
        self.ui_manager = UIManager(self.screen)
        
        # Initialize menus
        self.main_menu = MainMenu(self.screen, self.ui_manager)
        self.pause_menu = PauseMenu(self.screen, self.ui_manager)
        self.game_over_menu = GameOverMenu(self.screen, self.ui_manager)
        
        # Initialize HUD
        self.hud = HUD(self.screen, self.ui_manager)
        
        # Set initial phase
        self.game_state.set_phase(GamePhase.MENU)
        
        logger.info("Game loop initialized", "game")
    
    def run(self):
        """Run the main game loop"""
        logger.info(f"Starting {GAME_NAME} v{GAME_VERSION}", "game")
        
        while self.game_state.running:
            # Handle events
            self._handle_events()
            
            # Update game
            self._update()
            
            # Render
            self._render()
            
            # Cap frame rate
            self.clock.tick(FPS)
            
            # Calculate FPS
            self._calculate_fps()
        
        # Cleanup
        self._cleanup()
    
    def _handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            # Handle window close
            if event.type == pygame.QUIT:
                self.game_state.quit()
            
            # Pass event to game state
            self.game_state.handle_event(event)
            
            # Pass event to UI
            if self.ui_manager:
                self.ui_manager.handle_event(event)
            
            # Pass event to current menu
            if self.game_state.phase == GamePhase.MENU and self.main_menu:
                self.main_menu.handle_event(event)
            elif self.game_state.phase == GamePhase.PAUSED and self.pause_menu:
                self.pause_menu.handle_event(event)
            elif self.game_state.phase in [GamePhase.GAME_OVER, GamePhase.VICTORY] and self.game_over_menu:
                self.game_over_menu.handle_event(event)
    
    def _update(self):
        """Update game state"""
        # Update game state
        self.game_state.update()
        
        # Update UI
        if self.ui_manager:
            self.ui_manager.update(self.game_state.delta_time)
        
        # Update current menu
        if self.game_state.phase == GamePhase.MENU and self.main_menu:
            self.main_menu.update(self.game_state.delta_time)
        elif self.game_state.phase == GamePhase.PAUSED and self.pause_menu:
            self.pause_menu.update(self.game_state.delta_time)
        elif self.game_state.phase in [GamePhase.GAME_OVER, GamePhase.VICTORY] and self.game_over_menu:
            self.game_over_menu.update(self.game_state.delta_time)
    
    def _render(self):
        """Render game"""
        # Clear screen
        self.screen.fill((0, 0, 0))
        
        # Render based on current phase
        if self.game_state.phase == GamePhase.MENU:
            self._render_menu()
        elif self.game_state.phase == GamePhase.SETUP:
            self._render_setup()
        elif self.game_state.phase == GamePhase.PLAYING:
            self._render_game()
        elif self.game_state.phase == GamePhase.PAUSED:
            self._render_paused()
        elif self.game_state.phase in [GamePhase.GAME_OVER, GamePhase.VICTORY]:
            self._render_game_over()
        
        # Render UI
        if self.ui_manager:
            self.ui_manager.render()
        
        # Render FPS
        self._render_fps()
        
        # Update display
        pygame.display.flip()
    
    def _render_menu(self):
        """Render main menu"""
        if self.main_menu:
            self.main_menu.render()
    
    def _render_setup(self):
        """Render game setup screen"""
        # For now, just render a loading screen
        font = pygame.font.SysFont('Arial', 36)
        text = font.render("Setting up game...", True, (255, 255, 255))
        self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2,
                               SCREEN_HEIGHT // 2 - text.get_height() // 2))
    
    def _render_game(self):
        """Render game world"""
        # Get camera
        camera = self.game_state.get_camera()
        game_map = self.game_state.get_game_map()
        
        if not camera or not game_map:
            return
        
        # Render map
        self._render_map(camera, game_map)
        
        # Render entities
        self._render_entities(camera)
        
        # Render HUD
        if self.hud:
            self.hud.render(camera, game_map)
    
    def _render_paused(self):
        """Render paused game"""
        # Render game world (dimmed)
        self._render_game()
        
        # Render pause overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        self.screen.blit(overlay, (0, 0))
        
        # Render pause menu
        if self.pause_menu:
            self.pause_menu.render()
    
    def _render_game_over(self):
        """Render game over screen"""
        # Render game world (dimmed)
        self._render_game()
        
        # Render game over overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        # Render game over menu
        if self.game_over_menu:
            self.game_over_menu.render()
    
    def _render_map(self, camera, game_map):
        """Render game map"""
        # Get visible area
        view_rect = camera.get_view_rect()
        
        # Calculate visible cells
        start_x = max(0, int(view_rect[0]))
        start_y = max(0, int(view_rect[1]))
        end_x = min(game_map.width, int(view_rect[0] + view_rect[2]) + 1)
        end_y = min(game_map.height, int(view_rect[1] + view_rect[3]) + 1)
        
        # Draw cells
        cell_size = game_map.CELL_SIZE if hasattr(game_map, 'CELL_SIZE') else 12
        
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                cell = game_map.get_cell(x, y)
                if cell:
                    self._draw_cell(camera, cell, x, y, cell_size)
    
    def _draw_cell(self, camera, cell, x: int, y: int, cell_size: int):
        """Draw a single map cell"""
        # Calculate screen position
        world_pos = Vector2(x + 0.5, y + 0.5)
        screen_pos = camera.world_to_screen(world_pos)
        
        # Calculate screen size
        screen_size = int(cell_size * camera.zoom)
        if screen_size <= 0:
            return
        
        # Draw terrain
        color = cell.get_color()
        rect = pygame.Rect(
            int(screen_pos.x - screen_size / 2),
            int(screen_pos.y - screen_size / 2),
            screen_size,
            screen_size
        )
        
        # Draw base terrain
        pygame.draw.rect(self.screen, color, rect)
        
        # Draw grid lines
        if camera.zoom > 0.8:
            pygame.draw.rect(self.screen, (50, 50, 50), rect, 1)
        
        # Draw owner overlay
        if cell.owner and camera.zoom > 0.5:
            owner_color = cell.owner.color
            alpha_color = (*owner_color, 80)
            s = pygame.Surface((screen_size, screen_size), pygame.SRCALPHA)
            s.fill(alpha_color)
            self.screen.blit(s, (rect.x, rect.y))
        
        # Draw resource indicator
        if cell.resource and camera.zoom > 0.6:
            resource_color = Colors.GOLD if cell.resource == "gold" else Colors.GREEN
            resource_rect = pygame.Rect(
                rect.centerx - screen_size // 4,
                rect.centery - screen_size // 4,
                screen_size // 2,
                screen_size // 2
            )
            pygame.draw.rect(self.screen, resource_color, resource_rect)
        
        # Draw building indicator
        if cell.building and camera.zoom > 0.5:
            pygame.draw.rect(self.screen, Colors.WHITE, rect, 2)
        
        # Draw fog of war
        if cell.fog_of_war and self.game_state.settings.fog_of_war:
            s = pygame.Surface((screen_size, screen_size), pygame.SRCALPHA)
            s.fill((0, 0, 0, 180))
            self.screen.blit(s, (rect.x, rect.y))
    
    def _render_entities(self, camera):
        """Render all entities (units, buildings, projectiles, effects)"""
        # Render buildings
        for team in self.game_state.get_team_manager().get_all_teams():
            for building in team.get_buildings():
                if camera.is_visible(building.position, 20):
                    building.draw(self.screen, camera)
        
        # Render units
        for team in self.game_state.get_team_manager().get_all_teams():
            for unit in team.get_units():
                if camera.is_visible(unit.position, 10):
                    unit.draw(self.screen, camera)
        
        # Render projectiles
        for projectile in projectile_manager.projectiles:
            if camera.is_visible(projectile.position, 5):
                projectile.draw(self.screen, camera)
        
        # Render effects
        for effect in effect_manager.effects:
            if camera.is_visible(effect.position, 10):
                effect.draw(self.screen, camera)
    
    def _render_fps(self):
        """Render FPS counter"""
        if not self.game_state.settings.show_fps:
            return
        
        font = pygame.font.SysFont('Arial', 16)
        fps_text = font.render(f"FPS: {self.fps}", True, Colors.WHITE)
        self.screen.blit(fps_text, (10, 10))
    
    def _calculate_fps(self):
        """Calculate FPS"""
        self.frame_count += 1
        current_time = time.time()
        
        if current_time - self.last_frame_time >= 1.0:
            self.fps = self.frame_count
            self.frame_count = 0
            self.last_frame_time = current_time
    
    def _cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up resources", "system")
        
        # Cleanup pygame
        pygame.font.quit()
        pygame.quit()
        
        logger.info("Game loop cleanup complete", "system")


def run_game():
    """Run the Frontwars game"""
    game_loop = GameLoop()
    game_loop.run()


if __name__ == "__main__":
    run_game()
