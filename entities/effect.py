"""
Effect system for Frontwars (visual and gameplay effects)
"""

import math
import random
from typing import List, Tuple, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum, auto
import pygame

from config import Colors
from utils.vector import Vector2
from utils.helpers import lerp, distance
from utils.logger import logger


class EffectType(Enum):
    EXPLOSION = auto()
    FIRE = auto()
    SMOKE = auto()
    SPARKS = auto()
    BLOOD = auto()
    HEAL = auto()
    SHIELD = auto()
    STUN = auto()
    BUFF = auto()
    DEBUFF = auto()
    TELEPORT = auto()
    PARTICLE = auto()


class EffectState(Enum):
    ACTIVE = auto()
    FADING = auto()
    COMPLETE = auto()


@dataclass
class EffectConfig:
    """Configuration for effect types"""
    effect_type: EffectType
    duration: float = 1.0
    size: float = 1.0
    color: Tuple[int, int, int] = Colors.WHITE
    particle_count: int = 10
    particle_speed: float = 2.0
    particle_size: float = 0.2
    fade_out: bool = True
    sound: str = ""
    
    # Behavior
    applies_damage: bool = False
    damage: float = 0.0
    applies_healing: bool = False
    healing: float = 0.0
    applies_status: Optional[str] = None
    status_duration: float = 0.0


# Default effect configurations
DEFAULT_EFFECT_CONFIGS = {
    EffectType.EXPLOSION: EffectConfig(
        effect_type=EffectType.EXPLOSION,
        duration=0.8,
        size=3.0,
        color=Colors.ORANGE,
        particle_count=30,
        particle_speed=5.0,
        particle_size=0.3,
        fade_out=True,
        sound="explosion.wav",
        applies_damage=True,
        damage=50.0
    ),
    EffectType.FIRE: EffectConfig(
        effect_type=EffectType.FIRE,
        duration=2.0,
        size=2.0,
        color=Colors.RED,
        particle_count=20,
        particle_speed=3.0,
        particle_size=0.4,
        fade_out=True,
        sound="fire.wav",
        applies_damage=True,
        damage=10.0
    ),
    EffectType.SMOKE: EffectConfig(
        effect_type=EffectType.SMOKE,
        duration=3.0,
        size=2.5,
        color=(100, 100, 100),
        particle_count=15,
        particle_speed=1.0,
        particle_size=0.5,
        fade_out=True
    ),
    EffectType.SPARKS: EffectConfig(
        effect_type=EffectType.SPARKS,
        duration=0.5,
        size=1.0,
        color=Colors.YELLOW,
        particle_count=20,
        particle_speed=8.0,
        particle_size=0.15,
        fade_out=True
    ),
    EffectType.BLOOD: EffectConfig(
        effect_type=EffectType.BLOOD,
        duration=1.0,
        size=1.0,
        color=(150, 0, 0),
        particle_count=10,
        particle_speed=3.0,
        particle_size=0.2,
        fade_out=True
    ),
    EffectType.HEAL: EffectConfig(
        effect_type=EffectType.HEAL,
        duration=1.0,
        size=1.5,
        color=Colors.GREEN,
        particle_count=15,
        particle_speed=2.0,
        particle_size=0.25,
        fade_out=True,
        sound="heal.wav",
        applies_healing=True,
        healing=25.0
    ),
    EffectType.SHIELD: EffectConfig(
        effect_type=EffectType.SHIELD,
        duration=2.0,
        size=2.0,
        color=Colors.BLUE,
        particle_count=0,
        fade_out=True,
        sound="shield.wav"
    ),
    EffectType.STUN: EffectConfig(
        effect_type=EffectType.STUN,
        duration=3.0,
        size=1.5,
        color=Colors.PURPLE,
        particle_count=10,
        fade_out=True,
        sound="stun.wav",
        applies_status="stun",
        status_duration=3.0
    ),
    EffectType.BUFF: EffectConfig(
        effect_type=EffectType.BUFF,
        duration=5.0,
        size=1.0,
        color=Colors.GOLD,
        particle_count=5,
        fade_out=True,
        sound="buff.wav"
    ),
    EffectType.DEBUFF: EffectConfig(
        effect_type=EffectType.DEBUFF,
        duration=5.0,
        size=1.0,
        color=(50, 50, 50),
        particle_count=5,
        fade_out=True,
        sound="debuff.wav"
    ),
    EffectType.TELEPORT: EffectConfig(
        effect_type=EffectType.TELEPORT,
        duration=0.5,
        size=1.5,
        color=Colors.WHITE,
        particle_count=20,
        fade_out=True,
        sound="teleport.wav"
    )
}


@dataclass
class Particle:
    """Single particle in an effect"""
    position: Vector2
    velocity: Vector2
    size: float
    color: Tuple[int, int, int]
    lifetime: float
    age: float = 0.0
    gravity: float = 0.0
    drag: float = 0.0
    
    def update(self, delta_time: float):
        """Update particle"""
        self.age += delta_time
        
        # Apply gravity
        if self.gravity != 0:
            self.velocity.y += self.gravity * delta_time
        
        # Apply drag
        if self.drag != 0:
            self.velocity *= (1.0 - self.drag * delta_time)
        
        # Update position
        self.position += self.velocity * delta_time * 60
        
        # Update size (fade out)
        if self.age / self.lifetime > 0.5:
            self.size *= (1.0 - delta_time * 2)
    
    def is_alive(self) -> bool:
        """Check if particle is alive"""
        return self.age < self.lifetime
    
    def get_alpha(self) -> int:
        """Get alpha based on age"""
        if self.age / self.lifetime > 0.8:
            return int(255 * (1.0 - (self.age / self.lifetime - 0.8) / 0.2))
        return 255


class Effect:
    """Visual and gameplay effect"""
    
    def __init__(self,
                 effect_type: EffectType,
                 position: Vector2,
                 config: EffectConfig = None,
                 target: Optional[Any] = None):
        self.id = id(self)
        self.effect_type = effect_type
        self.config = config or DEFAULT_EFFECT_CONFIGS.get(effect_type, DEFAULT_EFFECT_CONFIGS[EffectType.PARTICLE])
        
        # Position and target
        self.position = position.copy()
        self.target = target
        
        # Timing
        self.duration = self.config.duration
        self.age = 0.0
        self.state = EffectState.ACTIVE
        
        # Particles
        self.particles: List[Particle] = []
        self._create_particles()
        
        # Visual
        self.size = self.config.size
        self.color = self.config.color
        
        # Gameplay
        self.applies_damage = self.config.applies_damage
        self.damage = self.config.damage
        self.applies_healing = self.config.applies_healing
        self.healing = self.config.healing
        self.applies_status = self.config.applies_status
        self.status_duration = self.config.status_duration
        
        # Applied flag (to prevent multiple applications)
        self.applied = False
    
    def _create_particles(self):
        """Create particles for effect"""
        for _ in range(self.config.particle_count):
            # Random direction
            angle = random.uniform(0, 2 * math.pi)
            speed = self.config.particle_speed * random.uniform(0.5, 1.5)
            velocity = Vector2(math.cos(angle) * speed, math.sin(angle) * speed)
            
            # Random size
            size = self.config.particle_size * random.uniform(0.5, 1.5)
            
            # Random lifetime
            lifetime = self.duration * random.uniform(0.5, 1.5)
            
            # Random color variation
            color = (
                max(0, min(255, self.color[0] + random.randint(-30, 30))),
                max(0, min(255, self.color[1] + random.randint(-30, 30))),
                max(0, min(255, self.color[2] + random.randint(-30, 30)))
            )
            
            # Create particle
            particle = Particle(
                position=self.position.copy(),
                velocity=velocity,
                size=size,
                color=color,
                lifetime=lifetime,
                gravity=0.2 if self.effect_type in [EffectType.EXPLOSION, EffectType.SPARKS] else 0.0,
                drag=0.1 if self.effect_type == EffectType.SMOKE else 0.0
            )
            
            self.particles.append(particle)
    
    def update(self, delta_time: float):
        """Update effect"""
        self.age += delta_time
        
        # Update state
        if self.age >= self.duration * 0.8 and self.state == EffectState.ACTIVE:
            self.state = EffectState.FADING
        elif self.age >= self.duration:
            self.state = EffectState.COMPLETE
        
        # Update particles
        for particle in self.particles[:]:
            particle.update(delta_time)
        
        # Remove dead particles
        self.particles = [p for p in self.particles if p.is_alive()]
        
        # Apply effect on first frame (if not already applied)
        if not self.applied and self.age < delta_time:
            self._apply_effect()
            self.applied = True
    
    def _apply_effect(self):
        """Apply gameplay effect"""
        if self.applies_damage and self.target:
            # Apply damage to target
            if hasattr(self.target, 'take_damage'):
                self.target.take_damage(self.damage)
        
        if self.applies_healing and self.target:
            # Apply healing to target
            if hasattr(self.target, 'heal'):
                self.target.heal(self.healing)
        
        if self.applies_status and self.target:
            # Apply status effect to target
            if hasattr(self.target, 'add_effect'):
                self.target.add_effect(self.applies_status, self.status_duration)
    
    def is_alive(self) -> bool:
        """Check if effect is alive"""
        return self.state != EffectState.COMPLETE
    
    def draw(self, surface: pygame.Surface, camera):
        """Draw effect on surface"""
        screen_pos = camera.world_to_screen(self.position)
        
        # Draw particles
        for particle in self.particles:
            screen_particle_pos = camera.world_to_screen(particle.position)
            
            # Calculate screen size
            screen_size = int(particle.size * camera.zoom * 8)
            if screen_size <= 0:
                continue
            
            # Get alpha
            alpha = particle.get_alpha()
            
            # Draw particle
            if alpha > 0:
                if alpha < 255:
                    s = pygame.Surface((screen_size * 2, screen_size * 2), pygame.SRCALPHA)
                    color = (*particle.color, alpha)
                    pygame.draw.circle(s, color, (screen_size, screen_size), screen_size)
                    surface.blit(s, (int(screen_particle_pos.x - screen_size), int(screen_particle_pos.y - screen_size)))
                else:
                    pygame.draw.circle(surface, particle.color,
                                      (int(screen_particle_pos.x), int(screen_particle_pos.y)),
                                      screen_size)
        
        # Draw effect center (for some effect types)
        if self.effect_type in [EffectType.EXPLOSION, EffectType.SHIELD, EffectType.TELEPORT]:
            screen_size = int(self.size * camera.zoom * 4)
            if screen_size > 0:
                # Fade based on state
                if self.state == EffectState.FADING:
                    alpha = int(255 * (1.0 - (self.age - self.duration * 0.8) / (self.duration * 0.2)))
                    s = pygame.Surface((screen_size * 2, screen_size * 2), pygame.SRCALPHA)
                    color = (*self.color, alpha)
                    
                    if self.effect_type == EffectType.EXPLOSION:
                        pygame.draw.circle(s, color, (screen_size, screen_size), screen_size)
                    elif self.effect_type == EffectType.SHIELD:
                        pygame.draw.circle(s, color, (screen_size, screen_size), screen_size, 2)
                    elif self.effect_type == EffectType.TELEPORT:
                        pygame.draw.circle(s, color, (screen_size, screen_size), screen_size // 2)
                    
                    surface.blit(s, (int(screen_pos.x - screen_size), int(screen_pos.y - screen_size)))
                else:
                    if self.effect_type == EffectType.EXPLOSION:
                        pygame.draw.circle(surface, self.color,
                                          (int(screen_pos.x), int(screen_pos.y)), screen_size)
                    elif self.effect_type == EffectType.SHIELD:
                        pygame.draw.circle(surface, self.color,
                                          (int(screen_pos.x), int(screen_pos.y)), screen_size, 2)
                    elif self.effect_type == EffectType.TELEPORT:
                        pygame.draw.circle(surface, self.color,
                                          (int(screen_pos.x), int(screen_pos.y)), screen_size // 2)
    
    def __str__(self) -> str:
        return f"Effect({self.effect_type.name}, pos=({self.position.x:.1f}, {self.position.y:.1f}), age={self.age:.2f}/{self.duration:.2f})"


class EffectManager:
    """Manages all effects in the game"""
    
    def __init__(self):
        self.effects: List[Effect] = []
        self.max_effects = 200
    
    def add_effect(self, effect: Effect):
        """Add an effect"""
        if len(self.effects) >= self.max_effects:
            # Remove oldest effect
            self.effects.pop(0)
        
        self.effects.append(effect)
    
    def create_effect(self,
                     effect_type: EffectType,
                     position: Vector2,
                     target: Optional[Any] = None,
                     config: EffectConfig = None) -> Effect:
        """Create and add a new effect"""
        effect = Effect(
            effect_type=effect_type,
            position=position,
            config=config,
            target=target
        )
        self.add_effect(effect)
        return effect
    
    def update(self, delta_time: float):
        """Update all effects"""
        for effect in self.effects[:]:
            effect.update(delta_time)
        
        # Remove dead effects
        self.effects = [e for e in self.effects if e.is_alive()]
    
    def draw(self, surface: pygame.Surface, camera):
        """Draw all effects"""
        for effect in self.effects:
            effect.draw(surface, camera)
    
    def clear(self):
        """Clear all effects"""
        self.effects.clear()
    
    def get_effect_count(self) -> int:
        """Get number of active effects"""
        return len(self.effects)
    
    def create_explosion(self, position: Vector2, damage: float = 50.0, target: Any = None):
        """Create an explosion effect"""
        config = DEFAULT_EFFECT_CONFIGS[EffectType.EXPLOSION].copy()
        config.damage = damage
        return self.create_effect(EffectType.EXPLOSION, position, target, config)
    
    def create_heal_effect(self, position: Vector2, healing: float = 25.0, target: Any = None):
        """Create a heal effect"""
        config = DEFAULT_EFFECT_CONFIGS[EffectType.HEAL].copy()
        config.healing = healing
        return self.create_effect(EffectType.HEAL, position, target, config)
    
    def create_stun_effect(self, position: Vector2, duration: float = 3.0, target: Any = None):
        """Create a stun effect"""
        config = DEFAULT_EFFECT_CONFIGS[EffectType.STUN].copy()
        config.status_duration = duration
        return self.create_effect(EffectType.STUN, position, target, config)


# Global effect manager
effect_manager = EffectManager()
