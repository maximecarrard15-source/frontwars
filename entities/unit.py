"""
Unit system for Frontwars
"""

import math
import random
from typing import List, Tuple, Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
import pygame

from config import GameSettings, Team, UnitType as ConfigUnitType, Colors
from utils.vector import Vector2
from utils.helpers import distance, lerp, point_in_rect, circles_overlap
from utils.pathfinding import pathfinder
from utils.logger import logger
from game.map import GameMap


class UnitState(Enum):
    IDLE = auto()
    MOVING = auto()
    ATTACKING = auto()
    DEFENDING = auto()
    RETREATING = auto()
    CHASING = auto()
    DEAD = auto()
    BUILDING = auto()
    HARVESTING = auto()
    STUNNED = auto()
    INVISIBLE = auto()


class UnitClass(Enum):
    INFANTRY = "infantry"
    VEHICLE = "vehicle"
    AIRCRAFT = "aircraft"
    NAVAL = "naval"
    BUILDING = "building"


class UnitRole(Enum):
    FIGHTER = "fighter"
    SUPPORT = "support"
    SCOUT = "scout"
    TANK = "tank"
    ARTILLERY = "artillery"
    ENGINEER = "engineer"
    HEALER = "healer"
    TRANSPORT = "transport"


@dataclass
class UnitStats:
    """Combat statistics for a unit"""
    health: float = 100.0
    max_health: float = 100.0
    armor: float = 0.0
    damage: float = 10.0
    attack_range: float = 5.0
    attack_speed: float = 1.0  # Attacks per second
    move_speed: float = 2.0
    
    # Accuracy
    accuracy: float = 0.8
    evasion: float = 0.0
    
    # Critical hits
    crit_chance: float = 0.05
    crit_multiplier: float = 2.0
    
    # Special abilities
    can_heal: bool = False
    heal_amount: float = 0.0
    can_build: bool = False
    can_harvest: bool = False
    harvest_speed: float = 1.0
    
    # Detection
    sight_range: float = 10.0
    detection_range: float = 5.0  # For detecting stealthed units
    
    def get_health_percentage(self) -> float:
        """Get health as percentage"""
        return self.health / self.max_health if self.max_health > 0 else 0.0
    
    def is_alive(self) -> bool:
        """Check if unit is alive"""
        return self.health > 0


@dataclass
class UnitConfig:
    """Configuration for unit types"""
    unit_type: ConfigUnitType
    name: str = ""
    description: str = ""
    unit_class: UnitClass = UnitClass.INFANTRY
    role: UnitRole = UnitRole.FIGHTER
    
    # Base stats
    base_health: float = 100.0
    base_armor: float = 0.0
    base_damage: float = 10.0
    base_attack_range: float = 5.0
    base_attack_speed: float = 1.0
    base_move_speed: float = 2.0
    
    # Cost and production
    cost: int = 100
    production_time: float = 5.0  # seconds
    upkeep: float = 1.0  # gold per second
    
    # Size and collision
    size: float = 1.0
    collision_radius: float = 0.5
    
    # Appearance
    color: Tuple[int, int, int] = Colors.WHITE
    sprite: str = ""
    scale: float = 1.0
    
    # Abilities
    abilities: List[str] = field(default_factory=list)
    
    # Upgrades
    max_level: int = 5
    
    def create_stats(self, level: int = 1) -> UnitStats:
        """Create stats for this unit at given level"""
        stats = UnitStats(
            health=self.base_health * (1 + 0.2 * (level - 1)),
            max_health=self.base_health * (1 + 0.2 * (level - 1)),
            armor=self.base_armor,
            damage=self.base_damage * (1 + 0.1 * (level - 1)),
            attack_range=self.base_attack_range,
            attack_speed=self.base_attack_speed,
            move_speed=self.base_move_speed
        )
        return stats


# Default unit configurations
DEFAULT_UNIT_CONFIGS = {
    ConfigUnitType.SOLDIER: UnitConfig(
        unit_type=ConfigUnitType.SOLDIER,
        name="Soldier",
        description="Basic infantry unit",
        unit_class=UnitClass.INFANTRY,
        role=UnitRole.FIGHTER,
        base_health=100,
        base_armor=0,
        base_damage=15,
        base_attack_range=4,
        base_attack_speed=1.5,
        base_move_speed=2.5,
        cost=100,
        production_time=3,
        upkeep=1,
        size=1.0,
        collision_radius=0.4,
        color=Colors.WHITE,
        abilities=["none"]
    ),
    ConfigUnitType.TANK: UnitConfig(
        unit_type=ConfigUnitType.TANK,
        name="Tank",
        description="Heavy armored vehicle",
        unit_class=UnitClass.VEHICLE,
        role=UnitRole.TANK,
        base_health=400,
        base_armor=3,
        base_damage=40,
        base_attack_range=6,
        base_attack_speed=0.8,
        base_move_speed=1.8,
        cost=500,
        production_time=10,
        upkeep=5,
        size=1.5,
        collision_radius=0.8,
        color=(100, 100, 100),
        abilities=["none"]
    ),
    ConfigUnitType.SCOUT: UnitConfig(
        unit_type=ConfigUnitType.SCOUT,
        name="Scout",
        description="Fast reconnaissance unit",
        unit_class=UnitClass.VEHICLE,
        role=UnitRole.SCOUT,
        base_health=80,
        base_armor=0,
        base_damage=5,
        base_attack_range=3,
        base_attack_speed=2.0,
        base_move_speed=4.0,
        cost=150,
        production_time=5,
        upkeep=2,
        size=0.8,
        collision_radius=0.3,
        color=(200, 200, 100),
        abilities=["stealth"]
    ),
    ConfigUnitType.ARTILLERY: UnitConfig(
        unit_type=ConfigUnitType.ARTILLERY,
        name="Artillery",
        description="Long-range siege unit",
        unit_class=UnitClass.VEHICLE,
        role=UnitRole.ARTILLERY,
        base_health=150,
        base_armor=1,
        base_damage=80,
        base_attack_range=15,
        base_attack_speed=0.5,
        base_move_speed=1.2,
        cost=600,
        production_time=15,
        upkeep=8,
        size=1.2,
        collision_radius=0.6,
        color=(50, 100, 50),
        abilities=["splash"]
    ),
    ConfigUnitType.ENGINEER: UnitConfig(
        unit_type=ConfigUnitType.ENGINEER,
        name="Engineer",
        description="Construction and repair unit",
        unit_class=UnitClass.INFANTRY,
        role=UnitRole.ENGINEER,
        base_health=60,
        base_armor=0,
        base_damage=2,
        base_attack_range=2,
        base_attack_speed=1.0,
        base_move_speed=2.0,
        cost=200,
        production_time=8,
        upkeep=3,
        size=1.0,
        collision_radius=0.4,
        color=(0, 200, 200),
        abilities=["build", "repair"]
    ),
    ConfigUnitType.AIRCRAFT: UnitConfig(
        unit_type=ConfigUnitType.AIRCRAFT,
        name="Fighter",
        description="Aerial combat unit",
        unit_class=UnitClass.AIRCRAFT,
        role=UnitRole.FIGHTER,
        base_health=200,
        base_armor=0,
        base_damage=30,
        base_attack_range=8,
        base_attack_speed=2.0,
        base_move_speed=5.0,
        cost=700,
        production_time=12,
        upkeep=6,
        size=1.0,
        collision_radius=0.5,
        color=(150, 150, 255),
        abilities=["fly"]
    ),
    ConfigUnitType.HELICOPTER: UnitConfig(
        unit_type=ConfigUnitType.HELICOPTER,
        name="Helicopter",
        description="Versatile aerial unit",
        unit_class=UnitClass.AIRCRAFT,
        role=UnitRole.TRANSPORT,
        base_health=250,
        base_armor=1,
        base_damage=20,
        base_attack_range=6,
        base_attack_speed=1.5,
        base_move_speed=3.5,
        cost=800,
        production_time=15,
        upkeep=7,
        size=1.2,
        collision_radius=0.6,
        color=(200, 100, 200),
        abilities=["fly", "transport"]
    )
}


class Unit:
    """Base unit class for all game units"""
    
    def __init__(self, 
                 unit_type: ConfigUnitType,
                 team: Team,
                 position: Vector2,
                 game_map: GameMap = None,
                 level: int = 1,
                 unit_id: int = None):
        # Unique identifier
        self.id = unit_id or random.randint(1, 2**32)
        self.unit_type = unit_type
        self.config = DEFAULT_UNIT_CONFIGS.get(unit_type, DEFAULT_UNIT_CONFIGS[ConfigUnitType.SOLDIER])
        self.team = team
        
        # Position and movement
        self.position = position.copy()
        self.target_position: Optional[Vector2] = None
        self.path: List[Vector2] = []
        self.path_index = 0
        self.velocity = Vector2(0, 0)
        self.speed = self.config.base_move_speed
        self.facing = 0.0  # In radians
        
        # State
        self.state = UnitState.IDLE
        self.prev_state = UnitState.IDLE
        
        # Combat
        self.stats = self.config.create_stats(level)
        self.level = level
        self.experience = 0.0
        self.experience_to_level = 100.0 * level
        
        # Targeting
        self.target: Optional['Unit'] = None
        self.attack_cooldown = 0.0
        self.attack_range_sq = self.stats.attack_range ** 2
        
        # Game references
        self.game_map = game_map
        
        # Visual
        self.color = team.color if team else self.config.color
        self.size = self.config.size
        self.collision_radius = self.config.collision_radius
        
        # Status effects
        self.effects: Dict[str, float] = {}  # effect_name: duration
        
        # Combat statistics
        self.kills = 0
        self.deaths = 0
        self.damage_dealt = 0.0
        self.damage_received = 0.0
        
        # Time tracking
        self.spawn_time = 0.0
        self.last_attack_time = 0.0
        self.last_move_time = 0.0
        
        # Initialize
        self._initialize()
        
        logger.debug(f"Created unit {self.config.name} (ID: {self.id}) for team {team.name if team else 'Neutral'}", "units")
    
    def _initialize(self):
        """Initialize unit"""
        self.spawn_time = pygame.time.get_ticks() / 1000.0
        self.last_attack_time = self.spawn_time
        self.last_move_time = self.spawn_time
        
        # Set initial facing
        self.facing = random.uniform(0, 2 * math.pi)
    
    @property
    def combat_strength(self) -> float:
        """Calculate overall combat strength"""
        return self.stats.health + self.stats.damage * 10 + self.stats.armor * 5
    
    @property
    def is_alive(self) -> bool:
        """Check if unit is alive"""
        return self.stats.is_alive() and self.state != UnitState.DEAD
    
    @property
    def is_moving(self) -> bool:
        """Check if unit is moving"""
        return self.state == UnitState.MOVING
    
    @property
    def is_attacking(self) -> bool:
        """Check if unit is attacking"""
        return self.state == UnitState.ATTACKING
    
    @property
    def can_attack(self) -> bool:
        """Check if unit can attack"""
        return self.attack_cooldown <= 0 and self.stats.attack_speed > 0
    
    @property
    def cost(self) -> int:
        """Get unit cost"""
        return self.config.cost
    
    @property
    def upkeep(self) -> float:
        """Get unit upkeep cost"""
        return self.config.upkeep
    
    @property
    def sight_range(self) -> float:
        """Get sight range"""
        return self.stats.sight_range
    
    def get_name(self) -> str:
        """Get unit name"""
        return self.config.name
    
    def get_display_name(self) -> str:
        """Get display name with level"""
        if self.level > 1:
            return f"{self.config.name} (Lv. {self.level})"
        return self.config.name
    
    def get_bounding_box(self) -> Tuple[float, float, float, float]:
        """Get bounding box"""
        half_size = self.size / 2
        return (
            self.position.x - half_size,
            self.position.y - half_size,
            self.size,
            self.size
        )
    
    def update(self, delta_time: float):
        """Update unit state"""
        if not self.is_alive:
            return
        
        # Update cooldowns
        self._update_cooldowns(delta_time)
        
        # Update status effects
        self._update_effects(delta_time)
        
        # Update state machine
        self._update_state(delta_time)
        
        # Update position
        self._update_position(delta_time)
        
        # Update targeting
        self._update_targeting(delta_time)
        
        # Reveal area around unit
        if self.game_map and self.team:
            self.game_map.reveal_area(self.position, self.sight_range, self.team.id)
    
    def _update_cooldowns(self, delta_time: float):
        """Update attack cooldown"""
        if self.attack_cooldown > 0:
            self.attack_cooldown -= delta_time * self.stats.attack_speed
            if self.attack_cooldown < 0:
                self.attack_cooldown = 0
    
    def _update_effects(self, delta_time: float):
        """Update status effects"""
        effects_to_remove = []
        
        for effect, duration in self.effects.items():
            duration -= delta_time
            if duration <= 0:
                effects_to_remove.append(effect)
            else:
                self.effects[effect] = duration
        
        for effect in effects_to_remove:
            del self.effects[effect]
            self._on_effect_end(effect)
    
    def _on_effect_end(self, effect: str):
        """Called when an effect ends"""
        if effect == "stun":
            if self.state == UnitState.STUNNED:
                self.state = UnitState.IDLE
    
    def _update_state(self, delta_time: float):
        """Update unit state"""
        self.prev_state = self.state
        
        # Check for death
        if not self.stats.is_alive():
            self.die()
            return
        
        # Handle stunned state
        if "stun" in self.effects:
            self.state = UnitState.STUNNED
            self.velocity = Vector2(0, 0)
            return
        
        # State transitions
        if self.state == UnitState.ATTACKING:
            if self.target and self._can_attack_target():
                self.attack(self.target)
            else:
                # Target out of range or dead
                self.target = None
                self.state = UnitState.IDLE
        
        elif self.state == UnitState.MOVING:
            if not self.path:
                self.state = UnitState.IDLE
            else:
                # Check if we should attack instead
                if self.target and self._can_attack_target():
                    self.state = UnitState.ATTACKING
        
        elif self.state == UnitState.IDLE:
            # Check for nearby enemies
            if self._find_enemy_target():
                self.state = UnitState.ATTACKING
            elif self.path:
                self.state = UnitState.MOVING
    
    def _update_position(self, delta_time: float):
        """Update unit position"""
        if self.state == UnitState.STUNNED or not self.is_alive:
            self.velocity = Vector2(0, 0)
            return
        
        # Calculate desired velocity
        if self.path and self.state == UnitState.MOVING:
            self._move_along_path(delta_time)
        else:
            self.velocity = Vector2(0, 0)
        
        # Apply velocity with collision avoidance
        new_position = self.position + self.velocity * delta_time * 60
        
        # Check for collisions
        if self.game_map:
            new_position = self._avoid_collisions(new_position, delta_time)
        
        # Update position
        self.position = new_position
        
        # Update facing direction
        if self.velocity.length() > 0.1:
            self.facing = self.velocity.angle()
        
        # Check if reached target
        if self.target_position:
            dist = self.position.distance_to(self.target_position)
            if dist < 0.5:  # Close enough
                self.position = self.target_position.copy()
                self.path = []
                self.target_position = None
    
    def _move_along_path(self, delta_time: float):
        """Move along current path"""
        if not self.path:
            self.velocity = Vector2(0, 0)
            return
        
        # Get current target from path
        current_target = self.path[self.path_index]
        
        # Calculate direction to target
        direction = (current_target - self.position).normalize()
        
        # Set velocity
        self.velocity = direction * self.speed
        
        # Check if reached current path point
        dist_to_target = self.position.distance_to(current_target)
        if dist_to_target < 0.5:  # Close enough to path point
            self.path_index += 1
            if self.path_index >= len(self.path):
                self.path = []
                self.path_index = 0
                self.velocity = Vector2(0, 0)
    
    def _avoid_collisions(self, new_position: Vector2, delta_time: float) -> Vector2:
        """Avoid collisions with other units and terrain"""
        # Check for terrain collisions
        if self.game_map:
            cell = self.game_map.get_cell_at_position(new_position)
            if cell and not cell.is_walkable():
                # Try to find a nearby walkable position
                for angle in range(0, 360, 45):
                    rad = math.radians(angle)
                    test_pos = new_position + Vector2(math.cos(rad), math.sin(rad)) * 0.5
                    test_cell = self.game_map.get_cell_at_position(test_pos)
                    if test_cell and test_cell.is_walkable():
                        return test_pos
                return self.position
        
        return new_position
    
    def _update_targeting(self, delta_time: float):
        """Update targeting logic"""
        # Check if current target is still valid
        if self.target:
            if not self.target.is_alive:
                self.target = None
            elif self.target.position.distance_to(self.position) > self.stats.attack_range * 1.5:
                # Target moved out of range, try to follow
                if self.state != UnitState.MOVING:
                    self.move_to(self.target.position)
    
    def _can_attack_target(self) -> bool:
        """Check if can attack current target"""
        if not self.target or not self.target.is_alive:
            return False
        
        dist_sq = self.position.distance_squared_to(self.target.position)
        return dist_sq <= self.attack_range_sq and self.can_attack
    
    def _find_enemy_target(self) -> Optional['Unit']:
        """Find a nearby enemy target"""
        if not self.game_map or not self.team:
            return None
        
        # Get all enemy units in sight range
        enemies = []
        for team in self.game_map.teams.values():
            if team != self.team and self.team.is_enemy(team):
                for unit in team.units:
                    dist = self.position.distance_to(unit.position)
                    if dist <= self.sight_range:
                        enemies.append(unit)
        
        if not enemies:
            return None
        
        # Find closest enemy
        closest = min(enemies, key=lambda u: self.position.distance_to(u.position))
        return closest
    
    def move_to(self, target: Vector2):
        """Move unit to target position"""
        if not self.is_alive:
            return
        
        self.target_position = target.copy()
        
        # Find path
        if self.game_map:
            self.path = self.game_map.find_path_continuous(self.position, target)
            self.path_index = 0
        else:
            self.path = [self.position, target]
            self.path_index = 0
        
        self.state = UnitState.MOVING
        self.target = None  # Clear attack target when moving
        
        logger.debug(f"Unit {self.id} moving to ({target.x:.1f}, {target.y:.1f})", "units")
    
    def attack_move(self, target: Vector2):
        """Move to position and attack any enemies encountered"""
        self.move_to(target)
        # In attack-move, units will attack enemies they encounter
    
    def attack(self, target: 'Unit'):
        """Attack a target unit"""
        if not self.is_alive or not target.is_alive:
            return
        
        if not self.can_attack:
            return
        
        # Check range
        dist_sq = self.position.distance_squared_to(target.position)
        if dist_sq > self.attack_range_sq:
            return
        
        # Calculate damage
        damage = self._calculate_damage(target)
        
        # Apply damage
        target.take_damage(damage, self)
        
        # Record statistics
        self.damage_dealt += damage
        target.damage_received += damage
        
        # Reset attack cooldown
        self.attack_cooldown = 1.0 / self.stats.attack_speed
        self.last_attack_time = pygame.time.get_ticks() / 1000.0
        
        # Gain experience
        self.gain_experience(damage * 0.1)
        
        logger.debug(f"Unit {self.id} ({self.config.name}) attacked {target.id} ({target.config.name}) for {damage:.1f} damage", "combat")
    
    def _calculate_damage(self, target: 'Unit') -> float:
        """Calculate damage to target"""
        base_damage = self.stats.damage
        
        # Apply critical hit
        if random.random() < self.stats.crit_chance:
            base_damage *= self.stats.crit_multiplier
        
        # Apply accuracy
        if random.random() > self.stats.accuracy:
            return 0.0  # Miss
        
        # Apply target evasion
        if random.random() < target.stats.evasion:
            return 0.0  # Target evaded
        
        # Apply armor reduction
        armor_reduction = target.stats.armor * GameSettings.COMBAT_ARMOR_REDUCTION
        damage = base_damage * (1.0 - armor_reduction)
        
        # Minimum damage
        return max(1.0, damage)
    
    def take_damage(self, amount: float, attacker: 'Unit' = None):
        """Take damage from attack"""
        if not self.is_alive:
            return
        
        # Apply damage
        self.stats.health -= amount
        
        # Check for death
        if self.stats.health <= 0:
            self.die()
            if attacker:
                attacker.kills += 1
                self._grant_experience_to_attacker(attacker)
    
    def _grant_experience_to_attacker(self, attacker: 'Unit'):
        """Grant experience to attacker for killing this unit"""
        experience = self.config.cost * 0.5  # Base experience
        if self.unit_type == ConfigUnitType.TANK:
            experience *= 2
        elif self.unit_type == ConfigUnitType.ARTILLERY:
            experience *= 1.5
        
        attacker.gain_experience(experience)
    
    def gain_experience(self, amount: float):
        """Gain experience"""
        self.experience += amount
        
        # Check for level up
        if self.experience >= self.experience_to_level:
            self.level_up()
    
    def level_up(self):
        """Level up the unit"""
        self.level += 1
        self.experience -= self.experience_to_level
        self.experience_to_level *= 1.5
        
        # Increase stats
        self.stats = self.config.create_stats(self.level)
        self.stats.health = self.stats.max_health  # Heal on level up
        
        logger.info(f"Unit {self.id} ({self.config.name}) leveled up to level {self.level}", "units")
    
    def heal(self, amount: float):
        """Heal the unit"""
        if not self.is_alive:
            return
        
        self.stats.health = min(self.stats.max_health, self.stats.health + amount)
    
    def die(self):
        """Unit dies"""
        self.state = UnitState.DEAD
        self.stats.health = 0
        self.deaths += 1
        
        # Remove from team
        if self.team:
            self.team.remove_unit(self)
        
        logger.info(f"Unit {self.id} ({self.config.name}) died", "units")
    
    def hold_position(self):
        """Hold current position"""
        self.path = []
        self.target_position = None
        self.state = UnitState.DEFENDING
    
    def stop(self):
        """Stop current action"""
        self.path = []
        self.target_position = None
        self.target = None
        self.state = UnitState.IDLE
    
    def retreat(self, target: Vector2):
        """Retreat to position"""
        self.move_to(target)
        self.state = UnitState.RETREATING
    
    def set_target(self, target: 'Unit'):
        """Set attack target"""
        self.target = target
        
        # Check if in range
        if self._can_attack_target():
            self.state = UnitState.ATTACKING
        else:
            # Move towards target
            self.move_to(target.position)
    
    def clear_target(self):
        """Clear attack target"""
        self.target = None
    
    def add_effect(self, effect: str, duration: float):
        """Add status effect"""
        self.effects[effect] = duration
        self._on_effect_start(effect)
    
    def _on_effect_start(self, effect: str):
        """Called when an effect starts"""
        if effect == "stun":
            self.state = UnitState.STUNNED
            self.velocity = Vector2(0, 0)
    
    def has_effect(self, effect: str) -> bool:
        """Check if has effect"""
        return effect in self.effects
    
    def get_effect_remaining(self, effect: str) -> float:
        """Get remaining duration of effect"""
        return self.effects.get(effect, 0.0)
    
    def get_health_percentage(self) -> float:
        """Get health as percentage"""
        return self.stats.get_health_percentage()
    
    def get_unit_info(self) -> Dict[str, Any]:
        """Get unit information for UI"""
        return {
            'id': self.id,
            'name': self.get_display_name(),
            'type': self.unit_type.value,
            'team': self.team.name if self.team else None,
            'team_color': self.team.color if self.team else Colors.WHITE,
            'health': self.stats.health,
            'max_health': self.stats.max_health,
            'health_percent': self.get_health_percentage(),
            'level': self.level,
            'damage': self.stats.damage,
            'armor': self.stats.armor,
            'range': self.stats.attack_range,
            'speed': self.stats.move_speed,
            'state': self.state.name,
            'kills': self.kills,
            'position': (self.position.x, self.position.y),
            'facing': self.facing,
            'size': self.size,
            'cost': self.cost
        }
    
    def draw(self, surface: pygame.Surface, camera):
        """Draw unit on surface"""
        # Convert position to screen coordinates
        screen_pos = camera.world_to_screen(self.position)
        
        # Draw unit circle
        radius = int(self.size * camera.zoom * 4)
        
        # Draw health bar
        if self.stats.max_health > 0:
            health_percent = self.get_health_percentage()
            bar_width = radius * 2
            bar_height = 4
            bar_x = screen_pos.x - radius
            bar_y = screen_pos.y - radius - bar_height - 2
            
            # Background
            pygame.draw.rect(surface, Colors.BLACK, 
                           (bar_x, bar_y, bar_width, bar_height))
            
            # Health bar
            health_width = int(bar_width * health_percent)
            if health_percent > 0.6:
                color = Colors.GREEN
            elif health_percent > 0.3:
                color = Colors.YELLOW
            else:
                color = Colors.RED
            
            pygame.draw.rect(surface, color,
                           (bar_x, bar_y, health_width, bar_height))
        
        # Draw unit body
        pygame.draw.circle(surface, self.color, 
                          (int(screen_pos.x), int(screen_pos.y)), radius)
        
        # Draw unit type indicator
        if camera.zoom > 0.5:
            # Draw facing direction
            indicator_length = radius
            end_x = screen_pos.x + math.cos(self.facing) * indicator_length
            end_y = screen_pos.y + math.sin(self.facing) * indicator_length
            pygame.draw.line(surface, Colors.WHITE,
                           (screen_pos.x, screen_pos.y),
                           (end_x, end_y), 2)
        
        # Draw selection indicator
        if self.is_selected:
            pygame.draw.circle(surface, Colors.YELLOW,
                              (int(screen_pos.x), int(screen_pos.y)),
                              radius + 3, 2)
        
        # Draw state indicator
        state_color = {
            UnitState.ATTACKING: Colors.RED,
            UnitState.MOVING: Colors.BLUE,
            UnitState.DEFENDING: Colors.GREEN,
            UnitState.RETREATING: Colors.ORANGE
        }.get(self.state, Colors.WHITE)
        
        if camera.zoom > 0.5:
            pygame.draw.circle(surface, state_color,
                              (int(screen_pos.x), int(screen_pos.y - radius - 8)),
                              4)
    
    def __str__(self) -> str:
        return f"Unit({self.id}, {self.config.name}, {self.team.name if self.team else 'Neutral'}, " \
               f"HP: {self.stats.health:.0f}/{self.stats.max_health:.0f})"
    
    def __repr__(self) -> str:
        return f"Unit({self.id}, {self.config.name}, {self.unit_type.value})"


# Unit factory
class UnitFactory:
    """Factory for creating units"""
    
    unit_id_counter = 1
    
    @classmethod
    def create_unit(cls, unit_type: ConfigUnitType, team: Team, 
                   position: Vector2, game_map: GameMap = None, 
                   level: int = 1) -> Unit:
        """Create a new unit"""
        unit = Unit(unit_type, team, position, game_map, level, cls.unit_id_counter)
        cls.unit_id_counter += 1
        
        # Add to team
        if team:
            team.add_unit(unit)
        
        return unit
    
    @classmethod
    def reset_counter(cls):
        """Reset unit ID counter"""
        cls.unit_id_counter = 1
