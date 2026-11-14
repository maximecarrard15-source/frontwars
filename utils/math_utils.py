"""
Advanced mathematics utilities for Frontwars
"""

import math
import random
from typing import List, Tuple, Optional
import numpy as np


def gaussian(x: float, mean: float = 0.0, std_dev: float = 1.0) -> float:
    """Gaussian function"""
    return math.exp(-((x - mean) ** 2) / (2 * std_dev ** 2)) / (std_dev * math.sqrt(2 * math.pi))


def sigmoid(x: float, steepness: float = 1.0, midpoint: float = 0.0) -> float:
    """Sigmoid function"""
    return 1.0 / (1.0 + math.exp(-steepness * (x - midpoint)))


def smooth_pulse(x: float, center: float = 0.5, width: float = 0.1) -> float:
    """Smooth pulse function (0 to 1)"""
    t = abs(x - center) / width
    if t > 1:
        return 0.0
    return math.exp(1.0 - 1.0 / (1.0 - t**2)) if t < 1 else 0.0


def noise_1d(x: float, seed: int = 0) -> float:
    """Simple 1D noise function"""
    # Simple hash-based noise
    x = x * 1000 + seed
    x = (x << 13) ^ x
    return (1.0 - ((x * (x * x * 15731 + 789221) + 1376312589) & 0x7fffffff) / 1073741824.0)


def noise_2d(x: float, y: float, seed: int = 0) -> float:
    """Simple 2D noise function"""
    # Combine x and y with seed
    n = x + y * 57 + seed * 131
    n = (n << 13) ^ n
    return (1.0 - ((n * (n * n * 15731 + 789221) + 1376312589) & 0x7fffffff) / 1073741824.0)


def perlin_noise_2d(x: float, y: float, seed: int = 0, 
                    octaves: int = 4, persistence: float = 0.5) -> float:
    """2D Perlin noise"""
    total = 0.0
    frequency = 1.0
    amplitude = 1.0
    max_value = 0.0
    
    for _ in range(octaves):
        total += gradient_noise_2d(x * frequency, y * frequency, seed) * amplitude
        max_value += amplitude
        amplitude *= persistence
        frequency *= 2.0
    
    return total / max_value


def gradient_noise_2d(x: float, y: float, seed: int = 0) -> float:
    """2D gradient noise"""
    # Get grid cell coordinates
    x0 = int(x)
    y0 = int(y)
    x1 = x0 + 1
    y1 = y0 + 1
    
    # Get fractional part
    sx = x - x0
    sy = y - y0
    
    # Generate random gradients
    random.seed(seed)
    gradients = {}
    for i in range(-1, 2):
        for j in range(-1, 2):
            random.seed(seed + x0 + i + (y0 + j) * 1000)
            gradients[(x0 + i, y0 + j)] = (random.random() * 2 - 1, random.random() * 2 - 1)
    
    # Normalize fractional coordinates
    n0 = gradient_noise_2d_helper(x0, y0, sx, sy, gradients)
    n1 = gradient_noise_2d_helper(x1, y0, sx - 1, sy, gradients)
    ix0 = lerp(n0, n1, sx)
    
    n0 = gradient_noise_2d_helper(x0, y1, sx, sy - 1, gradients)
    n1 = gradient_noise_2d_helper(x1, y1, sx - 1, sy - 1, gradients)
    ix1 = lerp(n0, n1, sx)
    
    return lerp(ix0, ix1, sy)


def gradient_noise_2d_helper(x: int, y: int, sx: float, sy: float, 
                             gradients: dict) -> float:
    """Helper for gradient noise"""
    # Get gradient vector
    gx, gy = gradients.get((x, y), (0, 0))
    
    # Compute dot product
    return gx * sx + gy * sy


def simplex_noise_2d(x: float, y: float, seed: int = 0) -> float:
    """2D Simplex noise (simplified)"""
    # This is a simplified version
    return perlin_noise_2d(x, y, seed)


def fractal_noise_2d(x: float, y: float, seed: int = 0,
                     octaves: int = 4, frequency: float = 1.0,
                     persistence: float = 0.5, lacunarity: float = 2.0) -> float:
    """Fractal noise (fBm)"""
    total = 0.0
    amplitude = 1.0
    max_value = 0.0
    
    for _ in range(octaves):
        total += perlin_noise_2d(x * frequency, y * frequency, seed) * amplitude
        max_value += amplitude
        amplitude *= persistence
        frequency *= lacunarity
    
    return total / max_value


def cellular_noise_2d(x: float, y: float, seed: int = 0,
                      num_points: int = 100, radius: float = 1.0) -> float:
    """2D Cellular/Worley noise"""
    # Generate random points
    random.seed(seed)
    points = []
    for _ in range(num_points):
        angle = random.random() * 2 * math.pi
        dist = random.random() * radius
        points.append((math.cos(angle) * dist, math.sin(angle) * dist))
    
    # Find distance to closest point
    min_dist = float('inf')
    for px, py in points:
        dx = x - px
        dy = y - py
        dist = dx**2 + dy**2
        if dist < min_dist:
            min_dist = dist
    
    return math.sqrt(min_dist) / radius


def value_noise_2d(x: float, y: float, seed: int = 0) -> float:
    """2D Value noise"""
    x0 = int(x)
    y0 = int(y)
    x1 = x0 + 1
    y1 = y0 + 1
    
    sx = x - x0
    sy = y - y0
    
    # Generate random values
    random.seed(seed)
    values = {}
    for i in range(x0 - 1, x1 + 2):
        for j in range(y0 - 1, y1 + 2):
            random.seed(seed + i + j * 1000)
            values[(i, j)] = random.random()
    
    # Interpolate
    n0 = values.get((x0, y0), 0)
    n1 = values.get((x1, y0), 0)
    ix0 = lerp(n0, n1, sx)
    
    n0 = values.get((x0, y1), 0)
    n1 = values.get((x1, y1), 0)
    ix1 = lerp(n0, n1, sx)
    
    return lerp(ix0, ix1, sy)


# Statistical functions

def mean(values: List[float]) -> float:
    """Calculate mean"""
    return sum(values) / len(values) if values else 0.0


def median(values: List[float]) -> float:
    """Calculate median"""
    if not values:
        return 0.0
    sorted_values = sorted(values)
    n = len(sorted_values)
    if n % 2 == 1:
        return sorted_values[n // 2]
    else:
        return (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2.0


def standard_deviation(values: List[float], sample: bool = True) -> float:
    """Calculate standard deviation"""
    if len(values) < 2:
        return 0.0
    
    m = mean(values)
    variance = sum((x - m) ** 2 for x in values) / (len(values) - (1 if sample else 0))
    return math.sqrt(variance)


def normalize_values(values: List[float]) -> List[float]:
    """Normalize values to [0, 1] range"""
    if not values:
        return []
    
    min_val = min(values)
    max_val = max(values)
    
    if min_val == max_val:
        return [0.5 for _ in values]
    
    return [(v - min_val) / (max_val - min_val) for v in values]


def standardize_values(values: List[float]) -> List[float]:
    """Standardize values (z-score normalization)"""
    if not values:
        return []
    
    m = mean(values)
    std = standard_deviation(values, sample=False)
    
    if std == 0:
        return [0.0 for _ in values]
    
    return [(v - m) / std for v in values]


# Geometric functions

def point_line_distance(point: Tuple[float, float],
                        line_start: Tuple[float, float],
                        line_end: Tuple[float, float]) -> float:
    """Calculate distance from point to line segment"""
    x0, y0 = point
    x1, y1 = line_start
    x2, y2 = line_end
    
    # Vector from line_start to line_end
    dx = x2 - x1
    dy = y2 - y1
    
    # If line is a point, return distance to that point
    if dx == 0 and dy == 0:
        return math.sqrt((x0 - x1)**2 + (y0 - y1)**2)
    
    # Calculate projection
    t = ((x0 - x1) * dx + (y0 - y1) * dy) / (dx**2 + dy**2)
    
    # Clamp t to [0, 1]
    t = max(0, min(1, t))
    
    # Projection point
    px = x1 + t * dx
    py = y1 + t * dy
    
    # Distance from point to projection
    return math.sqrt((x0 - px)**2 + (y0 - py)**2)


def point_in_polygon(point: Tuple[float, float],
                     polygon: List[Tuple[float, float]]) -> bool:
    """Check if point is inside polygon (ray casting)"""
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


def polygon_area(polygon: List[Tuple[float, float]]) -> float:
    """Calculate area of polygon (shoelace formula)"""
    n = len(polygon)
    area = 0.0
    
    for i in range(n):
        j = (i + 1) % n
        area += polygon[i][0] * polygon[j][1]
        area -= polygon[j][0] * polygon[i][1]
    
    return abs(area) / 2.0


def polygon_centroid(polygon: List[Tuple[float, float]]) -> Tuple[float, float]:
    """Calculate centroid of polygon"""
    n = len(polygon)
    cx, cy = 0.0, 0.0
    
    for i in range(n):
        j = (i + 1) % n
        factor = (polygon[i][0] * polygon[j][1]) - (polygon[j][0] * polygon[i][1])
        cx += (polygon[i][0] + polygon[j][0]) * factor
        cy += (polygon[i][1] + polygon[j][1]) * factor
    
    area = polygon_area(polygon)
    if area == 0:
        return (0, 0)
    
    factor = 1.0 / (6.0 * area)
    return (cx * factor, cy * factor)


# Matrix operations

def matrix_multiply(a: List[List[float]], b: List[List[float]]) -> List[List[float]]:
    """Multiply two matrices"""
    result = [[0.0 for _ in range(len(b[0]))] for _ in range(len(a))]
    
    for i in range(len(a)):
        for j in range(len(b[0])):
            for k in range(len(b)):
                result[i][j] += a[i][k] * b[k][j]
    
    return result


def matrix_rotate_2d(angle: float) -> List[List[float]]:
    """Create 2D rotation matrix"""
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    return [
        [cos_a, -sin_a],
        [sin_a, cos_a]
    ]


def matrix_scale_2d(sx: float, sy: float) -> List[List[float]]:
    """Create 2D scale matrix"""
    return [
        [sx, 0],
        [0, sy]
    ]


def matrix_translate_2d(tx: float, ty: float) -> List[List[float]]:
    """Create 2D translation matrix"""
    return [
        [1, 0, tx],
        [0, 1, ty],
        [0, 0, 1]
    ]


def transform_point_2d(point: Tuple[float, float],
                       matrix: List[List[float]]) -> Tuple[float, float]:
    """Transform point by 2D matrix"""
    x, y = point
    new_x = matrix[0][0] * x + matrix[0][1] * y + matrix[0][2]
    new_y = matrix[1][0] * x + matrix[1][1] * y + matrix[1][2]
    return (new_x, new_y)


# Spline functions

def linear_interpolation(t: float, p0: float, p1: float) -> float:
    """Linear interpolation"""
    return p0 + t * (p1 - p0)


def quadratic_interpolation(t: float, p0: float, p1: float, p2: float) -> float:
    """Quadratic interpolation"""
    return p1 + 0.5 * t * (p2 - p0 + t * (2 * p0 - 5 * p1 + 4 * p2 - p0 + t * (3 * (p1 - p2) + p0 - p1)))


def cubic_interpolation(t: float, p0: float, p1: float, p2: float, p3: float) -> float:
    """Cubic interpolation"""
    return p1 + 0.5 * t * (p2 - p0 + t * (2 * p0 - 5 * p1 + 4 * p2 - p3 + t * (3 * (p1 - p2) + p3 - p0)))


def catmull_rom_interpolation(t: float, p0: float, p1: float, p2: float, p3: float) -> float:
    """Catmull-Rom spline interpolation"""
    t2 = t * t
    t3 = t2 * t
    return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)


def bezier_cubic(t: float, p0: Tuple[float, float], p1: Tuple[float, float],
                 p2: Tuple[float, float], p3: Tuple[float, float]) -> Tuple[float, float]:
    """Cubic Bezier curve"""
    mt = 1 - t
    t2 = t * t
    t3 = t2 * t
    mt2 = mt * mt
    mt3 = mt2 * mt
    
    x = mt3 * p0[0] + 3 * mt2 * t * p1[0] + 3 * mt * t2 * p2[0] + t3 * p3[0]
    y = mt3 * p0[1] + 3 * mt2 * t * p1[1] + 3 * mt * t2 * p2[1] + t3 * p3[1]
    
    return (x, y)


def bezier_quadratic(t: float, p0: Tuple[float, float], p1: Tuple[float, float],
                    p2: Tuple[float, float]) -> Tuple[float, float]:
    """Quadratic Bezier curve"""
    mt = 1 - t
    t2 = t * t
    mt2 = mt * mt
    
    x = mt2 * p0[0] + 2 * mt * t * p1[0] + t2 * p2[0]
    y = mt2 * p0[1] + 2 * mt * t * p1[1] + t2 * p2[1]
    
    return (x, y)


# Easing functions

def ease_linear(t: float) -> float:
    """Linear easing"""
    return t


def ease_in_quad(t: float) -> float:
    """Quadratic ease in"""
    return t * t


def ease_out_quad(t: float) -> float:
    """Quadratic ease out"""
    return t * (2 - t)


def ease_in_out_quad(t: float) -> float:
    """Quadratic ease in out"""
    if t < 0.5:
        return 2 * t * t
    return -1 + (4 - 2 * t) * t


def ease_in_cubic(t: float) -> float:
    """Cubic ease in"""
    return t * t * t


def ease_out_cubic(t: float) -> float:
    """Cubic ease out"""
    t -= 1
    return 1 + t * t * t


def ease_in_out_cubic(t: float) -> float:
    """Cubic ease in out"""
    if t < 0.5:
        return 4 * t * t * t
    t -= 1
    return 1 + t * t * t * 4


def ease_in_quart(t: float) -> float:
    """Quartic ease in"""
    return t * t * t * t


def ease_out_quart(t: float) -> float:
    """Quartic ease out"""
    t -= 1
    return 1 - t * t * t * t


def ease_in_out_quart(t: float) -> float:
    """Quartic ease in out"""
    if t < 0.5:
        return 8 * t * t * t * t
    t -= 1
    return 1 - 8 * t * t * t * t


def ease_in_quint(t: float) -> float:
    """Quintic ease in"""
    return t * t * t * t * t


def ease_out_quint(t: float) -> float:
    """Quintic ease out"""
    t -= 1
    return 1 + t * t * t * t * t


def ease_in_out_quint(t: float) -> float:
    """Quintic ease in out"""
    if t < 0.5:
        return 16 * t * t * t * t * t
    t -= 1
    return 1 + 16 * t * t * t * t * t


def ease_in_sine(t: float) -> float:
    """Sine ease in"""
    return 1 - math.cos((t * math.pi) / 2)


def ease_out_sine(t: float) -> float:
    """Sine ease out"""
    return math.sin((t * math.pi) / 2)


def ease_in_out_sine(t: float) -> float:
    """Sine ease in out"""
    return -0.5 * (math.cos(t * math.pi) - 1)


def ease_in_expo(t: float) -> float:
    """Exponential ease in"""
    return 0 if t == 0 else 2 ** (10 * (t - 1))


def ease_out_expo(t: float) -> float:
    """Exponential ease out"""
    return 1 if t == 1 else 1 - 2 ** (-10 * t)


def ease_in_out_expo(t: float) -> float:
    """Exponential ease in out"""
    if t == 0:
        return 0
    if t == 1:
        return 1
    if t < 0.5:
        return 0.5 * 2 ** (20 * t - 10)
    return 1 - 0.5 * 2 ** (-20 * t + 10)


def ease_in_circ(t: float) -> float:
    """Circular ease in"""
    return 1 - math.sqrt(1 - t * t)


def ease_out_circ(t: float) -> float:
    """Circular ease out"""
    t -= 1
    return math.sqrt(1 - t * t)


def ease_in_out_circ(t: float) -> float:
    """Circular ease in out"""
    if t < 0.5:
        return (1 - math.sqrt(1 - 4 * t * t)) / 2
    t -= 1
    return (math.sqrt(1 - 4 * t * t) + 1) / 2


def ease_in_elastic(t: float, amplitude: float = 1.0, period: float = 0.5) -> float:
    """Elastic ease in"""
    if t == 0:
        return 0
    if t == 1:
        return 1
    
    if period == 0:
        period = 0.3
    
    s = period / 4
    t -= 1
    
    return -amplitude * math.pow(2, 10 * t) * math.sin((t - s) * (2 * math.pi) / period)


def ease_out_elastic(t: float, amplitude: float = 1.0, period: float = 0.5) -> float:
    """Elastic ease out"""
    if t == 0:
        return 0
    if t == 1:
        return 1
    
    if period == 0:
        period = 0.3
    
    s = period / 4
    
    return 1 + amplitude * math.pow(2, -10 * t) * math.sin((t - s) * (2 * math.pi) / period)


def ease_in_out_elastic(t: float, amplitude: float = 1.0, period: float = 0.5) -> float:
    """Elastic ease in out"""
    if t == 0:
        return 0
    if t == 1:
        return 1
    
    if period == 0:
        period = 0.3
    
    s = period / 4
    t -= 1
    
    if t < 0:
        return -0.5 * amplitude * math.pow(2, 10 * t) * math.sin((t - s) * (2 * math.pi) / period)
    
    return 1 - 0.5 * amplitude * math.pow(2, -10 * t) * math.sin((t - s) * (2 * math.pi) / period)


def ease_in_back(t: float, overshoot: float = 1.70158) -> float:
    """Back ease in"""
    return t * t * ((overshoot + 1) * t - overshoot)


def ease_out_back(t: float, overshoot: float = 1.70158) -> float:
    """Back ease out"""
    t -= 1
    return 1 + t * t * ((overshoot + 1) * t + overshoot)


def ease_in_out_back(t: float, overshoot: float = 1.70158) -> float:
    """Back ease in out"""
    if t < 0.5:
        return 0.5 * t * t * ((overshoot * 2 + 2) * t - overshoot * 2)
    t -= 1
    return 0.5 * (1 + t * t * ((overshoot * 2 + 2) * t + overshoot * 2))


def ease_out_bounce(t: float) -> float:
    """Bounce ease out"""
    if t < 1 / 2.75:
        return 7.5625 * t * t
    elif t < 2 / 2.75:
        t -= 1.5 / 2.75
        return 7.5625 * t * t + 0.75
    elif t < 2.5 / 2.75:
        t -= 2.25 / 2.75
        return 7.5625 * t * t + 0.9375
    else:
        t -= 2.625 / 2.75
        return 7.5625 * t * t + 0.984375


def ease_in_bounce(t: float) -> float:
    """Bounce ease in"""
    return 1 - ease_out_bounce(1 - t)


def ease_in_out_bounce(t: float) -> float:
    """Bounce ease in out"""
    if t < 0.5:
        return (1 - ease_out_bounce(1 - 2 * t)) / 2
    return (1 + ease_out_bounce(2 * t - 1)) / 2
