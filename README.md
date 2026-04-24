# EC327 Project — Snake+ (Pygame)

Grid snake with health, items, enemies, and a sidebar HUD.

## Requirements

- Python **3.10+** (3.11 or 3.12 recommended)
- [Pygame 2.x](https://www.pygame.org/)

## How to run

From the project root:

```bash
# 1. Create a virtual environment (optional but recommended)
python3 -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the game
python main.py
```

Without a virtual environment:

```bash
pip install -r requirements.txt
python main.py
```

## Controls

| Input | Action |
|--------|--------|
| Arrow keys | Move |
| Enter | Start (from menu) |
| P | Pause (while playing) |
| R | Restart (game over) |
| Q | Quit |

High scores are stored in **`highscore.json`** in the project root.

## Core modules

- `main.py` — Entry point and game loop  
- `snake.py` — Player snake  
- `world.py` — Grid helpers  
- `items.py` — Food and pickups  
- `enemies.py` — Blockers and chaser  
- `renderer.py` — Drawing and HUD  
- `constants.py` — Tuning values  

## Branch

Snake lives on branch **`snake-game`**. After cloning, check out that branch:

```bash
git clone https://github.com/syuan534/EC327_Project.git
cd EC327_Project
git checkout snake-game
```
