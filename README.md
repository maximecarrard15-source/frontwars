# Frontwars

![Frontwars Logo](https://img.icons8.com/ios-filled/50/000000/war.png) **Frontwars** - A High-Quality Real-Time Strategy Game in Python

## 📖 Description

Frontwars is a comprehensive real-time strategy (RTS) game built entirely in Python using Pygame. It features:

- **Real-time strategy gameplay** with unit control and base building
- **Procedural map generation** with various terrain types
- **Multiple unit types** (soldiers, tanks, scouts, artillery, etc.)
- **Building system** with production queues and resource management
- **Advanced pathfinding** using A* algorithm
- **Team-based multiplayer** (Human vs AI)
- **Camera controls** (pan, zoom, rotate)
- **Minimap** for strategic overview
- **HUD** with comprehensive game information
- **Menus and UI** system
- **Combat system** with damage calculations and armor
- **Status effects** (stun, heal, etc.)
- **Projectile system** with various projectile types
- **Visual effects** (explosions, fire, smoke, etc.)

## 🎮 Features

### Gameplay
- Control units and command them to move, attack, and defend
- Build various structures to produce units and generate resources
- Capture territory and defeat enemy teams
- Manage economy with gold income and upkeep costs
- Experience system with unit leveling

### Units
- **Soldier**: Basic infantry unit
- **Tank**: Heavy armored vehicle
- **Scout**: Fast reconnaissance unit
- **Artillery**: Long-range siege unit
- **Engineer**: Construction and repair unit
- **Aircraft**: Aerial combat unit
- **Helicopter**: Versatile aerial unit

### Buildings
- **Base**: Main base building
- **Barracks**: Produces infantry units
- **Factory**: Produces vehicles
- **Tower**: Defensive structure
- **Farm**: Generates food resources
- **Mine**: Generates gold resources
- **Research Lab**: Enables research and upgrades

### Maps
- Procedurally generated maps with:
  - Grass, water, mountains, forests, sand, roads
  - Rivers and lakes
  - Elevation variations
  - Resource distribution
  - Starting positions for teams
  - Roads connecting bases
  - Cities and neutral territories

### AI
- AI-controlled teams with various difficulty levels
- Unit production and management
- Combat tactics and targeting
- Resource collection
- Base defense

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Install from source

1. Clone the repository:
```bash
git clone https://github.com/your-username/frontwars.git
cd frontwars
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the game:
```bash
python main.py
```

### Install using pip (if available)
```bash
pip install frontwars
frontwars
```

## 🎯 Controls

### Camera Controls
- **W/A/S/D**: Move camera
- **Q/E**: Rotate camera
- **Mouse Wheel**: Zoom in/out
- **Middle Mouse Button**: Drag to pan camera
- **+/-**: Zoom in/out

### Unit Controls
- **Left Click**: Select unit or issue move command
- **Right Click**: Move selected units
- **A**: Select all units
- **S**: Stop command
- **H**: Hold position
- **B**: Build mode
- **ESC**: Clear selection or cancel action

### Game Controls
- **ESC**: Pause game / Open menu
- **P**: Toggle pause
- **F**: Toggle fog of war
- **TAB**: Toggle minimap

## 🏗️ Project Structure

```
frontwars/
├── main.py                 # Main entry point
├── config.py               # Game configuration and constants
├── setup.py                # Setup script
├── requirements.txt        # Dependencies
├── README.md               # This file
├── game/                   # Game core modules
│   ├── __init__.py
│   ├── game_state.py       # Game state management
│   ├── game_loop.py        # Main game loop
│   ├── map.py              # Map system and generation
│   ├── camera.py           # Camera system
│   ├── team.py             # Team management
│   └── player.py           # Player system
├── entities/               # Game entities
│   ├── __init__.py
│   ├── unit.py             # Unit system
│   ├── building.py         # Building system
│   ├── projectile.py       # Projectile system
│   └── effect.py           # Effect system
├── utils/                  # Utility modules
│   ├── __init__.py
│   ├── vector.py           # Vector mathematics
│   ├── pathfinding.py      # Pathfinding algorithms
│   ├── helpers.py          # Helper functions
│   ├── math_utils.py       # Advanced mathematics
│   └── logger.py           # Logging system
└── ui/                     # User interface
    ├── __init__.py
    ├── ui_manager.py        # UI manager
    ├── hud.py               # Heads-up display
    ├── menu.py              # Menu system
    └── widgets.py           # UI widgets
```

## 🛠️ Development

### Running Tests
```bash
# Tests will be added in future versions
python -m pytest tests/
```

### Code Style
This project follows PEP 8 style guidelines. You can check your code with:
```bash
pip install flake8
flake8 frontwars/
```

### Contributing
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add some feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Pygame](https://www.pygame.org/) - The game library used
- [Noise](https://pypi.org/project/noise/) - For procedural generation
- [NumPy](https://numpy.org/) - For mathematical operations

## 📞 Contact

For questions or feedback, please open an issue on the GitHub repository.

---

**Enjoy playing Frontwars!** 🎮
