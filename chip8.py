import numpy as np
import random
from typing import List, Dict, Callable

class Chip8:
    def __init__(self):
        # Memory (4096 bytes)
        self.memory = bytearray(4096)
        
        # Registers
        self.V: List[int] = [0] * 16      # V0..VF
        self.I: int = 0                  # Index register
        self.pc: int = 0x200              # Program counter (programs start at 0x200)
        
        # Stack
        self.stack: List[int] = [0] * 16
        self.sp: int = 0                  # Stack pointer
        
        # Timers
        self.delay_timer: int = 0
        self.sound_timer: int = 0
        
        # Display (64x32 grid, rows x cols)
        self.display = np.zeros((32, 64), dtype=bool)
        self.draw_flag: bool = False
        
        # Keyboard state (16 keys)
        self.keys: List[bool] = [False] * 16
        
        # Waiting for key press flag (for Fx0A)
        # Stores the register index (0-15) if waiting, else None
        self.waiting_for_key_reg = None
        
        # Cycle accuracy accumulator
        self.cycle_accumulator: int = 0
        self.should_exit: bool = False
        
        # Load fontset into memory (0x0000 - 0x01FF)
        self._load_fontset()
        
        # Setup instruction table
        self._build_opcode_table()
        
    def _load_fontset(self):
        fontset = [
            0xF0, 0x90, 0x90, 0x90, 0xF0,  # 0
            0x20, 0x60, 0x20, 0x20, 0x70,  # 1
            0xF0, 0x10, 0xF0, 0x80, 0xF0,  # 2
            0xF0, 0x10, 0xF0, 0x10, 0xF0,  # 3
            0x90, 0x90, 0xF0, 0x10, 0x10,  # 4
            0xF0, 0x80, 0xF0, 0x10, 0xF0,  # 5
            0xF0, 0x80, 0xF0, 0x90, 0xF0,  # 6
            0xF0, 0x10, 0x20, 0x40, 0x40,  # 7
            0xF0, 0x90, 0xF0, 0x90, 0xF0,  # 8
            0xF0, 0x90, 0xF0, 0x10, 0xF0,  # 9
            0xF0, 0x90, 0xF0, 0x90, 0x90,  # A
            0xE0, 0x90, 0xE0, 0x90, 0xE0,  # B
            0xF0, 0x80, 0x80, 0x80, 0xF0,  # C
            0xE0, 0x90, 0x90, 0x90, 0xE0,  # D
            0xF0, 0x80, 0xF0, 0x80, 0xF0,  # E
            0xF0, 0x80, 0xF0, 0x80, 0x80   # F
        ]
        # Load fontset at address 0x50 to keep 0x00 free
        self.fontset_offset = 0x50
        for i, byte in enumerate(fontset):
            self.memory[self.fontset_offset + i] = byte

    def load_rom(self, path: str):
        with open(path, 'rb') as f:
            data = f.read()
            # Chip-8 memory limit is 4096. Programs start at 0x200.
            max_size = 4096 - 0x200
            if len(data) > max_size:
                raise ValueError(f"ROM size ({len(data)} bytes) exceeds available memory ({max_size} bytes)")
            
            # Reset state
            self.memory[0x200:0x200+len(data)] = data
            self.pc = 0x200
            self.sp = 0
            self.stack = [0] * 16
            self.V = [0] * 16
            self.I = 0
            self.delay_timer = 0
            self.sound_timer = 0
            self.display.fill(False)
            self.draw_flag = True
            self.keys = [False] * 16
            self.waiting_for_key_reg = None
            self.cycle_accumulator = 0
            self.should_exit = False
            
    def cycle(self) -> int:
        """Fetch, decode, and execute one instruction. Returns cycles taken."""
        if self.waiting_for_key_reg is not None:
            # Check if any key is pressed
            for i, pressed in enumerate(self.keys):
                if pressed:
                    reg = self.waiting_for_key_reg
                    self.V[reg] = i
                    self.waiting_for_key_reg = None
                    break
            # While waiting for a key, the instruction execution is blocked.
            # Return nominal cycle count (e.g. 4)
            return 4
            
        if self.pc >= 4095:
            # Program counter out of bounds
            self.should_exit = True
            return 0
            
        opcode = (self.memory[self.pc] << 8) | self.memory[self.pc + 1]
        self.pc += 2
        
        cycles = self._execute(opcode)
        return cycles

    def _build_opcode_table(self):
        self.opcode_table: Dict[int, Callable[[int], int]] = {
            0x0: self._handle_0x0,
            0x1: self._op_1nnn,
            0x2: self._op_2nnn,
            0x3: self._op_3xkk,
            0x4: self._op_4xkk,
            0x5: self._op_5xy0,
            0x6: self._op_6xkk,
            0x7: self._op_7xkk,
            0x8: self._handle_0x8,
            0x9: self._op_9xy0,
            0xA: self._op_Annn,
            0xB: self._op_Bnnn,
            0xC: self._op_Cxkk,
            0xD: self._op_Dxyn,
            0xE: self._handle_0xE,
            0xF: self._handle_0xF,
        }

    def _execute(self, opcode: int) -> int:
        first = (opcode & 0xF000) >> 12
        handler = self.opcode_table.get(first, self._unknown_op)
        return handler(opcode)

    def _unknown_op(self, opcode: int) -> int:
        print(f"Unknown opcode: 0x{opcode:04X} at PC: 0x{self.pc - 2:03X}")
        return 4  # default cycle penalty

    # --- Group Handlers ---
    def _handle_0x0(self, opcode: int) -> int:
        last_byte = opcode & 0x00FF
        if last_byte == 0xE0:
            return self._op_00E0(opcode)
        elif last_byte == 0xEE:
            return self._op_00EE(opcode)
        else:
            return self._unknown_op(opcode)

    def _handle_0x8(self, opcode: int) -> int:
        last_nibble = opcode & 0x000F
        if last_nibble == 0x0:
            return self._op_8xy0(opcode)
        elif last_nibble == 0x1:
            return self._op_8xy1(opcode)
        elif last_nibble == 0x2:
            return self._op_8xy2(opcode)
        elif last_nibble == 0x3:
            return self._op_8xy3(opcode)
        elif last_nibble == 0x4:
            return self._op_8xy4(opcode)
        elif last_nibble == 0x5:
            return self._op_8xy5(opcode)
        elif last_nibble == 0x6:
            return self._op_8xy6(opcode)
        elif last_nibble == 0x7:
            return self._op_8xy7(opcode)
        elif last_nibble == 0xE:
            return self._op_8xyE(opcode)
        else:
            return self._unknown_op(opcode)

    def _handle_0xE(self, opcode: int) -> int:
        last_byte = opcode & 0x00FF
        if last_byte == 0x9E:
            return self._op_Ex9E(opcode)
        elif last_byte == 0xA1:
            return self._op_ExA1(opcode)
        else:
            return self._unknown_op(opcode)

    def _handle_0xF(self, opcode: int) -> int:
        last_byte = opcode & 0x00FF
        if last_byte == 0x07:
            return self._op_Fx07(opcode)
        elif last_byte == 0x0A:
            return self._op_Fx0A(opcode)
        elif last_byte == 0x15:
            return self._op_Fx15(opcode)
        elif last_byte == 0x18:
            return self._op_Fx18(opcode)
        elif last_byte == 0x1E:
            return self._op_Fx1E(opcode)
        elif last_byte == 0x29:
            return self._op_Fx29(opcode)
        elif last_byte == 0x33:
            return self._op_Fx33(opcode)
        elif last_byte == 0x55:
            return self._op_Fx55(opcode)
        elif last_byte == 0x65:
            return self._op_Fx65(opcode)
        else:
            return self._unknown_op(opcode)

    # --- Opcodes Implementation ---

    # 00E0 - CLS
    def _op_00E0(self, opcode: int) -> int:
        self.display.fill(False)
        self.draw_flag = True
        return 8

    # 00EE - RET
    def _op_00EE(self, opcode: int) -> int:
        if self.sp > 0:
            self.sp -= 1
            self.pc = self.stack[self.sp]
        else:
            print("Stack underflow on RET!")
        return 8

    # 1nnn - JP addr
    def _op_1nnn(self, opcode: int) -> int:
        self.pc = opcode & 0x0FFF
        return 12

    # 2nnn - CALL addr
    def _op_2nnn(self, opcode: int) -> int:
        if self.sp < 16:
            self.stack[self.sp] = self.pc
            self.sp += 1
            self.pc = opcode & 0x0FFF
        else:
            print("Stack overflow on CALL!")
        return 12

    # 3xkk - SE Vx, byte
    def _op_3xkk(self, opcode: int) -> int:
        x = (opcode & 0x0F00) >> 8
        kk = opcode & 0x00FF
        if self.V[x] == kk:
            self.pc += 2
        return 12

    # 4xkk - SNE Vx, byte
    def _op_4xkk(self, opcode: int) -> int:
        x = (opcode & 0x0F00) >> 8
        kk = opcode & 0x00FF
        if self.V[x] != kk:
            self.pc += 2
        return 12

    # 5xy0 - SE Vx, Vy
    def _op_5xy0(self, opcode: int) -> int:
        x = (opcode & 0x0F00) >> 8
        y = (opcode & 0x00F0) >> 4
        if self.V[x] == self.V[y]:
            self.pc += 2
        return 12

    # 6xkk - LD Vx, byte
    def _op_6xkk(self, opcode: int) -> int:
        x = (opcode & 0x0F00) >> 8
        kk = opcode & 0x00FF
        self.V[x] = kk
        return 8

    # 7xkk - ADD Vx, byte
    def _op_7xkk(self, opcode: int) -> int:
        x = (opcode & 0x0F00) >> 8
        kk = opcode & 0x00FF
        self.V[x] = (self.V[x] + kk) & 0xFF
        return 8

    # 8xy0 - LD Vx, Vy
    def _op_8xy0(self, opcode: int) -> int:
        x = (opcode & 0x0F00) >> 8
        y = (opcode & 0x00F0) >> 4
        self.V[x] = self.V[y]
        return 8

    # 8xy1 - OR Vx, Vy
    def _op_8xy1(self, opcode: int) -> int:
        x = (opcode & 0x0F00) >> 8
        y = (opcode & 0x00F0) >> 4
        self.V[x] = (self.V[x] | self.V[y]) & 0xFF
        return 8

    # 8xy2 - AND Vx, Vy
    def _op_8xy2(self, opcode: int) -> int:
        x = (opcode & 0x0F00) >> 8
        y = (opcode & 0x00F0) >> 4
        self.V[x] = (self.V[x] & self.V[y]) & 0xFF
        return 8

    # 8xy3 - XOR Vx, Vy
    def _op_8xy3(self, opcode: int) -> int:
        x = (opcode & 0x0F00) >> 8
        y = (opcode & 0x00F0) >> 4
        self.V[x] = (self.V[x] ^ self.V[y]) & 0xFF
        return 8

    # 8xy4 - ADD Vx, Vy
    def _op_8xy4(self, opcode: int) -> int:
        x = (opcode & 0x0F00) >> 8
        y = (opcode & 0x00F0) >> 4
        total = self.V[x] + self.V[y]
        self.V[x] = total & 0xFF
        self.V[0xF] = 1 if total > 255 else 0
        return 12

    # 8xy5 - SUB Vx, Vy
    def _op_8xy5(self, opcode: int) -> int:
        x = (opcode & 0x0F00) >> 8
        y = (opcode & 0x00F0) >> 4
        vx = self.V[x]
        vy = self.V[y]
        self.V[x] = (vx - vy) & 0xFF
        self.V[0xF] = 1 if vx >= vy else 0
        return 12

    # 8xy6 - SHR Vx {, Vy}
    def _op_8xy6(self, opcode: int) -> int:
        x = (opcode & 0x0F00) >> 8
        # Store least significant bit of Vx in VF
        lsb = self.V[x] & 1
        self.V[x] = (self.V[x] >> 1) & 0xFF
        self.V[0xF] = lsb
        return 12

    # 8xy7 - SUBN Vx, Vy
    def _op_8xy7(self, opcode: int) -> int:
        x = (opcode & 0x0F00) >> 8
        y = (opcode & 0x00F0) >> 4
        vx = self.V[x]
        vy = self.V[y]
        self.V[x] = (vy - vx) & 0xFF
        self.V[0xF] = 1 if vy >= vx else 0
        return 12

    # 8xyE - SHL Vx {, Vy}
    def _op_8xyE(self, opcode: int) -> int:
        x = (opcode & 0x0F00) >> 8
        msb = (self.V[x] & 0x80) >> 7
        self.V[x] = (self.V[x] << 1) & 0xFF
        self.V[0xF] = msb
        return 12

    # 9xy0 - SNE Vx, Vy
    def _op_9xy0(self, opcode: int) -> int:
        x = (opcode & 0x0F00) >> 8
        y = (opcode & 0x00F0) >> 4
        if self.V[x] != self.V[y]:
            self.pc += 2
        return 12

    # Annn - LD I, addr
    def _op_Annn(self, opcode: int) -> int:
        self.I = opcode & 0x0FFF
        return 8

    # Bnnn - JP V0, addr
    def _op_Bnnn(self, opcode: int) -> int:
        self.pc = (opcode & 0x0FFF) + self.V[0]
        return 12

    # Cxkk - RND Vx, byte
    def _op_Cxkk(self, opcode: int) -> int:
        x = (opcode & 0x0F00) >> 8
        kk = opcode & 0x00FF
        self.V[x] = random.randint(0, 255) & kk
        return 12

    # Dxyn - DRW Vx, Vy, nibble
    def _op_Dxyn(self, opcode: int) -> int:
        x = (opcode & 0x0F00) >> 8
        y = (opcode & 0x00F0) >> 4
        n = opcode & 0x000F
        
        start_x = self.V[x] % 64
        start_y = self.V[y] % 32
        
        self.V[0xF] = 0
        
        for row in range(n):
            if start_y + row >= 32:
                break
            sprite_byte = self.memory[self.I + row]
            for col in range(8):
                if start_x + col >= 64:
                    break
                sprite_pixel = (sprite_byte & (0x80 >> col)) != 0
                if sprite_pixel:
                    current_pixel = self.display[start_y + row][start_x + col]
                    if current_pixel:
                        self.V[0xF] = 1
                    self.display[start_y + row][start_x + col] = current_pixel ^ True
                    
        self.draw_flag = True
        return 16

    # Ex9E - SKP Vx
    def _op_Ex9E(self, opcode: int) -> int:
        x = (opcode & 0x0F00) >> 8
        key = self.V[x] & 0xF
        if self.keys[key]:
            self.pc += 2
        return 12

    # ExA1 - SKNP Vx
    def _op_ExA1(self, opcode: int) -> int:
        x = (opcode & 0x0F00) >> 8
        key = self.V[x] & 0xF
        if not self.keys[key]:
            self.pc += 2
        return 12

    # Fx07 - LD Vx, DT
    def _op_Fx07(self, opcode: int) -> int:
        x = (opcode & 0x0F00) >> 8
        self.V[x] = self.delay_timer
        return 8

    # Fx0A - LD Vx, K
    def _op_Fx0A(self, opcode: int) -> int:
        x = (opcode & 0x0F00) >> 8
        self.waiting_for_key_reg = x
        return 8

    # Fx15 - LD DT, Vx
    def _op_Fx15(self, opcode: int) -> int:
        x = (opcode & 0x0F00) >> 8
        self.delay_timer = self.V[x]
        return 8

    # Fx18 - LD ST, Vx
    def _op_Fx18(self, opcode: int) -> int:
        x = (opcode & 0x0F00) >> 8
        self.sound_timer = self.V[x]
        return 8

    # Fx1E - ADD I, Vx
    def _op_Fx1E(self, opcode: int) -> int:
        x = (opcode & 0x0F00) >> 8
        self.I = (self.I + self.V[x]) & 0xFFFF
        return 8

    # Fx29 - LD F, Vx
    def _op_Fx29(self, opcode: int) -> int:
        x = (opcode & 0x0F00) >> 8
        char = self.V[x] & 0xF
        self.I = self.fontset_offset + char * 5
        return 8

    # Fx33 - LD B, Vx
    def _op_Fx33(self, opcode: int) -> int:
        x = (opcode & 0x0F00) >> 8
        val = self.V[x]
        self.memory[self.I] = val // 100
        self.memory[self.I + 1] = (val // 10) % 10
        self.memory[self.I + 2] = val % 10
        return 12

    # Fx55 - LD [I], Vx
    def _op_Fx55(self, opcode: int) -> int:
        x = (opcode & 0x0F00) >> 8
        for i in range(x + 1):
            self.memory[self.I + i] = self.V[i]
        return 12

    # Fx65 - LD Vx, [I]
    def _op_Fx65(self, opcode: int) -> int:
        x = (opcode & 0x0F00) >> 8
        for i in range(x + 1):
            self.V[i] = self.memory[self.I + i]
        return 12
