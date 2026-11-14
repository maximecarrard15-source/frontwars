"""
Team management system for Frontwars
"""

from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import random

from config import Team as TeamEnum, Colors, DEFAULT_TEAMS, TeamConfig, GameSettings
from utils.vector import Vector2
from utils.logger import logger


class TeamRelation(Enum):
    ALLY = "ally"
    ENEMY = "enemy"
    NEUTRAL = "neutral"


@dataclass
class TeamStats:
    """Statistics for a team"""
    units_killed: int = 0
    units_lost: int = 0
    buildings_destroyed: int = 0
    buildings_lost: int = 0
    resources_collected: float = 0.0
    territories_captured: int = 0
    territories_lost: int = 0
    
    def get_kill_death_ratio(self) -> float:
        """Get kill/death ratio"""
        if self.units_lost == 0:
            return float('inf') if self.units_killed > 0 else 0.0
        return self.units_killed / self.units_lost


class Team:
    """Represents a team in the game"""
    
    def __init__(self, team_id: TeamEnum, config: TeamConfig = None):
        self.id = team_id
        self.config = config or DEFAULT_TEAMS.get(team_id, TeamConfig(
            name=f"Team {team_id.name}",
            color=Colors.WHITE,
            ai_controlled=True
        ))
        self.stats = TeamStats()
        self.gold = self.config.gold
        self.gold_income_rate = GameSettings.GOLD_INCOME_RATE
        self.last_gold_income = 0.0
        
        # Units and buildings
        self.units: List = []
        self.buildings: List = []
        self.owned_territories: Set[Tuple[int, int]] = set()
        
        # Diplomacy
        self.relations: Dict[TeamEnum, TeamRelation] = {}
        
        # AI settings
        self.ai_difficulty = GameSettings.AI_DIFFICULTY
        self.ai_personality = "balanced"
    
    @property
    def name(self) -> str:
        return self.config.name
    
    @property
    def color(self) -> Tuple[int, int, int]:
        return self.config.color
    
    @property
    def is_ai(self) -> bool:
        return self.config.ai_controlled
    
    @property
    def is_human(self) -> bool:
        return not self.config.ai_controlled
    
    def set_ai_controlled(self, ai_controlled: bool):
        """Set whether team is AI controlled"""
        self.config.ai_controlled = ai_controlled
    
    def add_gold(self, amount: float):
        """Add gold to team"""
        self.gold += amount
        logger.debug(f"Team {self.name} gained {amount} gold (total: {self.gold})", "economy")
    
    def spend_gold(self, amount: float) -> bool:
        """Spend gold, returns True if successful"""
        if self.gold >= amount:
            self.gold -= amount
            logger.debug(f"Team {self.name} spent {amount} gold (remaining: {self.gold})", "economy")
            return True
        return False
    
    def can_afford(self, amount: float) -> bool:
        """Check if team can afford amount"""
        return self.gold >= amount
    
    def update_gold_income(self, delta_time: float):
        """Update gold income based on time"""
        income = self.gold_income_rate * delta_time / 1000.0  # Convert ms to seconds
        self.add_gold(income)
    
    def add_unit(self, unit):
        """Add unit to team"""
        self.units.append(unit)
        logger.debug(f"Team {self.name} added unit {unit.unit_type}", "units")
    
    def remove_unit(self, unit):
        """Remove unit from team"""
        if unit in self.units:
            self.units.remove(unit)
            self.stats.units_lost += 1
            logger.debug(f"Team {self.name} lost unit {unit.unit_type}", "units")
    
    def add_building(self, building):
        """Add building to team"""
        self.buildings.append(building)
    
    def remove_building(self, building):
        """Remove building from team"""
        if building in self.buildings:
            self.buildings.remove(building)
            self.stats.buildings_lost += 1
    
    def capture_territory(self, x: int, y: int):
        """Capture territory at position"""
        self.owned_territories.add((x, y))
        self.stats.territories_captured += 1
    
    def lose_territory(self, x: int, y: int):
        """Lose territory at position"""
        if (x, y) in self.owned_territories:
            self.owned_territories.remove((x, y))
            self.stats.territories_lost += 1
    
    def owns_territory(self, x: int, y: int) -> bool:
        """Check if team owns territory"""
        return (x, y) in self.owned_territories
    
    def get_relation(self, other_team: 'Team') -> TeamRelation:
        """Get relation to other team"""
        return self.relations.get(other_team.id, TeamRelation.NEUTRAL)
    
    def set_relation(self, other_team: TeamEnum, relation: TeamRelation):
        """Set relation to other team"""
        self.relations[other_team] = relation
    
    def is_allied(self, other_team: 'Team') -> bool:
        """Check if allied with other team"""
        return self.get_relation(other_team) == TeamRelation.ALLY
    
    def is_enemy(self, other_team: 'Team') -> bool:
        """Check if enemy with other team"""
        relation = self.get_relation(other_team)
        return relation == TeamRelation.ENEMY
    
    def is_neutral(self, other_team: 'Team') -> bool:
        """Check if neutral with other team"""
        return self.get_relation(other_team) == TeamRelation.NEUTRAL
    
    def get_units(self) -> List:
        """Get all units"""
        return self.units.copy()
    
    def get_buildings(self) -> List:
        """Get all buildings"""
        return self.buildings.copy()
    
    def get_unit_count(self) -> int:
        """Get number of units"""
        return len(self.units)
    
    def get_building_count(self) -> int:
        """Get number of buildings"""
        return len(self.buildings)
    
    def get_total_value(self) -> float:
        """Get total value of units and buildings"""
        value = 0.0
        for unit in self.units:
            value += unit.cost
        for building in self.buildings:
            value += building.cost
        return value
    
    def get_strongest_unit(self):
        """Get strongest unit"""
        if not self.units:
            return None
        return max(self.units, key=lambda u: u.combat_strength)
    
    def get_weakest_unit(self):
        """Get weakest unit"""
        if not self.units:
            return None
        return min(self.units, key=lambda u: u.health)
    
    def get_closest_unit(self, position: Vector2, max_distance: float = float('inf')) -> Optional['Unit']:
        """Get closest unit to position"""
        closest = None
        closest_dist = float('inf')
        
        for unit in self.units:
            dist = unit.position.distance_to(position)
            if dist < closest_dist and dist <= max_distance:
                closest = unit
                closest_dist = dist
        
        return closest
    
    def get_units_in_radius(self, center: Vector2, radius: float) -> List:
        """Get all units within radius of center"""
        return [u for u in self.units if u.position.distance_to(center) <= radius]
    
    def has_units(self) -> bool:
        """Check if team has any units"""
        return len(self.units) > 0
    
    def has_buildings(self) -> bool:
        """Check if team has any buildings"""
        return len(self.buildings) > 0
    
    def is_defeated(self) -> bool:
        """Check if team is defeated (no units and no buildings)"""
        return not self.has_units() and not self.has_buildings()
    
    def surrender(self):
        """Surrender (remove all units and buildings)"""
        self.units.clear()
        self.buildings.clear()
        self.owned_territories.clear()
        logger.info(f"Team {self.name} has surrendered", "game")
    
    def get_stats(self) -> Dict:
        """Get team statistics"""
        return {
            'name': self.name,
            'gold': self.gold,
            'units': self.get_unit_count(),
            'buildings': self.get_building_count(),
            'territories': len(self.owned_territories),
            'units_killed': self.stats.units_killed,
            'units_lost': self.stats.units_lost,
            'buildings_destroyed': self.stats.buildings_destroyed,
            'buildings_lost': self.stats.buildings_lost,
            'resources_collected': self.stats.resources_collected,
            'kill_death_ratio': self.stats.get_kill_death_ratio()
        }
    
    def __str__(self) -> str:
        return f"Team({self.name}, {self.id.name}, gold={self.gold}, units={len(self.units)})"


class TeamManager:
    """Manages all teams in the game"""
    
    def __init__(self):
        self.teams: Dict[TeamEnum, Team] = {}
        self.active_teams: Set[TeamEnum] = set()
        self.winning_team: Optional[Team] = None
        self.game_over = False
    
    def add_team(self, team_id: TeamEnum, config: TeamConfig = None) -> Team:
        """Add a team"""
        team = Team(team_id, config)
        self.teams[team_id] = team
        self.active_teams.add(team_id)
        logger.info(f"Added team: {team.name} ({team_id.name})", "game")
        return team
    
    def remove_team(self, team_id: TeamEnum):
        """Remove a team"""
        if team_id in self.teams:
            del self.teams[team_id]
            self.active_teams.discard(team_id)
            logger.info(f"Removed team: {team_id.name}", "game")
    
    def get_team(self, team_id: TeamEnum) -> Optional[Team]:
        """Get team by ID"""
        return self.teams.get(team_id)
    
    def get_all_teams(self) -> List[Team]:
        """Get all teams"""
        return list(self.teams.values())
    
    def get_active_teams(self) -> List[Team]:
        """Get all active teams"""
        return [self.teams[t] for t in self.active_teams if t in self.teams]
    
    def get_human_teams(self) -> List[Team]:
        """Get all human-controlled teams"""
        return [t for t in self.teams.values() if t.is_human]
    
    def get_ai_teams(self) -> List[Team]:
        """Get all AI-controlled teams"""
        return [t for t in self.teams.values() if t.is_ai]
    
    def get_enemies(self, team: Team) -> List[Team]:
        """Get all enemies of team"""
        return [t for t in self.teams.values() if t.is_enemy(team)]
    
    def get_allies(self, team: Team) -> List[Team]:
        """Get all allies of team"""
        return [t for t in self.teams.values() if t.is_allied(team)]
    
    def get_winning_team(self) -> Optional[Team]:
        """Get winning team (if game is over)"""
        return self.winning_team
    
    def check_game_over(self) -> bool:
        """Check if game is over (only one team remaining)"""
        active = self.get_active_teams()
        
        if len(active) <= 1:
            if active:
                self.winning_team = active[0]
            self.game_over = True
            return True
        
        # Check if all but one team are defeated
        defeated_count = sum(1 for t in active if t.is_defeated())
        if defeated_count >= len(active) - 1:
            for team in active:
                if not team.is_defeated():
                    self.winning_team = team
                    break
            self.game_over = True
            return True
        
        return False
    
    def update(self, delta_time: float):
        """Update all teams"""
        for team in self.teams.values():
            team.update_gold_income(delta_time)
    
    def get_team_by_index(self, index: int) -> Optional[Team]:
        """Get team by index (for player selection)"""
        teams = self.get_all_teams()
        if 0 <= index < len(teams):
            return teams[index]
        return None
    
    def get_team_count(self) -> int:
        """Get number of teams"""
        return len(self.teams)
    
    def clear(self):
        """Clear all teams"""
        self.teams.clear()
        self.active_teams.clear()
        self.winning_team = None
        self.game_over = False
    
    def initialize_default_teams(self, num_teams: int = 2):
        """Initialize default teams"""
        self.clear()
        
        team_ids = [TeamEnum.RED, TeamEnum.BLUE, TeamEnum.GREEN, TeamEnum.YELLOW]
        
        for i in range(min(num_teams, len(team_ids))):
            team_id = team_ids[i]
            config = DEFAULT_TEAMS[team_id].copy()
            
            # First team is human, others are AI
            if i == 0:
                config.ai_controlled = False
            else:
                config.ai_controlled = True
            
            self.add_team(team_id, config)
        
        # Set up relations (everyone is enemies by default)
        for team in self.teams.values():
            for other_team in self.teams.values():
                if team.id != other_team.id:
                    team.set_relation(other_team.id, TeamRelation.ENEMY)
        
        logger.info(f"Initialized {num_teams} default teams", "game")


# Global team manager instance
team_manager = TeamManager()
