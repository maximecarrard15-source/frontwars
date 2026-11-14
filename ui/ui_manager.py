"""
UI Manager for Frontwars
"""

import pygame
from typing import List, Dict, Optional, Any, Callable, Tuple
from dataclasses import dataclass
from enum import Enum

from config import SCREEN_WIDTH, SCREEN_HEIGHT, Colors
from utils.logger import logger


class UIState(Enum):
    NORMAL = "normal"
    MENU = "menu"
    HUD = "hud"
    DIALOG = "dialog"


@dataclass
class UIElement:
    """Base UI element"""
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    visible: bool = True
    enabled: bool = True
    
    def contains_point(self, pos: Tuple[int, int]) -> bool:
        """Check if point is inside element"""
        return (self.x <= pos[0] <= self.x + self.width and
                self.y <= pos[1] <= self.y + self.height)
    
    def draw(self, surface: pygame.Surface):
        """Draw element on surface"""
        raise NotImplementedError
    
    def handle_event(self, event: pygame.event.Event):
        """Handle pygame event"""
        pass
    
    def update(self, delta_time: float):
        """Update element"""
        pass


class UIManager:
    """Manages all UI elements"""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.elements: List[UIElement] = []
        self.state = UIState.NORMAL
        self.focus_element: Optional[UIElement] = None
        self.hover_element: Optional[UIElement] = None
        
        # Modal stack
        self.modal_stack: List[UIElement] = []
        
        # Tooltips
        self.tooltip: Optional[str] = None
        self.tooltip_timeout = 0.0
        self.tooltip_delay = 0.5
        
        # Cursor
        self.cursor = pygame.SYSTEM_CURSOR_ARROW
        pygame.mouse.set_cursor(self.cursor)
        
        logger.info("UI Manager initialized", "ui")
    
    def add_element(self, element: UIElement):
        """Add UI element"""
        self.elements.append(element)
    
    def remove_element(self, element: UIElement):
        """Remove UI element"""
        if element in self.elements:
            self.elements.remove(element)
    
    def clear_elements(self):
        """Clear all UI elements"""
        self.elements.clear()
    
    def set_focus(self, element: Optional[UIElement]):
        """Set focus to element"""
        self.focus_element = element
    
    def set_hover(self, element: Optional[UIElement]):
        """Set hover element"""
        self.hover_element = element
    
    def set_tooltip(self, text: str):
        """Set tooltip text"""
        self.tooltip = text
        self.tooltip_timeout = self.tooltip_delay
    
    def clear_tooltip(self):
        """Clear tooltip"""
        self.tooltip = None
        self.tooltip_timeout = 0.0
    
    def set_cursor(self, cursor_type: int):
        """Set mouse cursor"""
        self.cursor = cursor_type
        pygame.mouse.set_cursor(self.cursor)
    
    def push_modal(self, element: UIElement):
        """Push modal element onto stack"""
        self.modal_stack.append(element)
        self.set_focus(element)
    
    def pop_modal(self):
        """Pop modal element from stack"""
        if self.modal_stack:
            element = self.modal_stack.pop()
            self.set_focus(None)
            return element
        return None
    
    def get_top_modal(self) -> Optional[UIElement]:
        """Get top modal element"""
        return self.modal_stack[-1] if self.modal_stack else None
    
    def handle_event(self, event: pygame.event.Event):
        """Handle pygame event"""
        # Handle mouse motion for tooltips
        if event.type == pygame.MOUSEMOTION:
            self._handle_mouse_motion(event.pos, event.rel)
        
        # Handle mouse button events
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self._handle_mouse_down(event.button, event.pos)
        elif event.type == pygame.MOUSEBUTTONUP:
            self._handle_mouse_up(event.button, event.pos)
        
        # Pass event to elements
        for element in self.elements:
            if element.visible and element.enabled:
                element.handle_event(event)
    
    def _handle_mouse_motion(self, pos: Tuple[int, int], rel: Tuple[int, int]):
        """Handle mouse motion"""
        # Check for hover
        new_hover = None
        for element in self.elements:
            if element.visible and element.enabled and element.contains_point(pos):
                new_hover = element
                break
        
        # Update hover
        if new_hover != self.hover_element:
            # Clear tooltip if mouse moved
            self.clear_tooltip()
            self.set_hover(new_hover)
    
    def _handle_mouse_down(self, button: int, pos: Tuple[int, int]):
        """Handle mouse button down"""
        # Check for clicks on elements
        for element in reversed(self.elements):  # Check from top to bottom
            if element.visible and element.enabled and element.contains_point(pos):
                self.set_focus(element)
                break
    
    def _handle_mouse_up(self, button: int, pos: Tuple[int, int]):
        """Handle mouse button up"""
        pass
    
    def update(self, delta_time: float):
        """Update UI"""
        # Update tooltip timeout
        if self.tooltip:
            self.tooltip_timeout -= delta_time
            if self.tooltip_timeout <= 0:
                self.clear_tooltip()
        
        # Update elements
        for element in self.elements:
            if element.visible:
                element.update(delta_time)
    
    def render(self):
        """Render all UI elements"""
        # Sort elements by z-order (if implemented)
        # For now, just render in order
        
        # Render elements
        for element in self.elements:
            if element.visible:
                element.draw(self.screen)
        
        # Render tooltip
        if self.tooltip:
            self._render_tooltip()
    
    def _render_tooltip(self):
        """Render tooltip"""
        font = pygame.font.SysFont('Arial', 14)
        text_surface = font.render(self.tooltip, True, Colors.WHITE)
        
        # Create background
        padding = 10
        bg_rect = pygame.Rect(
            pygame.mouse.get_pos()[0] + 15,
            pygame.mouse.get_pos()[1] + 15,
            text_surface.get_width() + padding * 2,
            text_surface.get_height() + padding * 2
        )
        
        # Draw background
        pygame.draw.rect(self.screen, Colors.DARK_GRAY, bg_rect)
        pygame.draw.rect(self.screen, Colors.UI_BORDER, bg_rect, 1)
        
        # Draw text
        self.screen.blit(text_surface, 
                        (bg_rect.x + padding, bg_rect.y + padding))
    
    def get_screen_size(self) -> Tuple[int, int]:
        """Get screen size"""
        return (SCREEN_WIDTH, SCREEN_HEIGHT)
    
    def get_mouse_position(self) -> Tuple[int, int]:
        """Get mouse position"""
        return pygame.mouse.get_pos()
    
    def is_key_pressed(self, key: int) -> bool:
        """Check if key is pressed"""
        return pygame.key.get_pressed()[key]


# Global UI manager instance
ui_manager = None
