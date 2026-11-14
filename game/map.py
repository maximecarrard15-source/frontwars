"""
Map system for Frontwars
"""

import random
import math
import noise
from typing import List, Tuple, Dict, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import numpy as np

from config import GameSettings, TerrainType, Team, Colors
from utils.vector import Vector2
from utils.pathfinding import Pathfinder, pathfinder
from utils.helpers import clamp, lerp, distance
from utils.logger import logger


@dataclass
class MapCell:
    """Single cell in the game map"""
    x: int
    y: int
    terrain: TerrainType = TerrainType.GRASS
    elevation: float = 0.0
    owner: Optional[Team] = None
    resource: Optional[str] = None
    resource_amount: float = 0.0
    building: Optional[str] = None
    fog_of_war: bool = True  # Hidden by fog of war
    explored: bool = False   # Has been explored by player
    
    def is_walkable(self) -> bool:
        """Check if cell is walkable"""
        return self.terrain not in [TerrainType.WATER, TerrainType.MOUNTAIN]
    
    def get_movement_cost(self) -> float:
        """Get movement cost for this terrain"""
        costs = {
            TerrainType.GRASS: 1.0,
            TerrainType.ROAD: 0.5,
            TerrainType.SAND: 1.5,
            TerrainType.FOREST: 2.0,
            TerrainType.WATER: float('inf'),
            TerrainType.MOUNTAIN: float('inf'),
            TerrainType.CITY: 1.0,
            TerrainType.BASE: 1.0
        }
        return costs.get(self.terrain, 1.0)
    
    def get_color(self) -> Tuple[int, int, int]:
        """Get color for this terrain"""
        colors = {
            TerrainType.GRASS: Colors.GRASS,
            TerrainType.WATER: Colors.WATER,
            TerrainType.MOUNTAIN: Colors.MOUNTAIN,
            TerrainType.FOREST: Colors.FOREST,
            TerrainType.SAND: Colors.SAND,
            TerrainType.ROAD: Colors.ROAD,
            TerrainType.CITY: (100, 100, 100),
            TerrainType.BASE: (150, 150, 150)
        }
        base_color = colors.get(self.terrain, Colors.GRASS)
        
        # Add elevation tint
        if self.elevation > 0.5:
            # Higher elevation = lighter
            tint = int(255 * 0.3 * (self.elevation - 0.5) / 0.5)
            base_color = tuple(min(255, c + tint) for c in base_color)
        elif self.elevation < -0.3:
            # Lower elevation = darker
            tint = int(255 * 0.4 * (-self.elevation) / 0.3)
            base_color = tuple(max(0, c - tint) for c in base_color)
        
        return base_color
    
    def copy(self) -> 'MapCell':
        """Create a copy"""
        return MapCell(
            x=self.x,
            y=self.y,
            terrain=self.terrain,
            elevation=self.elevation,
            owner=self.owner,
            resource=self.resource,
            resource_amount=self.resource_amount,
            building=self.building,
            fog_of_war=self.fog_of_war,
            explored=self.explored
        )


class MapGenerator:
    """Generates game maps with various algorithms"""
    
    def __init__(self):
        self.seed = None
        self.generation_method = "perlin"
    
    def set_seed(self, seed: int):
        """Set random seed for reproducible generation"""
        self.seed = seed
        random.seed(seed)
    
    def generate(self, width: int, height: int, 
                 teams: List[Team] = None) -> 'GameMap':
        """Generate a new map"""
        if self.seed is None:
            self.seed = random.randint(0, 2**32)
        
        logger.info(f"Generating map {width}x{height} with seed {self.seed}")
        
        game_map = GameMap(width, height)
        game_map.seed = self.seed
        
        # Generate base terrain
        self._generate_terrain(game_map)
        
        # Add rivers and lakes
        self._generate_water(game_map)
        
        # Add elevation
        self._generate_elevation(game_map)
        
        # Place resources
        self._generate_resources(game_map)
        
        # Create starting positions for teams
        if teams:
            self._generate_start_positions(game_map, teams)
        
        # Create roads
        self._generate_roads(game_map)
        
        # Place cities
        self._generate_cities(game_map)
        
        return game_map
    
    def _generate_terrain(self, game_map: 'GameMap'):
        """Generate base terrain using Perlin noise"""
        scale = 100.0
        octaves = 6
        persistence = 0.5
        lacunarity = 2.0
        
        for y in range(game_map.height):
            for x in range(game_map.width):
                # Normalize coordinates
                nx = x / game_map.width
                ny = y / game_map.height
                
                # Generate noise value
                value = noise.pnoise2(
                    nx * scale,
                    ny * scale,
                    octaves=octaves,
                    persistence=persistence,
                    lacunarity=lacunarity,
                    repeatx=game_map.width,
                    repeaty=game_map.height,
                    base=self.seed
                )
                
                # Determine terrain type based on noise value
                if value < -0.3:
                    terrain = TerrainType.WATER
                elif value < -0.1:
                    terrain = TerrainType.SAND
                elif value < 0.2:
                    terrain = TerrainType.GRASS
                elif value < 0.4:
                    terrain = TerrainType.FOREST
                elif value < 0.7:
                    terrain = TerrainType.GRASS
                else:
                    terrain = TerrainType.MOUNTAIN
                
                game_map.cells[y][x].terrain = terrain
    
    def _generate_elevation(self, game_map: 'GameMap'):
        """Generate elevation map"""
        scale = 80.0
        octaves = 4
        persistence = 0.5
        lacunarity = 2.0
        
        for y in range(game_map.height):
            for x in range(game_map.width):
                nx = x / game_map.width
                ny = y / game_map.height
                
                # Generate elevation noise
                value = noise.pnoise2(
                    nx * scale,
                    ny * scale,
                    octaves=octaves,
                    persistence=persistence,
                    lacunarity=lacunarity,
                    repeatx=game_map.width,
                    repeaty=game_map.height,
                    base=self.seed + 1000  # Different seed for elevation
                )
                
                # Normalize to [-1, 1] and store
                game_map.cells[y][x].elevation = value
    
    def _generate_water(self, game_map: 'GameMap'):
        """Generate rivers and lakes"""
        # Create some rivers
        num_rivers = random.randint(2, 5)
        for _ in range(num_rivers):
            self._create_river(game_map)
        
        # Create some lakes
        num_lakes = random.randint(3, 8)
        for _ in range(num_lakes):
            self._create_lake(game_map)
    
    def _create_river(self, game_map: 'GameMap'):
        """Create a river on the map"""
        # Start from edge
        start_side = random.randint(0, 3)  # 0: top, 1: right, 2: bottom, 3: left
        
        if start_side == 0:  # Top
            x, y = random.randint(0, game_map.width - 1), 0
        elif start_side == 1:  # Right
            x, y = game_map.width - 1, random.randint(0, game_map.height - 1)
        elif start_side == 2:  # Bottom
            x, y = random.randint(0, game_map.width - 1), game_map.height - 1
        else:  # Left
            x, y = 0, random.randint(0, game_map.height - 1)
        
        # River properties
        length = random.randint(20, 60)
        width = random.randint(2, 5)
        
        # Create river path
        path = [(x, y)]
        for _ in range(length):
            # Move in a somewhat straight direction
            direction = random.choice([
                (0, 1), (1, 0), (0, -1), (-1, 0),
                (1, 1), (1, -1), (-1, 1), (-1, -1)
            ])
            
            # Bias towards continuing in same direction
            if len(path) > 1:
                last_dir = (path[-1][0] - path[-2][0], path[-1][1] - path[-2][1])
                if last_dir in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    # 70% chance to continue in same direction
                    if random.random() < 0.7:
                        direction = last_dir
            
            nx, ny = x + direction[0], y + direction[1]
            
            # Check bounds
            if 0 <= nx < game_map.width and 0 <= ny < game_map.height:
                x, y = nx, ny
                path.append((x, y))
            else:
                break
        
        # Draw river
        for px, py in path:
            for dx in range(-width, width + 1):
                for dy in range(-width, width + 1):
                    if abs(dx) + abs(dy) <= width:
                        nx, ny = px + dx, py + dy
                        if 0 <= nx < game_map.width and 0 <= ny < game_map.height:
                            game_map.cells[ny][nx].terrain = TerrainType.WATER
    
    def _create_lake(self, game_map: 'GameMap'):
        """Create a lake on the map"""
        # Random position
        center_x = random.randint(10, game_map.width - 11)
        center_y = random.randint(10, game_map.height - 11)
        
        # Lake size
        radius_x = random.randint(5, 15)
        radius_y = random.randint(5, 15)
        
        # Draw lake (ellipse shape)
        for y in range(game_map.height):
            for x in range(game_map.width):
                # Normalized coordinates
                nx = (x - center_x) / radius_x
                ny = (y - center_y) / radius_y
                
                # Check if inside ellipse
                if nx**2 + ny**2 <= 1.0:
                    # Add some noise to make it natural
                    noise_val = noise.pnoise2(
                        x / game_map.width * 50,
                        y / game_map.height * 50,
                        octaves=2,
                        base=self.seed + 2000
                    )
                    
                    if nx**2 + ny**2 + noise_val * 0.3 <= 1.0:
                        game_map.cells[y][x].terrain = TerrainType.WATER
    
    def _generate_resources(self, game_map: 'GameMap'):
        """Generate resources on the map"""
        # Resource types and their spawn rates
        resources = [
            ("gold", 0.01),
            ("oil", 0.005),
            ("food", 0.015),
            ("wood", 0.02)
        ]
        
        for y in range(game_map.height):
            for x in range(game_map.width):
                cell = game_map.cells[y][x]
                
                # Skip water and mountains
                if cell.terrain in [TerrainType.WATER, TerrainType.MOUNTAIN]:
                    continue
                
                # Random chance to place resource
                for resource, probability in resources:
                    if random.random() < probability:
                        # Check if already has resource
                        if cell.resource is None:
                            cell.resource = resource
                            cell.resource_amount = random.uniform(100, 500)
    
    def _generate_start_positions(self, game_map: 'GameMap', teams: List[Team]):
        """Generate start positions for teams"""
        num_teams = len(teams)
        
        if num_teams == 2:
            # Place at opposite corners
            positions = [
                (10, 10),
                (game_map.width - 11, game_map.height - 11)
            ]
        elif num_teams == 4:
            # Place in each corner
            positions = [
                (10, 10),
                (game_map.width - 11, 10),
                (10, game_map.height - 11),
                (game_map.width - 11, game_map.height - 11)
            ]
        else:
            # Distribute evenly
            positions = []
            for i in range(num_teams):
                angle = 2 * math.pi * i / num_teams
                radius = min(game_map.width, game_map.height) * 0.4
                cx, cy = game_map.width // 2, game_map.height // 2
                x = int(cx + radius * math.cos(angle))
                y = int(cy + radius * math.sin(angle))
                positions.append((x, y))
        
        # Assign positions to teams
        for team, (x, y) in zip(teams, positions):
            # Clear area around start position
            for dy in range(-5, 6):
                for dx in range(-5, 6):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < game_map.width and 0 <= ny < game_map.height:
                        game_map.cells[ny][nx].terrain = TerrainType.GRASS
                        game_map.cells[ny][nx].elevation = 0.0
            
            # Mark base area
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < game_map.width and 0 <= ny < game_map.height:
                        game_map.cells[ny][nx].terrain = TerrainType.BASE
                        game_map.cells[ny][nx].owner = team
            
            # Set team start position
            game_map.team_start_positions[team] = Vector2(x, y)
    
    def _generate_roads(self, game_map: 'GameMap'):
        """Generate roads connecting start positions"""
        if len(game_map.team_start_positions) < 2:
            return
        
        positions = list(game_map.team_start_positions.values())
        
        # Connect each start position to others
        for i in range(len(positions)):
            for j in range(i + 1, len(positions)):
                start = positions[i]
                end = positions[j]
                self._create_road(game_map, start, end)
    
    def _create_road(self, game_map: 'GameMap', start: Vector2, end: Vector2):
        """Create a road between two points"""
        # Simple line for now (could use A* for better path)
        dx = end.x - start.x
        dy = end.y - start.y
        steps = max(abs(dx), abs(dy))
        
        if steps == 0:
            return
        
        for i in range(int(steps) + 1):
            t = i / steps
            x = int(start.x + dx * t)
            y = int(start.y + dy * t)
            
            if 0 <= x < game_map.width and 0 <= y < game_map.height:
                # Only place road on walkable terrain
                if game_map.cells[y][x].is_walkable():
                    game_map.cells[y][x].terrain = TerrainType.ROAD
    
    def _generate_cities(self, game_map: 'GameMap'):
        """Generate cities on the map"""
        num_cities = random.randint(3, 8)
        
        for _ in range(num_cities):
            # Find a good location for city
            for attempt in range(100):
                x = random.randint(10, game_map.width - 11)
                y = random.randint(10, game_map.height - 11)
                
                # Check if area is suitable
                suitable = True
                for dy in range(-3, 4):
                    for dx in range(-3, 4):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < game_map.width and 0 <= ny < game_map.height:
                            if not game_map.cells[ny][nx].is_walkable():
                                suitable = False
                                break
                    if not suitable:
                        break
                
                if suitable:
                    # Create city
                    for dy in range(-2, 3):
                        for dx in range(-2, 3):
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < game_map.width and 0 <= ny < game_map.height:
                                if random.random() < 0.7:  # 70% chance to be city
                                    game_map.cells[ny][nx].terrain = TerrainType.CITY
                    break


class GameMap:
    """The game map containing terrain, resources, and buildings"""
    
    def __init__(self, width: int = GameSettings.MAP_WIDTH, 
                 height: int = GameSettings.MAP_HEIGHT):
        self.width = width
        self.height = height
        self.cells: List[List[MapCell]] = []
        self.seed = None
        self.team_start_positions: Dict[Team, Vector2] = {}
        self.pathfinder = Pathfinder(width, height)
        
        # Initialize cells
        self._initialize_cells()
    
    def _initialize_cells(self):
        """Initialize all cells"""
        self.cells = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                row.append(MapCell(x, y))
            self.cells.append(row)
    
    def get_cell(self, x: int, y: int) -> Optional[MapCell]:
        """Get cell at position"""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.cells[y][x]
        return None
    
    def get_cell_at_position(self, position: Vector2) -> Optional[MapCell]:
        """Get cell at vector position"""
        return self.get_cell(int(position.x), int(position.y))
    
    def get_terrain(self, x: int, y: int) -> TerrainType:
        """Get terrain type at position"""
        cell = self.get_cell(x, y)
        return cell.terrain if cell else TerrainType.GRASS
    
    def is_walkable(self, x: int, y: int) -> bool:
        """Check if position is walkable"""
        cell = self.get_cell(x, y)
        return cell is not None and cell.is_walkable()
    
    def get_movement_cost(self, x: int, y: int) -> float:
        """Get movement cost at position"""
        cell = self.get_cell(x, y)
        return cell.get_movement_cost() if cell else float('inf')
    
    def set_owner(self, x: int, y: int, team: Team):
        """Set owner of cell"""
        cell = self.get_cell(x, y)
        if cell:
            cell.owner = team
    
    def get_owner(self, x: int, y: int) -> Optional[Team]:
        """Get owner of cell"""
        cell = self.get_cell(x, y)
        return cell.owner if cell else None
    
    def find_path(self, start: Vector2, end: Vector2) -> List[Vector2]:
        """Find path between two points"""
        start_int = (int(start.x), int(start.y))
        end_int = (int(end.x), int(end.y))
        
        # Create terrain grid for pathfinding
        terrain_grid = [[self.get_terrain(x, y) for x in range(self.width)] 
                       for y in range(self.height)]
        
        result = self.pathfinder.find_path(start_int, end_int, terrain_grid)
        
        if result.success:
            return [Vector2(x, y) for x, y in result.path]
        else:
            # Return direct line if no path found
            return [start, end]
    
    def find_path_continuous(self, start: Vector2, end: Vector2) -> List[Vector2]:
        """Find continuous path with sub-cell precision"""
        path = self.find_path(start, end)
        
        # Add start and end positions exactly
        if path:
            path[0] = start.copy()
            path[-1] = end.copy()
        
        return path
    
    def get_neighbors(self, x: int, y: int, include_diagonal: bool = True) -> List[Tuple[int, int]]:
        """Get walkable neighbor positions"""
        neighbors = []
        
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        if include_diagonal:
            directions.extend([(-1, -1), (-1, 1), (1, -1), (1, 1)])
        
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.width and 0 <= ny < self.height:
                if self.is_walkable(nx, ny):
                    neighbors.append((nx, ny))
        
        return neighbors
    
    def get_cells_in_radius(self, center: Vector2, radius: float) -> List[MapCell]:
        """Get all cells within radius of center"""
        cells = []
        radius_sq = radius ** 2
        
        for y in range(max(0, int(center.y - radius)), min(self.height, int(center.y + radius) + 1)):
            for x in range(max(0, int(center.x - radius)), min(self.width, int(center.x + radius) + 1)):
                dx = x - center.x
                dy = y - center.y
                if dx**2 + dy**2 <= radius_sq:
                    cells.append(self.cells[y][x])
        
        return cells
    
    def get_cells_in_rect(self, rect: Tuple[float, float, float, float]) -> List[MapCell]:
        """Get all cells within rectangle"""
        cells = []
        rx, ry, rw, rh = rect
        
        x0 = max(0, int(rx))
        x1 = min(self.width, int(rx + rw) + 1)
        y0 = max(0, int(ry))
        y1 = min(self.height, int(ry + rh) + 1)
        
        for y in range(y0, y1):
            for x in range(x0, x1):
                cells.append(self.cells[y][x])
        
        return cells
    
    def reveal_area(self, center: Vector2, radius: float, team: Team):
        """Reveal fog of war in area for team"""
        for cell in self.get_cells_in_radius(center, radius):
            cell.fog_of_war = False
            cell.explored = True
    
    def hide_area(self, center: Vector2, radius: float):
        """Hide area with fog of war"""
        for cell in self.get_cells_in_radius(center, radius):
            if cell.explored:
                cell.fog_of_war = True
    
    def is_visible(self, x: int, y: int) -> bool:
        """Check if cell is visible (not covered by fog of war)"""
        cell = self.get_cell(x, y)
        return cell is not None and not cell.fog_of_war
    
    def get_start_position(self, team: Team) -> Optional[Vector2]:
        """Get start position for team"""
        return self.team_start_positions.get(team)
    
    def get_spawn_position(self, team: Team, offset: int = 0) -> Vector2:
        """Get spawn position for team (with offset)"""
        start = self.get_start_position(team)
        if start is None:
            return Vector2(self.width // 2, self.height // 2)
        
        # Add offset in random direction
        angle = offset * 0.5  # Radians
        radius = 3 + offset * 0.5
        return Vector2(
            start.x + math.cos(angle) * radius,
            start.y + math.sin(angle) * radius
        )
    
    def get_random_position(self, terrain_filter: List[TerrainType] = None) -> Vector2:
        """Get random position on map with optional terrain filter"""
        for _ in range(100):  # Try 100 times
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            
            if terrain_filter:
                if self.get_terrain(x, y) in terrain_filter:
                    return Vector2(x, y)
            else:
                if self.is_walkable(x, y):
                    return Vector2(x, y)
        
        # Fallback to center
        return Vector2(self.width // 2, self.height // 2)
    
    def get_random_walkable_position(self) -> Vector2:
        """Get random walkable position"""
        return self.get_random_position([t for t in TerrainType if t not in [TerrainType.WATER, TerrainType.MOUNTAIN]])
    
    def to_grid_coordinates(self, world_pos: Vector2) -> Tuple[int, int]:
        """Convert world position to grid coordinates"""
        return (int(world_pos.x), int(world_pos.y))
    
    def to_world_coordinates(self, grid_x: int, grid_y: int) -> Vector2:
        """Convert grid coordinates to world position"""
        return Vector2(grid_x, grid_y)
    
    def get_bounds(self) -> Tuple[float, float, float, float]:
        """Get map bounds (x, y, width, height)"""
        return (0, 0, self.width, self.height)
    
    def get_center(self) -> Vector2:
        """Get map center"""
        return Vector2(self.width / 2, self.height / 2)
    
    def save(self) -> dict:
        """Save map to dictionary"""
        data = {
            'width': self.width,
            'height': self.height,
            'seed': self.seed,
            'cells': [],
            'team_start_positions': {t.value: {'x': p.x, 'y': p.y} 
                                    for t, p in self.team_start_positions.items()}
        }
        
        for row in self.cells:
            row_data = []
            for cell in row:
                row_data.append({
                    'terrain': cell.terrain.value,
                    'elevation': cell.elevation,
                    'owner': cell.owner.value if cell.owner else None,
                    'resource': cell.resource,
                    'resource_amount': cell.resource_amount,
                    'building': cell.building,
                    'explored': cell.explored
                })
            data['cells'].append(row_data)
        
        return data
    
    def load(self, data: dict):
        """Load map from dictionary"""
        self.width = data['width']
        self.height = data['height']
        self.seed = data.get('seed')
        self.team_start_positions = {}
        
        # Load team start positions
        for team_val, pos in data.get('team_start_positions', {}).items():
            self.team_start_positions[Team(int(team_val))] = Vector2(pos['x'], pos['y'])
        
        # Initialize cells
        self._initialize_cells()
        
        # Load cell data
        for y, row_data in enumerate(data.get('cells', [])):
            for x, cell_data in enumerate(row_data):
                if y < self.height and x < self.width:
                    cell = self.cells[y][x]
                    cell.terrain = TerrainType(cell_data.get('terrain', 'grass'))
                    cell.elevation = cell_data.get('elevation', 0.0)
                    cell.owner = Team(cell_data.get('owner')) if cell_data.get('owner') is not None else None
                    cell.resource = cell_data.get('resource')
                    cell.resource_amount = cell_data.get('resource_amount', 0.0)
                    cell.building = cell_data.get('building')
                    cell.explored = cell_data.get('explored', False)
        
        # Update pathfinder
        self.pathfinder = Pathfinder(self.width, self.height)


# Global map generator instance
map_generator = MapGenerator()
