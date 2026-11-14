#!/usr/bin/env python3
"""
Frontwars - A high-quality real-time strategy game in Python

This is the main entry point for the Frontwars game.
Run this file to start the game.

Usage:
    python main.py

Features:
    - Real-time strategy gameplay
    - Multiple unit types and buildings
    - Team-based multiplayer (AI vs Human)
    - Procedural map generation
    - Pathfinding and unit movement
    - Combat system with damage calculations
    - Camera controls (pan, zoom, rotate)
    - Minimap
    - HUD with game information
    - Menus and UI
"""

import sys
import os
import pygame

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import game modules
from game.game_loop import GameLoop, run_game
from config import GAME_NAME, GAME_VERSION
from utils.logger import logger


def main():
    """Main function to run Frontwars"""
    print(f"Starting {GAME_NAME} v{GAME_VERSION}")
    print("=" * 50)
    
    try:
        # Run the game
        run_game()
    except KeyboardInterrupt:
        print("\nGame interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", "system")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
