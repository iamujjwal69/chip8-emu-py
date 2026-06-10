# Enhanced Chip-8 Emulator & Visual Dashboard

A premium, cycle-accurate Chip-8 interpreter written in Python using Pygame. Features a retro-futuristic dark mode visual dashboard, active keypad matrix visualization, instant save/load states, and a multi-threaded asynchronous CLI debugger.

---

## Live Online Deployment & Local Performance

### 🌐 Play Online (WebAssembly)
The project is deployed and playable directly in your web browser:
👉 **[https://iamujjwal69.github.io/chip8-emu-py/](https://iamujjwal69.github.io/chip8-emu-py/)**

*Note: The web version is compiled using Pygbag to run Python inside WebAssembly. Due to browser virtualization overhead and WebGL translation, you may experience minor audio latency or lag in the browser.*

### 💻 Local Desktop Execution (Recommended / Optimized)
For the most **optimized, lag-free, and high-performance** experience with zero-latency audio and graphics, running it locally as a native desktop application is highly recommended.

---

## Features

- **Optimized Local Execution**: Low-level instructions execute natively in Python for a fluid 60 FPS experience.
- **Visual Dashboard**: Designed with a glowing cyber-cyan interface displaying realtime registers (PC and I) and program status indicators.
- **Keypad Matrix Tracking**: Renders a live 4x4 keypad grid on the dashboard, lighting up keys dynamically as they are pressed.
- **Binary State Serialization**: Press `F5` / `F6` to instantly serialize (save) and deserialize (load) the emulator's state utilizing Python's `pickle`.
- **Asynchronous CLI Debugger**: Toggle with `F12` to enter a threaded console command-line loop. Step cycles, inspect memory, list stack levels, and set execution breakpoints.
- **CI/CD Pipeline**: GitHub Actions automatically triggers on pushes to `main` to build WebAssembly assets using Pygbag and deploy to GitHub Pages.

---

## Game Controls (Tetris)

The default game loaded is **Tetris** (`roms/tetris.ch8`). Use the following keyboard mappings to control the game:

| Keyboard Key | Action |
|---|---|
| **`Q`** (Key 4) | Move Block Left |
| **`E`** (Key 6) | Move Block Right |
| **`W`** (Key 5) | Rotate Block |
| **`S`** (Key 8) | Fast Drop Block |

---

## Keyboard Keypad Mapping Matrix

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
| `break <addr>` | `b <addr>` | Set a breakpoint at a hex address (e.g. `b 200` or `break 0x228`) |
| `delbreak <addr>`| `d <addr>` | Delete breakpoint at specified hex address |
| `breakpoints` | `bl` | List all active breakpoints |
| `regs` | `r` | Print values of PC, I, SP, DT, ST and all registers V0-VF |
| `stack` | | Inspect stack trace and stack pointer index |
| `mem <addr> [len]`| `m <addr>` | Inspect hex values in memory starting at `<addr>` (default length 16) |
| `quit` | `q` | Terminate the emulator |

---

## Prerequisites & Installation (Local Server)

1. Ensure **Python 3.8+** is installed on your system.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Emulator Locally

To run the emulator with the default game (Tetris):
```bash
python main.py
```

To load a custom ROM (e.g. IBM Logo):
```bash
python main.py roms/ibm_logo.ch8
```

---

## How to List This on Your Resume

If you are showcasing this project on your portfolio or resume, here is a suggested layout:

### **Enhanced CHIP-8 Emulator & Interactive Debugger**
* **Technologies**: Python, Pygame, NumPy, WebAssembly (Pygbag), GitHub Actions, Git
* **Key Achievements**:
  * **Low-Level Hardware Simulation**: Simulated a CPU with 16 registers, call stack, program counters, 4KB RAM, and mapped all 35 machine opcodes.
  * **Asynchronous Multi-Threaded Debugging**: Programmed a multi-threaded, asynchronous CLI debugger on a background thread for live register inspection, breakpoint tracking, and non-blocking instruction stepping.
  * **State Serialization**: Created binary state serialization (quick save/load) utilizing `pickle` to capture and recover system memory states.
  * **CI/CD Build Pipeline**: Configured a CI/CD GitHub Actions workflow compiling the project to WebAssembly (WASM) to automatically deploy to GitHub Pages on commit pushes.
