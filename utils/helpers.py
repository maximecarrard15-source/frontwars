"""
Helper functions for Frontwars
"""

import math
import random
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import pygame

from .vector import Vector2
from config import Colors, GameSettings


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value between min and max"""
    return max(min_val, min(max_val, value))


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation"""
    return a + (b - a) * t


def inverse_lerp(a: float, b: float, value: float) -> float:
    """Inverse linear interpolation"""
    if a == b:
        return 0.0
    return (value - a) / (b - a)


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    """Smoothstep interpolation (smooth transition)"""
    t = inverse_lerp(edge0, edge1, x)
    t = clamp(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def remap(value: float, from_min: float, from_max: float, 
          to_min: float, to_max: float) -> float:
    """Remap value from one range to another"""
    t = inverse_lerp(from_min, from_max, value)
    return lerp(to_min, to_max, t)


def distance(a: Union[Vector2, Tuple[float, float]], 
             b: Union[Vector2, Tuple[float, float]]) -> float:
    """Calculate distance between two points"""
    if isinstance(a, Vector2) and isinstance(b, Vector2):
        return a.distance_to(b)
    elif isinstance(a, Vector2):
        return a.distance_to(Vector2.from_tuple(b))
    elif isinstance(b, Vector2):
        return Vector2.from_tuple(a).distance_to(b)
    else:
        return math.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)


def distance_squared(a: Union[Vector2, Tuple[float, float]], 
                     b: Union[Vector2, Tuple[float, float]]) -> float:
    """Calculate squared distance (faster, no sqrt)"""
    if isinstance(a, Vector2) and isinstance(b, Vector2):
        return a.distance_squared_to(b)
    elif isinstance(a, Vector2):
        return a.distance_squared_to(Vector2.from_tuple(b))
    elif isinstance(b, Vector2):
        return Vector2.from_tuple(a).distance_squared_to(b)
    else:
        return (a[0] - b[0])**2 + (a[1] - b[1])**2


def normalize(x: float, y: float) -> Tuple[float, float]:
    """Normalize coordinates to unit length"""
    length = math.sqrt(x**2 + y**2)
    if length > 0:
        return (x / length, y / length)
    return (0.0, 0.0)


def rotate_point(point: Tuple[float, float], 
                 center: Tuple[float, float], 
                 angle: float) -> Tuple[float, float]:
    """Rotate point around center by angle (radians)"""
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    
    px = point[0] - center[0]
    py = point[1] - center[1]
    
    new_x = px * cos_a - py * sin_a
    new_y = px * sin_a + py * cos_a
    
    return (new_x + center[0], new_y + center[1])


def angle_between(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    """Calculate angle between two vectors (radians)"""
    dot = a[0] * b[0] + a[1] * b[1]
    det = a[0] * b[1] - a[1] * b[0]
    return math.atan2(det, dot)


def direction_to_angle(dx: float, dy: float) -> float:
    """Convert direction vector to angle (radians)"""
    return math.atan2(dy, dx)


def angle_to_direction(angle: float) -> Tuple[float, float]:
    """Convert angle to direction vector"""
    return (math.cos(angle), math.sin(angle))


def random_point_in_circle(center: Tuple[float, float], 
                           radius: float) -> Tuple[float, float]:
    """Generate random point inside circle"""
    angle = random.uniform(0, 2 * math.pi)
    r = random.uniform(0, radius)
    return (
        center[0] + r * math.cos(angle),
        center[1] + r * math.sin(angle)
    )


def random_point_in_rect(rect: Tuple[float, float, float, float]) -> Tuple[float, float]:
    """Generate random point inside rectangle"""
    x, y, w, h = rect
    return (
        x + random.uniform(0, w),
        y + random.uniform(0, h)
    )


def point_in_rect(point: Tuple[float, float], 
                  rect: Tuple[float, float, float, float]) -> bool:
    """Check if point is inside rectangle (x, y, width, height)"""
    x, y = point
    rx, ry, rw, rh = rect
    return rx <= x <= rx + rw and ry <= y <= ry + rh


def point_in_circle(point: Tuple[float, float], 
                    center: Tuple[float, float], 
                    radius: float) -> bool:
    """Check if point is inside circle"""
    dx = point[0] - center[0]
    dy = point[1] - center[1]
    return dx**2 + dy**2 <= radius**2


def rects_overlap(rect1: Tuple[float, float, float, float],
                  rect2: Tuple[float, float, float, float]) -> bool:
    """Check if two rectangles overlap"""
    r1x, r1y, r1w, r1h = rect1
    r2x, r2y, r2w, r2h = rect2
    
    return not (r1x + r1w < r2x or r2x + r2w < r1x or
                r1y + r1h < r2y or r2y + r2h < r1y)


def circle_overlaps_rect(circle_center: Tuple[float, float], 
                          circle_radius: float,
                          rect: Tuple[float, float, float, float]) -> bool:
    """Check if circle overlaps with rectangle"""
    # Find the closest point in the rectangle to the circle center
    closest_x = clamp(circle_center[0], rect[0], rect[0] + rect[2])
    closest_y = clamp(circle_center[1], rect[1], rect[1] + rect[3])
    
    # Calculate distance
    dx = circle_center[0] - closest_x
    dy = circle_center[1] - closest_y
    
    return (dx**2 + dy**2) <= (circle_radius**2)


def circles_overlap(center1: Tuple[float, float], radius1: float,
                    center2: Tuple[float, float], radius2: float) -> bool:
    """Check if two circles overlap"""
    dx = center1[0] - center2[0]
    dy = center1[1] - center2[1]
    distance_sq = dx**2 + dy**2
    return distance_sq <= (radius1 + radius2)**2


def line_rect_intersection(line_start: Tuple[float, float],
                           line_end: Tuple[float, float],
                           rect: Tuple[float, float, float, float]) -> Optional[Tuple[float, float]]:
    """Find intersection between line and rectangle"""
    rx, ry, rw, rh = rect
    
    # Check intersection with each edge
    edges = [
        ((rx, ry), (rx + rw, ry)),      # Top
        ((rx + rw, ry), (rx + rw, ry + rh)),  # Right
        ((rx + rw, ry + rh), (rx, ry + rh)),  # Bottom
        ((rx, ry + rh), (rx, ry))       # Left
    ]
    
    for edge_start, edge_end in edges:
        intersection = line_line_intersection(line_start, line_end, edge_start, edge_end)
        if intersection:
            return intersection
    
    return None


def line_line_intersection(a1: Tuple[float, float], a2: Tuple[float, float],
                           b1: Tuple[float, float], b2: Tuple[float, float]) -> Optional[Tuple[float, float]]:
    """Find intersection between two line segments"""
    # Line segment intersection using parametric equations
    s1_x = a2[0] - a1[0]
    s1_y = a2[1] - a1[1]
    s2_x = b2[0] - b1[0]
    s2_y = b2[1] - b1[1]
    
    denom = (-s2_x * s1_y + s1_x * s2_y)
    
    if abs(denom) < 1e-10:
        return None  # Lines are parallel
    
    s = (-s1_y * (a1[0] - b1[0]) + s1_x * (a1[1] - b1[1])) / denom
    t = (s2_x * (a1[1] - b1[1]) - s2_y * (a1[0] - b1[0])) / denom
    
    if 0 <= s <= 1 and 0 <= t <= 1:
        return (
            a1[0] + (t * s1_x),
            a1[1] + (t * s1_y)
        )
    
    return None


def get_rect_center(rect: Tuple[float, float, float, float]) -> Tuple[float, float]:
    """Get center of rectangle"""
    return (rect[0] + rect[2] / 2, rect[1] + rect[3] / 2)


def get_rect_corners(rect: Tuple[float, float, float, float]) -> List[Tuple[float, float]]:
    """Get all four corners of rectangle"""
    x, y, w, h = rect
    return [
        (x, y),           # Top-left
        (x + w, y),       # Top-right
        (x + w, y + h),   # Bottom-right
        (x, y + h)        # Bottom-left
    ]


def polygon_contains_point(polygon: List[Tuple[float, float]], 
                           point: Tuple[float, float]) -> bool:
    """Check if point is inside polygon using ray casting"""
    x, y = point
    n = len(polygon)
    inside = False
    
    p1x, p1y = polygon[0]
    for i in range(n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    
    return inside


def convex_hull(points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """Calculate convex hull using Andrew's monotone chain algorithm"""
    if len(points) <= 1:
        return points
    
    # Sort points lexographically
    points = sorted(points)
    
    # Build lower hull
    lower = []
    for p in points:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    
    # Build upper hull
    upper = []
    for p in reversed(points):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    
    # Concatenate and remove duplicates
    return lower[:-1] + upper[:-1]


def cross(o: Tuple[float, float], a: Tuple[float, float], b: Tuple[float, float]) -> float:
    """Cross product for convex hull calculation"""
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


# Pygame-specific helpers

def create_surface(size: Tuple[int, int], alpha: int = 255) -> pygame.Surface:
    """Create a surface with per-pixel alpha"""
    if alpha < 255:
        return pygame.Surface(size, pygame.SRCALPHA)
    else:
        return pygame.Surface(size)


def draw_rect_alpha(surface: pygame.Surface, color: Tuple[int, int, int, int],
                    rect: Tuple[float, float, float, float]):
    """Draw rectangle with alpha channel"""
    s = pygame.Surface((int(rect[2]), int(rect[3])), pygame.SRCALPHA)
    s.fill(color)
    surface.blit(s, (int(rect[0]), int(rect[1])))


def draw_circle_alpha(surface: pygame.Surface, color: Tuple[int, int, int, int],
                      center: Tuple[float, float], radius: float):
    """Draw circle with alpha channel"""
    # Create a surface for the circle
    size = int(radius * 2) + 2
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(s, color, (size // 2, size // 2), int(radius))
    surface.blit(s, (int(center[0] - radius), int(center[1] - radius)))


def draw_line_alpha(surface: pygame.Surface, color: Tuple[int, int, int, int],
                    start: Tuple[float, float], end: Tuple[float, float],
                    width: int = 1):
    """Draw line with alpha channel"""
    # For simple alpha lines, we need to draw on a separate surface
    # This is a simplified version
    pygame.draw.line(surface, color, start, end, width)


def fade_surface(surface: pygame.Surface, alpha: int) -> pygame.Surface:
    """Fade a surface to given alpha"""
    faded = surface.copy()
    faded.set_alpha(alpha)
    return faded


def tint_surface(surface: pygame.Surface, color: Tuple[int, int, int]) -> pygame.Surface:
    """Tint a surface with a color"""
    tinted = surface.copy()
    tinted.fill(color, special_flags=pygame.BLEND_MULT)
    return tinted


def scale_surface(surface: pygame.Surface, scale: float) -> pygame.Surface:
    """Scale a surface by factor"""
    if scale == 1.0:
        return surface
    
    new_size = (int(surface.get_width() * scale), int(surface.get_height() * scale))
    return pygame.transform.scale(surface, new_size)


def rotate_surface(surface: pygame.Surface, angle: float) -> pygame.Surface:
    """Rotate a surface by angle (degrees)"""
    return pygame.transform.rotate(surface, angle)


def get_surface_center(surface: pygame.Surface) -> Tuple[float, float]:
    """Get center of surface"""
    return (surface.get_width() / 2, surface.get_height() / 2)


# Timing helpers

def get_time_ms() -> float:
    """Get current time in milliseconds"""
    return pygame.time.get_ticks()


def get_time_sec() -> float:
    """Get current time in seconds"""
    return pygame.time.get_ticks() / 1000.0


def timer_reset() -> float:
    """Reset and return timer"""
    return get_time_ms()


def timer_elapsed(start_time: float) -> float:
    """Get elapsed time since start_time (ms)"""
    return get_time_ms() - start_time


def cooldown_ready(last_time: float, cooldown: float) -> bool:
    """Check if cooldown has expired"""
    return timer_elapsed(last_time) >= cooldown


# Random helpers

def random_choice_weighted(items: List[Any], weights: List[float]) -> Any:
    """Random choice with weights"""
    total = sum(weights)
    r = random.uniform(0, total)
    cumulative = 0
    for item, weight in zip(items, weights):
        cumulative += weight
        if r <= cumulative:
            return item
    return items[-1]


def random_sign() -> int:
    """Return random sign (-1 or 1)"""
    return 1 if random.random() >= 0.5 else -1


def random_bool(probability: float = 0.5) -> bool:
    """Return random boolean with given probability"""
    return random.random() < probability


def weighted_random(weights: Dict[Any, float]) -> Any:
    """Select random item based on weights"""
    items = list(weights.keys())
    weight_values = list(weights.values())
    return random_choice_weighted(items, weight_values)


# String helpers

def format_time(seconds: float) -> str:
    """Format seconds to MM:SS"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def format_number(num: float, precision: int = 0) -> str:
    """Format number with comma separators"""
    if precision > 0:
        return f"{num:,.{precision}f}"
    else:
        return f"{num:,.0f}"


def truncate_text(text: str, max_length: int) -> str:
    """Truncate text with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


# File helpers

def ensure_directory(path: str):
    """Ensure directory exists"""
    import os
    os.makedirs(path, exist_ok=True)


def file_exists(path: str) -> bool:
    """Check if file exists"""
    import os
    return os.path.exists(path)


def read_text_file(path: str) -> str:
    """Read text file"""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def write_text_file(path: str, content: str):
    """Write text file"""
    ensure_directory(path.rsplit('/', 1)[0] if '/' in path else '.')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
