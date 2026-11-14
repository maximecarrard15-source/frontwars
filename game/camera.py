"""
Camera system for Frontwars
"""

import pygame
import math
from typing import Tuple, Optional
from dataclasses import dataclass

from config import GameSettings, SCREEN_WIDTH, SCREEN_HEIGHT
from utils.vector import Vector2
from utils.helpers import clamp, lerp


@dataclass
class Camera:
    """Game camera that can move, zoom, and rotate"""
    
    position: Vector2 = Vector2(0, 0)  # Center position
    zoom: float = 1.0
    rotation: float = 0.0  # In radians
    
    # Viewport settings
    viewport_width: int = SCREEN_WIDTH
    viewport_height: int = SCREEN_HEIGHT
    
    # Movement settings
    speed: float = GameSettings.CAMERA_SPEED
    zoom_speed: float = GameSettings.CAMERA_ZOOM_SPEED
    rotation_speed: float = 0.05
    
    # Smoothing
    smooth_movement: bool = True
    smooth_zoom: bool = True
    movement_damping: float = 0.9
    zoom_damping: float = 0.9
    
    # Target for following
    target: Optional[Vector2] = None
    follow_distance: float = 5.0
    follow_smoothness: float = 0.1
    
    # Shake effect
    shake_intensity: float = 0.0
    shake_duration: float = 0.0
    shake_decay: float = 0.95
    
    def __post_init__(self):
        # Initialize view matrix
        self._update_view_matrix()
    
    def _update_view_matrix(self):
        """Update the view transformation matrix"""
        # Translation matrix
        tx = -self.position.x * self.zoom
        ty = -self.position.y * self.zoom
        
        # Rotation matrix
        cos_r = math.cos(self.rotation)
        sin_r = math.sin(self.rotation)
        
        # Combined transformation
        self.view_matrix = [
            [cos_r * self.zoom, -sin_r * self.zoom, tx],
            [sin_r * self.zoom, cos_r * self.zoom, ty],
            [0, 0, 1]
        ]
        
        # Inverse matrix for screen to world
        det = self.view_matrix[0][0] * self.view_matrix[1][1] - self.view_matrix[0][1] * self.view_matrix[1][0]
        if det != 0:
            inv_det = 1.0 / det
            self.inv_view_matrix = [
                [self.view_matrix[1][1] * inv_det, -self.view_matrix[0][1] * inv_det, 
                 (self.view_matrix[0][1] * self.view_matrix[1][2] - self.view_matrix[1][1] * self.view_matrix[0][2]) * inv_det],
                [-self.view_matrix[1][0] * inv_det, self.view_matrix[0][0] * inv_det,
                 (self.view_matrix[1][0] * self.view_matrix[0][2] - self.view_matrix[0][0] * self.view_matrix[1][2]) * inv_det],
                [0, 0, 1]
            ]
        else:
            self.inv_view_matrix = [
                [1, 0, 0],
                [0, 1, 0],
                [0, 0, 1]
            ]
    
    def set_position(self, position: Vector2):
        """Set camera position"""
        self.position = position.copy()
        self._update_view_matrix()
    
    def move(self, dx: float, dy: float):
        """Move camera by delta"""
        self.position.x += dx
        self.position.y += dy
        self._update_view_matrix()
    
    def move_to(self, x: float, y: float):
        """Move camera to position"""
        self.position.x = x
        self.position.y = y
        self._update_view_matrix()
    
    def set_zoom(self, zoom: float):
        """Set zoom level"""
        self.zoom = clamp(zoom, GameSettings.CAMERA_MIN_ZOOM, GameSettings.CAMERA_MAX_ZOOM)
        self._update_view_matrix()
    
    def zoom_in(self, amount: float = 1.0):
        """Zoom in"""
        new_zoom = self.zoom * (1.0 + self.zoom_speed * amount)
        self.set_zoom(new_zoom)
    
    def zoom_out(self, amount: float = 1.0):
        """Zoom out"""
        new_zoom = self.zoom * (1.0 - self.zoom_speed * amount)
        self.set_zoom(new_zoom)
    
    def set_rotation(self, rotation: float):
        """Set rotation in radians"""
        self.rotation = rotation
        self._update_view_matrix()
    
    def rotate(self, delta: float):
        """Rotate camera by delta (radians)"""
        self.rotation += delta
        self._update_view_matrix()
    
    def world_to_screen(self, world_pos: Vector2) -> Vector2:
        """Convert world position to screen position"""
        # Apply transformation
        x = self.view_matrix[0][0] * world_pos.x + self.view_matrix[0][1] * world_pos.y + self.view_matrix[0][2]
        y = self.view_matrix[1][0] * world_pos.x + self.view_matrix[1][1] * world_pos.y + self.view_matrix[1][2]
        
        # Add viewport offset
        screen_x = x + self.viewport_width / 2
        screen_y = y + self.viewport_height / 2
        
        # Add shake effect
        if self.shake_intensity > 0:
            import random
            screen_x += random.uniform(-self.shake_intensity, self.shake_intensity)
            screen_y += random.uniform(-self.shake_intensity, self.shake_intensity)
        
        return Vector2(screen_x, screen_y)
    
    def screen_to_world(self, screen_pos: Vector2) -> Vector2:
        """Convert screen position to world position"""
        # Remove viewport offset
        x = screen_pos.x - self.viewport_width / 2
        y = screen_pos.y - self.viewport_height / 2
        
        # Apply inverse transformation
        world_x = self.inv_view_matrix[0][0] * x + self.inv_view_matrix[0][1] * y + self.inv_view_matrix[0][2]
        world_y = self.inv_view_matrix[1][0] * x + self.inv_view_matrix[1][1] * y + self.inv_view_matrix[1][2]
        
        return Vector2(world_x, world_y)
    
    def get_view_rect(self) -> Tuple[float, float, float, float]:
        """Get the rectangle of the visible area in world coordinates"""
        # Get screen corners in world coordinates
        top_left = self.screen_to_world(Vector2(0, 0))
        bottom_right = self.screen_to_world(Vector2(self.viewport_width, self.viewport_height))
        
        return (
            min(top_left.x, bottom_right.x),
            min(top_left.y, bottom_right.y),
            abs(bottom_right.x - top_left.x),
            abs(bottom_right.y - top_left.y)
        )
    
    def is_visible(self, world_pos: Vector2, margin: float = 0) -> bool:
        """Check if world position is visible on screen"""
        view_rect = self.get_view_rect()
        return (view_rect[0] - margin <= world_pos.x <= view_rect[0] + view_rect[2] + margin and
                view_rect[1] - margin <= world_pos.y <= view_rect[1] + view_rect[3] + margin)
    
    def is_visible_rect(self, rect: Tuple[float, float, float, float]) -> bool:
        """Check if rectangle is visible on screen"""
        rx, ry, rw, rh = rect
        
        # Check if any corner is visible
        corners = [
            Vector2(rx, ry),
            Vector2(rx + rw, ry),
            Vector2(rx + rw, ry + rh),
            Vector2(rx, ry + rh)
        ]
        
        for corner in corners:
            if self.is_visible(corner):
                return True
        
        return False
    
    def clamp_to_map(self, map_width: float, map_height: float):
        """Clamp camera to map boundaries"""
        view_rect = self.get_view_rect()
        
        # Clamp position
        if view_rect[2] > map_width:
            self.position.x = map_width / 2
        else:
            self.position.x = clamp(self.position.x, view_rect[2] / 2, map_width - view_rect[2] / 2)
        
        if view_rect[3] > map_height:
            self.position.y = map_height / 2
        else:
            self.position.y = clamp(self.position.y, view_rect[3] / 2, map_height - view_rect[3] / 2)
        
        self._update_view_matrix()
    
    def follow(self, target: Vector2, delta_time: float = 0.016):
        """Follow a target with smoothing"""
        self.target = target
        
        # Calculate desired position
        desired_x = target.x
        desired_y = target.y
        
        # Smooth movement
        if self.smooth_movement:
            self.position.x = lerp(self.position.x, desired_x, self.follow_smoothness)
            self.position.y = lerp(self.position.y, desired_y, self.follow_smoothness)
        else:
            self.position.x = desired_x
            self.position.y = desired_y
        
        self._update_view_matrix()
    
    def stop_following(self):
        """Stop following target"""
        self.target = None
    
    def shake(self, intensity: float = 10.0, duration: float = 0.5):
        """Add camera shake effect"""
        self.shake_intensity = max(self.shake_intensity, intensity)
        self.shake_duration = max(self.shake_duration, duration)
    
    def update_shake(self, delta_time: float):
        """Update shake effect"""
        if self.shake_duration > 0:
            self.shake_duration -= delta_time
            self.shake_intensity *= self.shake_decay
            
            if self.shake_duration <= 0:
                self.shake_intensity = 0
                self.shake_duration = 0
    
    def update(self, delta_time: float):
        """Update camera (shake, following, etc.)"""
        self.update_shake(delta_time)
        
        if self.target:
            self.follow(self.target, delta_time)
    
    def get_viewport_center(self) -> Vector2:
        """Get center of viewport in screen coordinates"""
        return Vector2(self.viewport_width / 2, self.viewport_height / 2)
    
    def get_zoom_level(self) -> float:
        """Get current zoom level"""
        return self.zoom
    
    def get_scale(self) -> float:
        """Get current scale factor"""
        return self.zoom
    
    def copy(self) -> 'Camera':
        """Create a copy of the camera"""
        return Camera(
            position=self.position.copy(),
            zoom=self.zoom,
            rotation=self.rotation,
            viewport_width=self.viewport_width,
            viewport_height=self.viewport_height
        )
    
    def reset(self):
        """Reset camera to default state"""
        self.position = Vector2(0, 0)
        self.zoom = 1.0
        self.rotation = 0.0
        self.target = None
        self.shake_intensity = 0.0
        self.shake_duration = 0.0
        self._update_view_matrix()


class CameraController:
    """Controller for camera input handling"""
    
    def __init__(self, camera: Camera):
        self.camera = camera
        self.drag_start: Optional[Vector2] = None
        self.drag_position: Optional[Vector2] = None
        self.is_dragging = False
        
        # Keyboard movement state
        self.move_up = False
        self.move_down = False
        self.move_left = False
        self.move_right = False
        
        # Mouse wheel zoom
        self.zoom_in = False
        self.zoom_out = False
    
    def handle_event(self, event: pygame.event.Event):
        """Handle pygame event"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 2:  # Middle mouse button
                self.drag_start = Vector2(event.pos[0], event.pos[1])
                self.drag_position = self.camera.screen_to_world(self.drag_start)
                self.is_dragging = True
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 2:
                self.is_dragging = False
                self.drag_start = None
                self.drag_position = None
        
        elif event.type == pygame.MOUSEWHEEL:
            if event.y > 0:
                self.camera.zoom_in(abs(event.y) * 0.1)
            elif event.y < 0:
                self.camera.zoom_out(abs(event.y) * 0.1)
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w:
                self.move_up = True
            elif event.key == pygame.K_s:
                self.move_down = True
            elif event.key == pygame.K_a:
                self.move_left = True
            elif event.key == pygame.K_d:
                self.move_right = True
            elif event.key == pygame.K_q:
                self.camera.rotate(-self.camera.rotation_speed)
            elif event.key == pygame.K_e:
                self.camera.rotate(self.camera.rotation_speed)
            elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                self.camera.zoom_in()
            elif event.key == pygame.K_MINUS:
                self.camera.zoom_out()
        
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_w:
                self.move_up = False
            elif event.key == pygame.K_s:
                self.move_down = False
            elif event.key == pygame.K_a:
                self.move_left = False
            elif event.key == pygame.K_d:
                self.move_right = False
    
    def update(self, delta_time: float):
        """Update camera based on input"""
        # Handle keyboard movement
        speed = self.camera.speed * delta_time * 60
        if self.move_up:
            self.camera.move(0, -speed)
        if self.move_down:
            self.camera.move(0, speed)
        if self.move_left:
            self.camera.move(-speed, 0)
        if self.move_right:
            self.camera.move(speed, 0)
        
        # Handle mouse drag
        if self.is_dragging and self.drag_start:
            mouse_pos = Vector2(pygame.mouse.get_pos())
            current_world = self.camera.screen_to_world(mouse_pos)
            
            if self.drag_position:
                dx = self.drag_position.x - current_world.x
                dy = self.drag_position.y - current_world.y
                self.camera.move(dx, dy)
                self.drag_position = current_world
    
    def set_camera(self, camera: Camera):
        """Set the camera to control"""
        self.camera = camera
