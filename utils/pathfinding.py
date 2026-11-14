"""
Pathfinding algorithms for Frontwars
"""

import heapq
from typing import List, Tuple, Dict, Optional, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
import math
import time

from .vector import Vector2
from config import GameSettings, TerrainType


class PathfindingAlgorithm(Enum):
    ASTAR = "astar"
    DIJKSTRA = "dijkstra"
    BFS = "bfs"
    JPS = "jps"  # Jump Point Search


@dataclass
class Node:
    """Node for pathfinding"""
    x: int
    y: int
    cost: float = 0.0
    heuristic: float = 0.0
    parent: Optional['Node'] = None
    
    @property
    def total_cost(self) -> float:
        return self.cost + self.heuristic
    
    def __lt__(self, other: 'Node') -> bool:
        return self.total_cost < other.total_cost


@dataclass
class PathResult:
    """Result of pathfinding operation"""
    path: List[Tuple[int, int]] = field(default_factory=list)
    cost: float = 0.0
    success: bool = False
    iterations: int = 0
    time_elapsed: float = 0.0
    message: str = ""
    
    def __bool__(self) -> bool:
        return self.success


class Pathfinder:
    """Base pathfinding class"""
    
    def __init__(self, 
                 grid_width: int = GameSettings.MAP_WIDTH,
                 grid_height: int = GameSettings.MAP_HEIGHT,
                 max_iterations: int = GameSettings.PATHFINDING_MAX_ITERATIONS):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.max_iterations = max_iterations
        self.algorithm = PathfindingAlgorithm.ASTAR
        
        # Movement cost weights
        self.movement_costs = {
            TerrainType.GRASS: 1.0,
            TerrainType.ROAD: 0.5,
            TerrainType.SAND: 1.5,
            TerrainType.FOREST: 2.0,
            TerrainType.WATER: float('inf'),  # Impassable
            TerrainType.MOUNTAIN: float('inf'),  # Impassable
            TerrainType.CITY: 1.0,
            TerrainType.BASE: 1.0
        }
        
        # Cache for pathfinding results
        self.path_cache: Dict[Tuple[Tuple[int, int], Tuple[int, int]], PathResult] = {}
        self.last_pathfind_time = 0.0
        
    def set_grid_size(self, width: int, height: int):
        """Set grid dimensions"""
        self.grid_width = width
        self.grid_height = height
        
    def set_movement_cost(self, terrain_type: TerrainType, cost: float):
        """Set movement cost for terrain type"""
        self.movement_costs[terrain_type] = cost
        
    def get_movement_cost(self, terrain_type: TerrainType) -> float:
        """Get movement cost for terrain type"""
        return self.movement_costs.get(terrain_type, 1.0)
    
    def is_walkable(self, x: int, y: int, grid: List[List[TerrainType]]) -> bool:
        """Check if position is walkable"""
        if not (0 <= x < self.grid_width and 0 <= y < self.grid_height):
            return False
        
        terrain = grid[y][x] if 0 <= y < len(grid) and 0 <= x < len(grid[0]) else None
        if terrain is None:
            return False
            
        cost = self.get_movement_cost(terrain)
        return cost < float('inf')
    
    def heuristic(self, a: Tuple[int, int], b: Tuple[int, int]) -> float:
        """Calculate heuristic between two points (Euclidean distance)"""
        return math.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)
    
    def manhattan_distance(self, a: Tuple[int, int], b: Tuple[int, int]) -> float:
        """Calculate Manhattan distance"""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    
    def get_neighbors(self, x: int, y: int, grid: List[List[TerrainType]],
                      allow_diagonal: bool = True) -> List[Tuple[int, int]]:
        """Get walkable neighbor positions"""
        neighbors = []
        
        # Cardinal directions
        directions = [
            (-1, 0), (1, 0), (0, -1), (0, 1)
        ]
        
        # Add diagonal directions
        if allow_diagonal:
            directions.extend([
                (-1, -1), (-1, 1), (1, -1), (1, 1)
            ])
        
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if self.is_walkable(nx, ny, grid):
                neighbors.append((nx, ny))
                
        return neighbors
    
    def find_path(self, 
                  start: Tuple[int, int], 
                  end: Tuple[int, int],
                  grid: List[List[TerrainType]],
                  max_path_length: int = GameSettings.PATHFINDING_MAX_PATH_LENGTH) -> PathResult:
        """Find path from start to end"""
        start_time = time.time()
        iterations = 0
        
        # Check cache
        cache_key = (start, end)
        if cache_key in self.path_cache:
            cached = self.path_cache[cache_key]
            # Only use cache if grid hasn't changed significantly
            # (In a real implementation, we'd need to track grid changes)
            return cached
        
        # Validate inputs
        if not self.is_walkable(start[0], start[1], grid):
            return PathResult(
                success=False,
                message=f"Start position {start} is not walkable"
            )
            
        if not self.is_walkable(end[0], end[1], grid):
            return PathResult(
                success=False,
                message=f"End position {end} is not walkable"
            )
        
        # Use the selected algorithm
        if self.algorithm == PathfindingAlgorithm.ASTAR:
            result = self._astar(start, end, grid, max_path_length)
        elif self.algorithm == PathfindingAlgorithm.DIJKSTRA:
            result = self._dijkstra(start, end, grid, max_path_length)
        elif self.algorithm == PathfindingAlgorithm.BFS:
            result = self._bfs(start, end, grid, max_path_length)
        else:
            result = self._astar(start, end, grid, max_path_length)
        
        result.iterations = iterations
        result.time_elapsed = time.time() - start_time
        
        # Cache result
        if result.success and len(self.path_cache) < 1000:
            self.path_cache[cache_key] = result
            
        return result
    
    def _astar(self, start: Tuple[int, int], end: Tuple[int, int],
               grid: List[List[TerrainType]],
               max_path_length: int) -> PathResult:
        """A* pathfinding algorithm"""
        iterations = 0
        
        # Priority queue
        open_set: List[Node] = []
        
        # Create start node
        start_node = Node(start[0], start[1], 0.0, self.heuristic(start, end))
        start_node.parent = None
        
        heapq.heappush(open_set, start_node)
        
        # Track visited nodes and their best costs
        closed_set: Set[Tuple[int, int]] = set()
        g_scores: Dict[Tuple[int, int], float] = {start: 0.0}
        f_scores: Dict[Tuple[int, int], float] = {start: start_node.total_cost}
        came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}
        
        while open_set and iterations < self.max_iterations:
            iterations += 1
            
            # Get node with lowest f_score
            current_node = heapq.heappop(open_set)
            current = (current_node.x, current_node.y)
            
            # Check if we reached the goal
            if current == end:
                path = self._reconstruct_path(came_from, current)
                if len(path) <= max_path_length:
                    return PathResult(
                        path=path,
                        cost=g_scores[current],
                        success=True,
                        iterations=iterations,
                        message="Path found"
                    )
                else:
                    return PathResult(
                        success=False,
                        message="Path too long"
                    )
            
            if current in closed_set:
                continue
                
            closed_set.add(current)
            
            # Explore neighbors
            for neighbor in self.get_neighbors(current[0], current[1], grid):
                if neighbor in closed_set:
                    continue
                    
                # Calculate tentative g_score
                terrain = grid[neighbor[1]][neighbor[0]]
                movement_cost = self.get_movement_cost(terrain)
                
                # Diagonal movement costs more
                if abs(neighbor[0] - current[0]) > 0 and abs(neighbor[1] - current[1]) > 0:
                    movement_cost *= 1.414  # sqrt(2)
                
                tentative_g_score = g_scores[current] + movement_cost
                
                if neighbor not in g_scores or tentative_g_score < g_scores[neighbor]:
                    # This path to neighbor is better
                    came_from[neighbor] = current
                    g_scores[neighbor] = tentative_g_score
                    f_scores[neighbor] = tentative_g_score + self.heuristic(neighbor, end)
                    
                    # Create node and add to open set
                    neighbor_node = Node(
                        neighbor[0], neighbor[1],
                        tentative_g_score,
                        self.heuristic(neighbor, end)
                    )
                    neighbor_node.parent = current_node
                    heapq.heappush(open_set, neighbor_node)
        
        # No path found
        return PathResult(
            success=False,
            message="No path found"
        )
    
    def _dijkstra(self, start: Tuple[int, int], end: Tuple[int, int],
                  grid: List[List[TerrainType]],
                  max_path_length: int) -> PathResult:
        """Dijkstra's algorithm (uniform cost search)"""
        iterations = 0
        
        open_set: List[Node] = []
        start_node = Node(start[0], start[1], 0.0, 0.0)
        heapq.heappush(open_set, start_node)
        
        closed_set: Set[Tuple[int, int]] = set()
        g_scores: Dict[Tuple[int, int], float] = {start: 0.0}
        came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}
        
        while open_set and iterations < self.max_iterations:
            iterations += 1
            
            current_node = heapq.heappop(open_set)
            current = (current_node.x, current_node.y)
            
            if current == end:
                path = self._reconstruct_path(came_from, current)
                if len(path) <= max_path_length:
                    return PathResult(
                        path=path,
                        cost=g_scores[current],
                        success=True,
                        iterations=iterations
                    )
                else:
                    return PathResult(success=False, message="Path too long")
            
            if current in closed_set:
                continue
                
            closed_set.add(current)
            
            for neighbor in self.get_neighbors(current[0], current[1], grid):
                if neighbor in closed_set:
                    continue
                    
                terrain = grid[neighbor[1]][neighbor[0]]
                movement_cost = self.get_movement_cost(terrain)
                
                if abs(neighbor[0] - current[0]) > 0 and abs(neighbor[1] - current[1]) > 0:
                    movement_cost *= 1.414
                
                tentative_g_score = g_scores[current] + movement_cost
                
                if neighbor not in g_scores or tentative_g_score < g_scores[neighbor]:
                    came_from[neighbor] = current
                    g_scores[neighbor] = tentative_g_score
                    
                    neighbor_node = Node(neighbor[0], neighbor[1], tentative_g_score, 0.0)
                    heapq.heappush(open_set, neighbor_node)
        
        return PathResult(success=False, message="No path found")
    
    def _bfs(self, start: Tuple[int, int], end: Tuple[int, int],
             grid: List[List[TerrainType]],
             max_path_length: int) -> PathResult:
        """Breadth-First Search algorithm"""
        iterations = 0
        
        from collections import deque
        queue = deque([start])
        visited = {start: None}
        
        while queue and iterations < self.max_iterations:
            iterations += 1
            current = queue.popleft()
            
            if current == end:
                path = self._reconstruct_path(visited, current)
                if len(path) <= max_path_length:
                    return PathResult(
                        path=path,
                        cost=len(path),
                        success=True,
                        iterations=iterations
                    )
                else:
                    return PathResult(success=False, message="Path too long")
            
            if current in visited and visited[current] is not None:
                continue
                
            visited[current] = current
            
            for neighbor in self.get_neighbors(current[0], current[1], grid):
                if neighbor not in visited:
                    visited[neighbor] = current
                    queue.append(neighbor)
        
        return PathResult(success=False, message="No path found")
    
    def _reconstruct_path(self, came_from: Dict[Tuple[int, int], Tuple[int, int]],
                         current: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Reconstruct path from came_from dictionary"""
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
            # Prevent infinite loops
            if len(path) > self.max_iterations:
                break
        
        path.reverse()
        return path
    
    def find_path_to_position(self, start: Vector2, end: Vector2,
                              grid: List[List[TerrainType]]) -> List[Vector2]:
        """Find path from Vector2 start to Vector2 end"""
        start_int = (int(start.x), int(start.y))
        end_int = (int(end.x), int(end.y))
        
        result = self.find_path(start_int, end_int, grid)
        
        if result.success:
            return [Vector2(x, y) for x, y in result.path]
        else:
            # Try to find closest walkable position to end
            closest = self._find_closest_walkable(end_int, grid)
            if closest:
                result = self.find_path(start_int, closest, grid)
                if result.success:
                    return [Vector2(x, y) for x, y in result.path]
            
            # Return direct line if no path found
            return [start, end]
    
    def _find_closest_walkable(self, position: Tuple[int, int],
                               grid: List[List[TerrainType]],
                               radius: int = 5) -> Optional[Tuple[int, int]]:
        """Find closest walkable position to given position"""
        x, y = position
        
        # Check position itself
        if self.is_walkable(x, y, grid):
            return (x, y)
        
        # Check positions in expanding radius
        for r in range(1, radius + 1):
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    if abs(dx) == r or abs(dy) == r:  # Only check perimeter
                        nx, ny = x + dx, y + dy
                        if self.is_walkable(nx, ny, grid):
                            return (nx, ny)
        
        return None
    
    def simplify_path(self, path: List[Vector2], tolerance: float = 0.5) -> List[Vector2]:
        """Simplify path using Douglas-Peucker algorithm"""
        if len(path) <= 2:
            return path
            
        # Convert to numpy for easier calculations
        import numpy as np
        points = np.array([(p.x, p.y) for p in path])
        
        def douglas_peucker(points, epsilon):
            if len(points) <= 2:
                return points
            
            # Find point with maximum distance
            dmax = 0
            index = 0
            end = len(points) - 1
            
            for i in range(1, end):
                d = self._perpendicular_distance(points[i], points[0], points[end])
                if d > dmax:
                    index = i
                    dmax = d
            
            # If max distance is greater than epsilon, recursively simplify
            if dmax > epsilon:
                results = []
                results.extend(douglas_peucker(points[:index+1], epsilon))
                results.extend(douglas_peucker(points[index:], epsilon)[1:])
                return results
            else:
                return [points[0], points[end]]
        
        simplified = douglas_peucker(points, tolerance)
        return [Vector2(p[0], p[1]) for p in simplified]
    
    def _perpendicular_distance(self, point, line_start, line_end):
        """Calculate perpendicular distance from point to line"""
        if np.array_equal(line_start, line_end):
            return np.linalg.norm(point - line_start)
        
        line_vec = line_end - line_start
        point_vec = point - line_start
        line_len = np.linalg.norm(line_vec)
        line_unit = line_vec / line_len
        
        proj = np.dot(point_vec, line_unit)
        proj_point = line_start + proj * line_unit
        
        return np.linalg.norm(point - proj_point)
    
    def clear_cache(self):
        """Clear pathfinding cache"""
        self.path_cache.clear()


class AStarPathfinder(Pathfinder):
    """A* pathfinding with optimizations"""
    
    def __init__(self, grid_width: int = GameSettings.MAP_WIDTH,
                 grid_height: int = GameSettings.MAP_HEIGHT):
        super().__init__(grid_width, grid_height)
        self.algorithm = PathfindingAlgorithm.ASTAR
        
        # Optimizations
        self.use_jump_point = False
        self.use_bi_directional = False
        self.use_hierarchical = False
    
    def find_path(self, start: Tuple[int, int], end: Tuple[int, int],
                  grid: List[List[TerrainType]],
                  max_path_length: int = GameSettings.PATHFINDING_MAX_PATH_LENGTH) -> PathResult:
        """Optimized A* pathfinding"""
        
        # Quick check for same position
        if start == end:
            return PathResult(
                path=[start, end],
                cost=0.0,
                success=True,
                message="Start and end are the same"
            )
        
        # Use standard A* for now
        return super().find_path(start, end, grid, max_path_length)
    
    def find_path_continuous(self, start: Vector2, end: Vector2,
                            grid: List[List[TerrainType]],
                            collision_radius: float = 0.5) -> List[Vector2]:
        """Find continuous path with collision avoidance"""
        # Convert to grid coordinates
        start_grid = (int(start.x), int(start.y))
        end_grid = (int(end.x), int(end.y))
        
        # Find path on grid
        result = self.find_path(start_grid, end_grid, grid)
        
        if result.success:
            # Convert to continuous path
            path = [Vector2(p[0] + 0.5, p[1] + 0.5) for p in result.path]
            
            # Add start and end positions
            if len(path) > 0:
                path[0] = start
                path[-1] = end
            
            return path
        else:
            # Fallback: direct line
            return [start, end]


# Global pathfinder instance
pathfinder = AStarPathfinder()
