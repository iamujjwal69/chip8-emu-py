# Enhanced Chip-8 Emulator in Python + Pygame

A premium, cycle-accurate Chip-8 interpreter written in Python using Pygame. Features a retro-futuristic dark mode visual dashboard, active keypad visualization, save/load state functionality, and an interactive CLI debugger.

## Features

- **Cycle-Accurate Timing**: Models instruction execution cycles closely and handles 60 Hz timers using delta timing.
- **Modern Dashboard UI**: Rendered in a high-contrast Neon Cyan design with live status lights, PC/I register counters, and an interactive keyboard map.
- **Keypad Matrix Visualization**: Renders a 4x4 keypad grid dynamically, lighting up keys in real-time as you press them on your keyboard.
- **Save/Load State**: Fast binary state serialization powered by Python's `pickle`.
- **Asynchronous CLI Debugger**: A full command-line debugger running on a background thread. Step instructions, set breakpoints, read registers, and inspect memory without freezing the GUI.

---

## Keyboard Keypad Mapping

Standard Chip-8 keypads are arranged in a 4x4 hexadecimal grid. The mapping on a standard QWERTY keyboard is as follows:

| QWERTY Key | Chip-8 Key | Description |
|---|---|---|
| `1` `2` `3` `4` | `1` `2` `3` `C` | Top Row |
| `Q` `W` `E` `R` | `4` `5` `6` `D` | Mid-Upper Row |
| `A` `S` `D` `F` | `7` `8` `9` `E` | Mid-Lower Row |
| `Z` `X` `C` `V` | `A` `0` `B` `F` | Bottom Row |

---

## Emulator Hotkeys

- **`F5`**: Quick Save State (saved to `quicksave.ch8state`).
- **`F6`**: Quick Load State.
- **`F10`**: Single Step Instruction (while Debugger is active).
- **`F12`**: Toggle CLI Debugger in console.

---

## CLI Debugger Commands

When the CLI debugger is toggled on (`F12`), the emulator pauses execution and prompts for commands in the console (`dbg> `).

| Command | Shortcut | Description |
|---|---|---|
| `help` | `h` | List all available debugger commands |
| `step` | `s` | Execute exactly one instruction cycle |
| `continue` | `c` | Resume normal execution (closes debugger) |
| `break <addr>` | `b <addr>` | Set a breakpoint at a hex address (e.g. `b 20a` or `break 0x208`) |
| `delbreak <addr>`| `d <addr>` | Delete breakpoint at specified hex address |
| `breakpoints` | `bl` | List all active breakpoints |
| `regs` | `r` | Print values of PC, I, SP, DT, ST and all registers V0-VF |
| `stack` | | Inspect stack trace and stack pointer index |
| `mem <addr> [len]`| `m <addr>` | Inspect hex values in memory starting at `<addr>` (default length 16) |
| `quit` | `q` | Terminate the emulator |

---

## Prerequisites & Installation

1. Ensure **Python 3.8+** is installed on your system.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Emulator

Run the emulator with the default IBM Logo test ROM:
```bash
python main.py
```

To load a custom ROM:
```bash
python main.py path/to/your_rom.ch8
```
