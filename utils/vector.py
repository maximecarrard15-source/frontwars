"""
Vector mathematics for Frontwars
"""

import math
from typing import Union, Tuple, List
from dataclasses import dataclass
import numpy as np


@dataclass
class Vector2:
    """2D vector for game positions and movements"""
    x: float = 0.0
    y: float = 0.0
    
    def __add__(self, other: Union['Vector2', Tuple[float, float]]) -> 'Vector2':
        if isinstance(other, Vector2):
            return Vector2(self.x + other.x, self.y + other.y)
        else:
            return Vector2(self.x + other[0], self.y + other[1])
    
    def __sub__(self, other: Union['Vector2', Tuple[float, float]]) -> 'Vector2':
        if isinstance(other, Vector2):
            return Vector2(self.x - other.x, self.y - other.y)
        else:
            return Vector2(self.x - other[0], self.y - other[1])
    
    def __mul__(self, scalar: float) -> 'Vector2':
        return Vector2(self.x * scalar, self.y * scalar)
    
    def __truediv__(self, scalar: float) -> 'Vector2':
        return Vector2(self.x / scalar, self.y / scalar)
    
    def __neg__(self) -> 'Vector2':
        return Vector2(-self.x, -self.y)
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, Vector2):
            return abs(self.x - other.x) < 1e-6 and abs(self.y - other.y) < 1e-6
        return False
    
    def __hash__(self) -> int:
        return hash((round(self.x, 6), round(self.y, 6)))
    
    def __repr__(self) -> str:
        return f"Vector2({self.x:.2f}, {self.y:.2f})"
    
    def __len__(self) -> float:
        return self.length()
    
    def __getitem__(self, index: int) -> float:
        if index == 0:
            return self.x
        elif index == 1:
            return self.y
        else:
            raise IndexError("Vector2 index out of range")
    
    def __setitem__(self, index: int, value: float):
        if index == 0:
            self.x = value
        elif index == 1:
            self.y = value
        else:
            raise IndexError("Vector2 index out of range")
    
    @classmethod
    def from_tuple(cls, coords: Tuple[float, float]) -> 'Vector2':
        """Create Vector2 from tuple"""
        return cls(coords[0], coords[1])
    
    @classmethod
    def from_list(cls, coords: List[float]) -> 'Vector2':
        """Create Vector2 from list"""
        return cls(coords[0], coords[1])
    
    @classmethod
    def zero(cls) -> 'Vector2':
        """Return zero vector"""
        return cls(0.0, 0.0)
    
    @classmethod
    def one(cls) -> 'Vector2':
        """Return one vector"""
        return cls(1.0, 1.0)
    
    @classmethod
    def up(cls) -> 'Vector2':
        """Return up vector"""
        return cls(0.0, -1.0)
    
    @classmethod
    def down(cls) -> 'Vector2':
        """Return down vector"""
        return cls(0.0, 1.0)
    
    @classmethod
    def left(cls) -> 'Vector2':
        """Return left vector"""
        return cls(-1.0, 0.0)
    
    @classmethod
    def right(cls) -> 'Vector2':
        """Return right vector"""
        return cls(1.0, 0.0)
    
    def to_tuple(self) -> Tuple[float, float]:
        """Convert to tuple"""
        return (self.x, self.y)
    
    def to_list(self) -> List[float]:
        """Convert to list"""
        return [self.x, self.y]
    
    def to_int(self) -> Tuple[int, int]:
        """Convert to integer tuple"""
        return (int(self.x), int(self.y))
    
    def length(self) -> float:
        """Calculate vector length (magnitude)"""
        return math.sqrt(self.x**2 + self.y**2)
    
    def length_squared(self) -> float:
        """Calculate squared length (faster, no sqrt)"""
        return self.x**2 + self.y**2
    
    def normalize(self) -> 'Vector2':
        """Normalize vector to unit length"""
        length = self.length()
        if length > 0:
            return Vector2(self.x / length, self.y / length)
        return Vector2(0.0, 0.0)
    
    def normalized(self) -> 'Vector2':
        """Return normalized copy"""
        return self.normalize()
    
    def scale(self, scalar: float) -> 'Vector2':
        """Scale vector by scalar"""
        return self * scalar
    
    def distance_to(self, other: 'Vector2') -> float:
        """Calculate distance to another vector"""
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
    
    def distance_squared_to(self, other: 'Vector2') -> float:
        """Calculate squared distance to another vector"""
        return (self.x - other.x)**2 + (self.y - other.y)**2
    
    def dot(self, other: 'Vector2') -> float:
        """Calculate dot product"""
        return self.x * other.x + self.y * other.y
    
    def cross(self, other: 'Vector2') -> float:
        """Calculate cross product (2D result is scalar)"""
        return self.x * other.y - self.y * other.x
    
    def angle(self) -> float:
        """Get angle in radians"""
        return math.atan2(self.y, self.x)
    
    def angle_degrees(self) -> float:
        """Get angle in degrees"""
        return math.degrees(self.angle())
    
    def rotate(self, angle: float) -> 'Vector2':
        """Rotate vector by angle (radians)"""
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        return Vector2(
            self.x * cos_a - self.y * sin_a,
            self.x * sin_a + self.y * cos_a
        )
    
    def rotate_degrees(self, angle: float) -> 'Vector2':
        """Rotate vector by angle (degrees)"""
        return self.rotate(math.radians(angle))
    
    def lerp(self, other: 'Vector2', t: float) -> 'Vector2':
        """Linear interpolation to another vector"""
        return Vector2(
            self.x + (other.x - self.x) * t,
            self.y + (other.y - self.y) * t
        )
    
    def clamp(self, min_val: float, max_val: float) -> 'Vector2':
        """Clamp vector components"""
        return Vector2(
            max(min_val, min(max_val, self.x)),
            max(min_val, min(max_val, self.y))
        )
    
    def copy(self) -> 'Vector2':
        """Return a copy"""
        return Vector2(self.x, self.y)
    
    def is_zero(self, epsilon: float = 1e-6) -> bool:
        """Check if vector is approximately zero"""
        return self.length_squared() < epsilon**2
    
    def to_numpy(self) -> np.ndarray:
        """Convert to numpy array"""
        return np.array([self.x, self.y])
    
    @staticmethod
    def from_numpy(array: np.ndarray) -> 'Vector2':
        """Create from numpy array"""
        return Vector2(array[0], array[1])


@dataclass
class Vector3:
    """3D vector for advanced game features"""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    
    def __add__(self, other: Union['Vector3', Tuple[float, float, float]]) -> 'Vector3':
        if isinstance(other, Vector3):
            return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)
        else:
            return Vector3(self.x + other[0], self.y + other[1], self.z + other[2])
    
    def __sub__(self, other: Union['Vector3', Tuple[float, float, float]]) -> 'Vector3':
        if isinstance(other, Vector3):
            return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)
        else:
            return Vector3(self.x - other[0], self.y - other[1], self.z - other[2])
    
    def __mul__(self, scalar: float) -> 'Vector3':
        return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)
    
    def __truediv__(self, scalar: float) -> 'Vector3':
        return Vector3(self.x / scalar, self.y / scalar, self.z / scalar)
    
    def __neg__(self) -> 'Vector3':
        return Vector3(-self.x, -self.y, -self.z)
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, Vector3):
            return (abs(self.x - other.x) < 1e-6 and 
                    abs(self.y - other.y) < 1e-6 and 
                    abs(self.z - other.z) < 1e-6)
        return False
    
    def __repr__(self) -> str:
        return f"Vector3({self.x:.2f}, {self.y:.2f}, {self.z:.2f})"
    
    def to_tuple(self) -> Tuple[float, float, float]:
        return (self.x, self.y, self.z)
    
    def length(self) -> float:
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)
    
    def normalize(self) -> 'Vector3':
        length = self.length()
        if length > 0:
            return Vector3(self.x / length, self.y / length, self.z / length)
        return Vector3(0.0, 0.0, 0.0)
    
    def dot(self, other: 'Vector3') -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z
    
    def cross(self, other: 'Vector3') -> 'Vector3':
        return Vector3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x
        )
    
    def to_vector2(self) -> Vector2:
        """Convert to 2D vector (ignore z)"""
        return Vector2(self.x, self.y)
    
    def copy(self) -> 'Vector3':
        return Vector3(self.x, self.y, self.z)


# Utility functions
def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value between min and max"""
    return max(min_val, min(max_val, value))


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation"""
    return a + (b - a) * t


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


def normalize(x: float, y: float) -> Tuple[float, float]:
    """Normalize coordinates"""
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
    
    # Translate point to origin
    px = point[0] - center[0]
    py = point[1] - center[1]
    
    # Rotate
    new_x = px * cos_a - py * sin_a
    new_y = px * sin_a + py * cos_a
    
    # Translate back
    return (new_x + center[0], new_y + center[1])


def point_in_rect(point: Tuple[float, float], 
                  rect: Tuple[float, float, float, float]) -> bool:
    """Check if point is inside rectangle (x, y, width, height)"""
    x, y = point
    rx, ry, rw, rh = rect
    return rx <= x <= rx + rw and ry <= y <= ry + rh


def rects_overlap(rect1: Tuple[float, float, float, float],
                  rect2: Tuple[float, float, float, float]) -> bool:
    """Check if two rectangles overlap"""
    r1x, r1y, r1w, r1h = rect1
    r2x, r2y, r2w, r2h = rect2
    
    return not (r1x + r1w < r2x or r2x + r2w < r1x or
                r1y + r1h < r2y or r2y + r2h < r1y)


def circle_contains_point(center: Tuple[float, float], 
                          radius: float,
                          point: Tuple[float, float]) -> bool:
    """Check if point is inside circle"""
    dx = point[0] - center[0]
    dy = point[1] - center[1]
    return dx**2 + dy**2 <= radius**2
