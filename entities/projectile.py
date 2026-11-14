"""
Projectile system for Frontwars
"""

import math
from typing import Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import pygame

from config import Colors
from utils.vector import Vector2
from utils.helpers import distance
from .unit import Unit


class ProjectileType(Enum):
    BULLET = "bullet"
    SHELL = "shell"
    MISSILE = "missile"
    LASER = "laser"
    EXPLOSION = "explosion"
    FLAME = "flame"


@dataclass
class ProjectileConfig:
    """Configuration for projectile types"""
    projectile_type: ProjectileType
    speed: float = 10.0
    damage: float = 10.0
    size: float = 0.2
    color: Tuple[int, int, int] = Colors.WHITE
    lifetime: float = 5.0  # Maximum lifetime in seconds
    pierce: bool = False  # Can pierce through multiple targets
    splash: bool = False  # Has splash damage
    splash_radius: float = 0.0
    homing: bool = False  # Homes in on target
    homing_strength: float = 1.0
    
    # Visual
    sprite: str = ""
    trail: bool = False
    trail_length: int = 5


# Default projectile configurations
DEFAULT_PROJECTILE_CONFIGS = {
    ProjectileType.BULLET: ProjectileConfig(
        projectile_type=ProjectileType.BULLET,
        speed=15.0,
        damage=10.0,
        size=0.15,
        color=Colors.YELLOW,
        lifetime=2.0,
        pierce=False
    ),
    ProjectileType.SHELL: ProjectileConfig(
        projectile_type=ProjectileType.SHELL,
        speed=8.0,
        damage=40.0,
        size=0.3,
        color=Colors.ORANGE,
        lifetime=3.0,
        splash=True,
        splash_radius=2.0
    ),
    ProjectileType.MISSILE: ProjectileConfig(
        projectile_type=ProjectileType.MISSILE,
        speed=6.0,
        damage=50.0,
        size=0.4,
        color=Colors.RED,
        lifetime=4.0,
        homing=True,
        homing_strength=2.0,
        splash=True,
        splash_radius=3.0
    ),
    ProjectileType.LASER: ProjectileConfig(
        projectile_type=ProjectileType.LASER,
        speed=20.0,
        damage=25.0,
        size=0.1,
        color=Colors.BLUE,
        lifetime=0.5,
        pierce=True
    ),
    ProjectileType.EXPLOSION: ProjectileConfig(
        projectile_type=ProjectileType.EXPLOSION,
        speed=0.0,
        damage=80.0,
        size=1.0,
        color=Colors.RED,
        lifetime=0.5,
        splash=True,
        splash_radius=4.0
    ),
    ProjectileType.FLAME: ProjectileConfig(
        projectile_type=ProjectileType.FLAME,
        speed=5.0,
        damage=5.0,
        size=0.5,
        color=Colors.ORANGE,
        lifetime=1.0,
        splash=True,
        splash_radius=1.5
    )
}


class Projectile:
    """Projectile that travels from source to target"""
    
    def __init__(self,
                 projectile_type: ProjectileType,
                 source: Vector2,
                 target: Vector2,
                 damage: float = 0.0,
                 shooter: Optional[Unit] = None,
                 target_unit: Optional[Unit] = None,
                 config: ProjectileConfig = None):
        self.id = id(self)
        self.projectile_type = projectile_type
        self.config = config or DEFAULT_PROJECTILE_CONFIGS.get(projectile_type, DEFAULT_PROJECTILE_CONFIGS[ProjectileType.BULLET])
        
        # Position and movement
        self.position = source.copy()
        self.source = source.copy()
        self.target = target.copy()
        self.velocity = self._calculate_velocity()
        
        # Combat
        self.damage = damage or self.config.damage
        self.shooter = shooter
        self.target_unit = target_unit
        self.has_hit = False
        
        # Lifetime
        self.lifetime = self.config.lifetime
        self.age = 0.0
        
        # Visual
        self.color = self.config.color
        self.size = self.config.size
        
        # Trail
        self.trail: list = []
        self.max_trail_length = self.config.trail_length if self.config.trail else 0
    
    def _calculate_velocity(self) -> Vector2:
        """Calculate initial velocity"""
        direction = (self.target - self.position).normalize()
        return direction * self.config.speed
    
    def update(self, delta_time: float):
        """Update projectile position"""
        self.age += delta_time
        
        # Check lifetime
        if self.age >= self.lifetime:
            self.has_hit = True
            return
        
        # Update position
        self.position += self.velocity * delta_time * 60
        
        # Add to trail
        if self.max_trail_length > 0:
            self.trail.append(self.position.copy())
            if len(self.trail) > self.max_trail_length:
                self.trail.pop(0)
        
        # Homing behavior
        if self.config.homing and self.target_unit and self.target_unit.is_alive:
            self._apply_homing(delta_time)
        
        # Check for collision
        self._check_collision()
    
    def _apply_homing(self, delta_time: float):
        """Apply homing behavior towards target"""
        if not self.target_unit:
            return
        
        # Calculate direction to target
        direction_to_target = (self.target_unit.position - self.position).normalize()
        
        # Interpolate between current velocity and target direction
        homing_factor = self.config.homing_strength * delta_time
        new_direction = self.velocity.normalize().lerp(direction_to_target, homing_factor)
        
        # Update velocity
        self.velocity = new_direction * self.config.speed
    
    def _check_collision(self):
        """Check for collision with target or other units"""
        if not self.target_unit:
            return
        
        # Check distance to target
        dist = self.position.distance_to(self.target_unit.position)
        
        # Simple collision check (could be more sophisticated)
        if dist < self.target_unit.collision_radius + self.size:
            self.hit(self.target_unit)
    
    def hit(self, unit: Unit):
        """Projectile hits a unit"""
        if self.has_hit:
            return
        
        self.has_hit = True
        
        # Apply damage
        unit.take_damage(self.damage, self.shooter)
        
        # Apply splash damage if enabled
        if self.config.splash and self.target_unit:
            self._apply_splash_damage()
        
        # Don't pierce by default
        if not self.config.pierce:
            self.has_hit = True
    
    def _apply_splash_damage(self):
        """Apply splash damage to nearby units"""
        if not self.target_unit or not self.target_unit.team:
            return
        
        # Get all units near impact point
        impact_point = self.target_unit.position
        
        # This would need access to all units in the game
        # For now, just a placeholder
        pass
    
    def is_alive(self) -> bool:
        """Check if projectile is still active"""
        return not self.has_hit and self.age < self.lifetime
    
    def draw(self, surface: pygame.Surface, camera):
        """Draw projectile on surface"""
        screen_pos = camera.world_to_screen(self.position)
        
        # Draw trail
        if self.trail and camera.zoom > 0.5:
            for i, trail_pos in enumerate(self.trail):
                alpha = int(255 * (i + 1) / len(self.trail))
                screen_trail_pos = camera.world_to_screen(trail_pos)
                
                # Draw trail point
                trail_size = int(self.size * camera.zoom * 2 * (i + 1) / len(self.trail))
                if trail_size > 0:
                    s = pygame.Surface((trail_size * 2, trail_size * 2), pygame.SRCALPHA)
                    color = (*self.color, alpha // 2)
                    pygame.draw.circle(s, color, (trail_size, trail_size), trail_size)
                    surface.blit(s, (int(screen_trail_pos.x - trail_size), int(screen_trail_pos.y - trail_size)))
        
        # Draw projectile
        radius = int(self.size * camera.zoom * 4)
        
        if self.projectile_type == ProjectileType.LASER:
            # Draw laser line
            if len(self.trail) > 0:
                start_pos = camera.world_to_screen(self.trail[0] if self.trail else self.source)
                pygame.draw.line(surface, self.color,
                               (int(start_pos.x), int(start_pos.y)),
                               (int(screen_pos.x), int(screen_pos.y)),
                               max(1, radius // 2))
        
        # Draw projectile body
        if radius > 0:
            if self.projectile_type == ProjectileType.EXPLOSION:
                # Draw explosion (larger, with fading)
                alpha = int(255 * (1.0 - self.age / self.lifetime))
                s = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
                color = (*self.color, alpha)
                pygame.draw.circle(s, color, (radius * 2, radius * 2), radius * 2)
                surface.blit(s, (int(screen_pos.x - radius * 2), int(screen_pos.y - radius * 2)))
            else:
                # Draw regular projectile
                pygame.draw.circle(surface, self.color,
                                  (int(screen_pos.x), int(screen_pos.y)), radius)
                
                # Add outline for better visibility
                if camera.zoom > 0.5:
                    pygame.draw.circle(surface, Colors.WHITE,
                                      (int(screen_pos.x), int(screen_pos.y)), radius, 1)
    
    def __str__(self) -> str:
        return f"Projectile({self.projectile_type.value}, damage={self.damage:.1f})"


class ProjectileManager:
    """Manages all projectiles in the game"""
    
    def __init__(self):
        self.projectiles: list = []
        self.max_projectiles = 500
    
    def add_projectile(self, projectile: Projectile):
        """Add a projectile"""
        if len(self.projectiles) >= self.max_projectiles:
            # Remove oldest projectile
            self.projectiles.pop(0)
        
        self.projectiles.append(projectile)
    
    def create_projectile(self,
                         projectile_type: ProjectileType,
                         source: Vector2,
                         target: Vector2,
                         damage: float = 0.0,
                         shooter: Unit = None,
                         target_unit: Unit = None) -> Projectile:
        """Create and add a new projectile"""
        projectile = Projectile(
            projectile_type=projectile_type,
            source=source,
            target=target,
            damage=damage,
            shooter=shooter,
            target_unit=target_unit
        )
        self.add_projectile(projectile)
        return projectile
    
    def update(self, delta_time: float):
        """Update all projectiles"""
        # Update existing projectiles
        for projectile in self.projectiles[:]:
            projectile.update(delta_time)
        
        # Remove dead projectiles
        self.projectiles = [p for p in self.projectiles if p.is_alive()]
    
    def draw(self, surface: pygame.Surface, camera):
        """Draw all projectiles"""
        for projectile in self.projectiles:
            projectile.draw(surface, camera)
    
    def clear(self):
        """Clear all projectiles"""
        self.projectiles.clear()
    
    def get_projectile_count(self) -> int:
        """Get number of active projectiles"""
        return len(self.projectiles)


# Global projectile manager
projectile_manager = ProjectileManager()
