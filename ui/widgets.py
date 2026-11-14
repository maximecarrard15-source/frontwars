"""
UI Widgets for Frontwars
"""

import pygame
from typing import List, Tuple, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

from config import Colors, SCREEN_WIDTH, SCREEN_HEIGHT
from utils.logger import logger
from .ui_manager import UIElement, ui_manager


class WidgetState(Enum):
    NORMAL = "normal"
    HOVER = "hover"
    ACTIVE = "active"
    DISABLED = "disabled"


@dataclass
class Widget(UIElement):
    """Base widget class"""
    state: WidgetState = WidgetState.NORMAL
    color: Tuple[int, int, int] = Colors.UI_PANEL
    hover_color: Tuple[int, int, int] = Colors.UI_BUTTON_HOVER
    active_color: Tuple[int, int, int] = Colors.UI_BUTTON_ACTIVE
    disabled_color: Tuple[int, int, int] = Colors.GRAY
    border_color: Tuple[int, int, int] = Colors.UI_BORDER
    border_width: int = 1
    padding: int = 5
    
    def __post_init__(self):
        super().__init__()
    
    def get_color(self) -> Tuple[int, int, int]:
        """Get current color based on state"""
        if self.state == WidgetState.DISABLED:
            return self.disabled_color
        elif self.state == WidgetState.ACTIVE:
            return self.active_color
        elif self.state == WidgetState.HOVER:
            return self.hover_color
        return self.color
    
    def set_state(self, state: WidgetState):
        """Set widget state"""
        self.state = state
    
    def enable(self):
        """Enable widget"""
        self.enabled = True
        if self.state == WidgetState.DISABLED:
            self.state = WidgetState.NORMAL
    
    def disable(self):
        """Disable widget"""
        self.enabled = False
        self.state = WidgetState.DISABLED
    
    def draw(self, surface: pygame.Surface):
        """Draw widget"""
        if not self.visible:
            return
        
        # Draw background
        color = self.get_color()
        rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, color, rect)
        
        # Draw border
        if self.border_width > 0:
            pygame.draw.rect(surface, self.border_color, rect, self.border_width)
    
    def handle_event(self, event: pygame.event.Event):
        """Handle event"""
        if not self.visible or not self.enabled:
            return
        
        if event.type == pygame.MOUSEMOTION:
            if self.contains_point(event.pos):
                self.set_state(WidgetState.HOVER)
            else:
                self.set_state(WidgetState.NORMAL)
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.contains_point(event.pos):
                self.set_state(WidgetState.ACTIVE)
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.set_state(WidgetState.HOVER if self.contains_point(event.pos) else WidgetState.NORMAL)


class Button(Widget):
    """Button widget"""
    
    def __init__(self, x: int, y: int, width: int, height: int,
                 text: str = "", on_click: Optional[Callable] = None,
                 font_size: int = 16, text_color: Tuple[int, int, int] = Colors.UI_TEXT):
        super().__init__(x, y, width, height)
        self.text = text
        self.on_click = on_click
        self.font_size = font_size
        self.text_color = text_color
        self.font = pygame.font.SysFont('Arial', font_size)
        self.text_surface = self.font.render(text, True, text_color)
    
    def draw(self, surface: pygame.Surface):
        """Draw button"""
        super().draw(surface)
        
        # Draw text
        if self.text:
            text_rect = self.text_surface.get_rect()
            text_rect.center = (self.x + self.width // 2, self.y + self.height // 2)
            surface.blit(self.text_surface, text_rect)
    
    def handle_event(self, event: pygame.event.Event):
        """Handle event"""
        super().handle_event(event)
        
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.contains_point(event.pos) and self.on_click:
                self.on_click()
    
    def set_text(self, text: str):
        """Set button text"""
        self.text = text
        self.text_surface = self.font.render(text, True, self.text_color)


class Label(Widget):
    """Label widget"""
    
    def __init__(self, x: int, y: int, text: str = "",
                 font_size: int = 16, text_color: Tuple[int, int, int] = Colors.UI_TEXT,
                 background_color: Optional[Tuple[int, int, int]] = None):
        self.text = text
        self.font_size = font_size
        self.text_color = text_color
        self.background_color = background_color
        self.font = pygame.font.SysFont('Arial', font_size)
        self.text_surface = self.font.render(text, True, text_color)
        
        # Calculate size based on text
        width = self.text_surface.get_width()
        height = self.text_surface.get_height()
        
        super().__init__(x, y, width, height)
        
        # Override colors
        self.color = background_color if background_color else Colors.TRANSPARENT
        self.border_width = 0
    
    def draw(self, surface: pygame.Surface):
        """Draw label"""
        if self.background_color:
            rect = pygame.Rect(self.x, self.y, self.width, self.height)
            pygame.draw.rect(surface, self.background_color, rect)
        
        surface.blit(self.text_surface, (self.x, self.y))
    
    def set_text(self, text: str):
        """Set label text"""
        self.text = text
        self.text_surface = self.font.render(text, True, self.text_color)
        self.width = self.text_surface.get_width()
        self.height = self.text_surface.get_height()


class Panel(Widget):
    """Panel widget (container for other widgets)"""
    
    def __init__(self, x: int, y: int, width: int, height: int,
                 title: str = "", border_width: int = 1):
        super().__init__(x, y, width, height)
        self.title = title
        self.title_height = 25
        self.border_width = border_width
        self.children: List[Widget] = []
        self.font = pygame.font.SysFont('Arial', 14)
    
    def add_child(self, widget: Widget):
        """Add child widget"""
        self.children.append(widget)
    
    def remove_child(self, widget: Widget):
        """Remove child widget"""
        if widget in self.children:
            self.children.remove(widget)
    
    def draw(self, surface: pygame.Surface):
        """Draw panel"""
        # Draw background
        rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, self.color, rect)
        
        # Draw border
        if self.border_width > 0:
            pygame.draw.rect(surface, self.border_color, rect, self.border_width)
        
        # Draw title
        if self.title:
            title_surface = self.font.render(self.title, True, Colors.UI_TEXT)
            title_rect = pygame.Rect(self.x, self.y, self.width, self.title_height)
            pygame.draw.rect(surface, Colors.UI_PANEL, title_rect)
            pygame.draw.rect(surface, self.border_color, title_rect, 1)
            surface.blit(title_surface, (self.x + 5, self.y + 5))
        
        # Draw children
        for child in self.children:
            if child.visible:
                child.draw(surface)
    
    def handle_event(self, event: pygame.event.Event):
        """Handle event"""
        super().handle_event(event)
        
        # Pass event to children
        for child in self.children:
            if child.visible and child.enabled:
                child.handle_event(event)


class ProgressBar(Widget):
    """Progress bar widget"""
    
    def __init__(self, x: int, y: int, width: int, height: int,
                 progress: float = 0.0, max_progress: float = 100.0,
                 bar_color: Tuple[int, int, int] = Colors.GREEN,
                 background_color: Tuple[int, int, int] = Colors.DARK_GRAY):
        super().__init__(x, y, width, height)
        self.progress = progress
        self.max_progress = max_progress
        self.bar_color = bar_color
        self.background_color = background_color
        self.border_width = 1
    
    def draw(self, surface: pygame.Surface):
        """Draw progress bar"""
        # Draw background
        rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, self.background_color, rect)
        
        # Draw border
        pygame.draw.rect(surface, self.border_color, rect, self.border_width)
        
        # Draw progress bar
        progress_percent = min(1.0, max(0.0, self.progress / self.max_progress))
        bar_width = int(self.width * progress_percent)
        bar_rect = pygame.Rect(self.x, self.y, bar_width, self.height)
        pygame.draw.rect(surface, self.bar_color, bar_rect)
    
    def set_progress(self, progress: float):
        """Set progress value"""
        self.progress = progress
    
    def set_max_progress(self, max_progress: float):
        """Set maximum progress"""
        self.max_progress = max_progress
    
    def get_progress_percentage(self) -> float:
        """Get progress as percentage"""
        return (self.progress / self.max_progress) * 100 if self.max_progress > 0 else 0.0


class Image(Widget):
    """Image widget"""
    
    def __init__(self, x: int, y: int, image: pygame.Surface):
        width = image.get_width()
        height = image.get_height()
        super().__init__(x, y, width, height)
        self.image = image
    
    def draw(self, surface: pygame.Surface):
        """Draw image"""
        surface.blit(self.image, (self.x, self.y))
    
    def set_image(self, image: pygame.Surface):
        """Set image"""
        self.image = image
        self.width = image.get_width()
        self.height = image.get_height()


class TextInput(Widget):
    """Text input widget"""
    
    def __init__(self, x: int, y: int, width: int, height: int,
                 placeholder: str = "", font_size: int = 16):
        super().__init__(x, y, width, height)
        self.placeholder = placeholder
        self.text = ""
        self.font_size = font_size
        self.font = pygame.font.SysFont('Arial', font_size)
        self.active = False
        self.cursor_position = 0
        self.cursor_visible = True
        self.cursor_timer = 0.0
        self.cursor_blink_rate = 0.5
    
    def draw(self, surface: pygame.Surface):
        """Draw text input"""
        # Draw background
        rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, self.color, rect)
        
        # Draw border
        border_color = Colors.UI_BUTTON_ACTIVE if self.active else self.border_color
        pygame.draw.rect(surface, border_color, rect, self.border_width)
        
        # Draw text or placeholder
        text_to_render = self.text if self.text else self.placeholder
        text_color = Colors.UI_TEXT_DARK if self.text else Colors.GRAY
        text_surface = self.font.render(text_to_render, True, text_color)
        
        # Draw text
        surface.blit(text_surface, (self.x + 5, self.y + self.height // 2 - text_surface.get_height() // 2))
        
        # Draw cursor if active
        if self.active and self.cursor_visible:
            cursor_x = self.x + 5 + self.font.size(self.text[:self.cursor_position])[0]
            cursor_y = self.y + 5
            cursor_height = self.height - 10
            pygame.draw.line(surface, Colors.WHITE,
                           (cursor_x, cursor_y), (cursor_x, cursor_y + cursor_height), 2)
    
    def handle_event(self, event: pygame.event.Event):
        """Handle event"""
        super().handle_event(event)
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.contains_point(event.pos):
                self.active = True
                # Calculate cursor position based on click
                click_x = event.pos[0] - self.x - 5
                for i, char in enumerate(self.text):
                    char_width = self.font.size(char)[0]
                    if click_x <= char_width:
                        self.cursor_position = i
                        break
                    click_x -= char_width
                else:
                    self.cursor_position = len(self.text)
            else:
                self.active = False
        
        elif event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    self.active = False
                elif event.key == pygame.K_BACKSPACE:
                    if self.cursor_position > 0:
                        self.text = self.text[:self.cursor_position - 1] + self.text[self.cursor_position:]
                        self.cursor_position -= 1
                elif event.key == pygame.K_DELETE:
                    if self.cursor_position < len(self.text):
                        self.text = self.text[:self.cursor_position] + self.text[self.cursor_position + 1:]
                elif event.key == pygame.K_LEFT:
                    self.cursor_position = max(0, self.cursor_position - 1)
                elif event.key == pygame.K_RIGHT:
                    self.cursor_position = min(len(self.text), self.cursor_position + 1)
                elif event.key == pygame.K_HOME:
                    self.cursor_position = 0
                elif event.key == pygame.K_END:
                    self.cursor_position = len(self.text)
                elif event.unicode.isprintable():
                    self.text = self.text[:self.cursor_position] + event.unicode + self.text[self.cursor_position:]
                    self.cursor_position += 1
    
    def update(self, delta_time: float):
        """Update text input"""
        self.cursor_timer += delta_time
        if self.cursor_timer >= self.cursor_blink_rate:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0.0
    
    def get_text(self) -> str:
        """Get text"""
        return self.text
    
    def set_text(self, text: str):
        """Set text"""
        self.text = text
        self.cursor_position = len(text)


class ListBox(Widget):
    """List box widget"""
    
    def __init__(self, x: int, y: int, width: int, height: int,
                 items: List[str] = None, font_size: int = 14):
        super().__init__(x, y, width, height)
        self.items = items or []
        self.font_size = font_size
        self.font = pygame.font.SysFont('Arial', font_size)
        self.selected_index = -1
        self.scroll_position = 0
        self.item_height = font_size + 4
        self.visible_items = height // self.item_height
    
    def draw(self, surface: pygame.Surface):
        """Draw list box"""
        # Draw background
        rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, self.color, rect)
        
        # Draw border
        pygame.draw.rect(surface, self.border_color, rect, self.border_width)
        
        # Draw items
        for i in range(self.scroll_position, min(self.scroll_position + self.visible_items, len(self.items))):
            item = self.items[i]
            item_y = self.y + (i - self.scroll_position) * self.item_height
            
            # Draw selection
            if i == self.selected_index:
                pygame.draw.rect(surface, Colors.UI_BUTTON_HOVER,
                               (self.x, item_y, self.width, self.item_height))
            
            # Draw text
            text_surface = self.font.render(item, True, Colors.UI_TEXT)
            surface.blit(text_surface, (self.x + 5, item_y + 2))
    
    def handle_event(self, event: pygame.event.Event):
        """Handle event"""
        super().handle_event(event)
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.contains_point(event.pos):
                # Calculate clicked item
                rel_y = event.pos[1] - self.y
                item_index = self.scroll_position + rel_y // self.item_height
                if 0 <= item_index < len(self.items):
                    self.selected_index = item_index
    
    def set_items(self, items: List[str]):
        """Set items"""
        self.items = items
        self.selected_index = -1
        self.scroll_position = 0
    
    def add_item(self, item: str):
        """Add item"""
        self.items.append(item)
    
    def remove_item(self, index: int):
        """Remove item"""
        if 0 <= index < len(self.items):
            self.items.pop(index)
            if self.selected_index >= index:
                self.selected_index -= 1
    
    def get_selected_item(self) -> Optional[str]:
        """Get selected item"""
        if 0 <= self.selected_index < len(self.items):
            return self.items[self.selected_index]
        return None
    
    def get_selected_index(self) -> int:
        """Get selected index"""
        return self.selected_index


class Checkbox(Widget):
    """Checkbox widget"""
    
    def __init__(self, x: int, y: int, checked: bool = False,
                 label: str = "", on_change: Optional[Callable[[bool], None]] = None):
        self.checked = checked
        self.label = label
        self.on_change = on_change
        
        # Calculate size based on label
        font = pygame.font.SysFont('Arial', 14)
        label_surface = font.render(label, True, Colors.UI_TEXT)
        label_width = label_surface.get_width()
        
        width = 20 + (label_width + 10 if label else 0)
        height = max(20, label_surface.get_height() + 4)
        
        super().__init__(x, y, width, height)
        self.font = font
        self.box_size = 16
    
    def draw(self, surface: pygame.Surface):
        """Draw checkbox"""
        # Draw label
        if self.label:
            label_surface = self.font.render(self.label, True, Colors.UI_TEXT)
            surface.blit(label_surface, (self.x + self.box_size + 5, 
                                        self.y + self.height // 2 - label_surface.get_height() // 2))
        
        # Draw checkbox
        box_rect = pygame.Rect(self.x, self.y + self.height // 2 - self.box_size // 2,
                              self.box_size, self.box_size)
        pygame.draw.rect(surface, self.color, box_rect)
        pygame.draw.rect(surface, self.border_color, box_rect, 1)
        
        # Draw check mark if checked
        if self.checked:
            pygame.draw.line(surface, Colors.UI_TEXT,
                           (box_rect.x + 2, box_rect.y + self.box_size // 2),
                           (box_rect.x + self.box_size // 2, box_rect.y + self.box_size - 2), 2)
            pygame.draw.line(surface, Colors.UI_TEXT,
                           (box_rect.x + self.box_size // 2, box_rect.y + self.box_size - 2),
                           (box_rect.x + self.box_size - 2, box_rect.y + 2), 2)
    
    def handle_event(self, event: pygame.event.Event):
        """Handle event"""
        super().handle_event(event)
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.contains_point(event.pos):
                self.checked = not self.checked
                if self.on_change:
                    self.on_change(self.checked)
    
    def set_checked(self, checked: bool):
        """Set checked state"""
        self.checked = checked
    
    def is_checked(self) -> bool:
        """Check if checked"""
        return self.checked


class Slider(Widget):
    """Slider widget"""
    
    def __init__(self, x: int, y: int, width: int, height: int,
                 min_value: float = 0.0, max_value: float = 100.0, value: float = 50.0,
                 on_change: Optional[Callable[[float], None]] = None):
        super().__init__(x, y, width, height)
        self.min_value = min_value
        self.max_value = max_value
        self.value = value
        self.on_change = on_change
        self.thumb_size = 16
        self.dragging = False
    
    def draw(self, surface: pygame.Surface):
        """Draw slider"""
        # Draw track
        track_height = self.height // 4
        track_y = self.y + self.height // 2 - track_height // 2
        track_rect = pygame.Rect(self.x, track_y, self.width, track_height)
        pygame.draw.rect(surface, Colors.DARK_GRAY, track_rect)
        
        # Draw progress
        progress = (self.value - self.min_value) / (self.max_value - self.min_value)
        progress_width = int(self.width * progress)
        progress_rect = pygame.Rect(self.x, track_y, progress_width, track_height)
        pygame.draw.rect(surface, Colors.BLUE, progress_rect)
        
        # Draw thumb
        thumb_x = self.x + int(progress * (self.width - self.thumb_size))
        thumb_rect = pygame.Rect(thumb_x, track_y - (self.thumb_size - track_height) // 2,
                              self.thumb_size, self.thumb_size)
        pygame.draw.rect(surface, Colors.WHITE, thumb_rect)
        pygame.draw.rect(surface, Colors.GRAY, thumb_rect, 1)
    
    def handle_event(self, event: pygame.event.Event):
        """Handle event"""
        super().handle_event(event)
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.contains_point(event.pos):
                self.dragging = True
                self._update_value_from_mouse(event.pos[0])
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = False
        
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self._update_value_from_mouse(event.pos[0])
    
    def _update_value_from_mouse(self, mouse_x: int):
        """Update value based on mouse position"""
        rel_x = mouse_x - self.x
        progress = max(0, min(1, rel_x / (self.width - self.thumb_size)))
        self.value = self.min_value + progress * (self.max_value - self.min_value)
        
        if self.on_change:
            self.on_change(self.value)
    
    def set_value(self, value: float):
        """Set value"""
        self.value = max(self.min_value, min(self.max_value, value))
    
    def get_value(self) -> float:
        """Get value"""
        return self.value


class Minimap(Widget):
    """Minimap widget"""
    
    def __init__(self, x: int, y: int, width: int, height: int,
                 game_map = None, camera = None):
        super().__init__(x, y, width, height)
        self.game_map = game_map
        self.camera = camera
        self.border_width = 2
    
    def draw(self, surface: pygame.Surface):
        """Draw minimap"""
        if not self.game_map:
            return
        
        # Draw background
        rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, Colors.BLACK, rect)
        
        # Draw border
        pygame.draw.rect(surface, Colors.WHITE, rect, self.border_width)
        
        # Draw map
        if self.game_map:
            self._draw_map(surface, rect)
        
        # Draw camera viewport
        if self.camera:
            self._draw_camera_viewport(surface, rect)
    
    def _draw_map(self, surface: pygame.Surface, rect: pygame.Rect):
        """Draw map on minimap"""
        # Calculate scale
        map_width = self.game_map.width
        map_height = self.game_map.height
        scale_x = self.width / map_width
        scale_y = self.height / map_height
        
        # Draw terrain (simplified)
        for y in range(0, map_height, max(1, int(2 / scale_y))):
            for x in range(0, map_width, max(1, int(2 / scale_x))):
                cell = self.game_map.get_cell(x, y)
                if cell:
                    # Get color
                    color = cell.get_color()
                    
                    # Draw pixel
                    screen_x = self.x + int(x * scale_x)
                    screen_y = self.y + int(y * scale_y)
                    
                    # Draw small rectangle for each cell
                    cell_size = max(1, int(scale_x), int(scale_y))
                    cell_rect = pygame.Rect(screen_x, screen_y, cell_size, cell_size)
                    pygame.draw.rect(surface, color, cell_rect)
    
    def _draw_camera_viewport(self, surface: pygame.Surface, rect: pygame.Rect):
        """Draw camera viewport on minimap"""
        if not self.camera or not self.game_map:
            return
        
        # Get camera view rect in world coordinates
        view_rect = self.camera.get_view_rect()
        
        # Calculate scale
        map_width = self.game_map.width
        map_height = self.game_map.height
        scale_x = self.width / map_width
        scale_y = self.height / map_height
        
        # Convert to minimap coordinates
        minimap_x = self.x + int(view_rect[0] * scale_x)
        minimap_y = self.y + int(view_rect[1] * scale_y)
        minimap_width = int(view_rect[2] * scale_x)
        minimap_height = int(view_rect[3] * scale_y)
        
        # Draw viewport rectangle
        viewport_rect = pygame.Rect(minimap_x, minimap_y, minimap_width, minimap_height)
        pygame.draw.rect(surface, Colors.WHITE, viewport_rect, 1)
    
    def handle_event(self, event: pygame.event.Event):
        """Handle event"""
        super().handle_event(event)
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.contains_point(event.pos):
                self._handle_click(event.pos)
    
    def _handle_click(self, pos: Tuple[int, int]):
        """Handle click on minimap"""
        if not self.camera or not self.game_map:
            return
        
        # Calculate click position in world coordinates
        map_width = self.game_map.width
        map_height = self.game_map.height
        
        rel_x = pos[0] - self.x
        rel_y = pos[1] - self.y
        
        world_x = (rel_x / self.width) * map_width
        world_y = (rel_y / self.height) * map_height
        
        # Move camera to clicked position
        self.camera.move_to(world_x, world_y)
    
    def set_game_map(self, game_map):
        """Set game map"""
        self.game_map = game_map
    
    def set_camera(self, camera):
        """Set camera"""
        self.camera = camera
