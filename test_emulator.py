import os
import unittest
import numpy as np
from chip8 import Chip8
from savestate import save_state, load_state

class TestChip8Emulator(unittest.TestCase):
    def setUp(self):
        self.cpu = Chip8()

    def test_fontset_loaded(self):
        # Font for character '0' should be at fontset_offset (0x50)
        self.assertEqual(self.cpu.memory[0x50], 0xF0)
        self.assertEqual(self.cpu.memory[0x51], 0x90)
        # Font for character 'F' should end at 0x50 + 16 * 5 - 1 = 0x50 + 79 = 0x9F
        self.assertEqual(self.cpu.memory[0x9F], 0x80)

    def test_op_1nnn_jump(self):
        # PC points to 0x200 by default. Set instruction: JP 0x228
        self.cpu.memory[0x200] = 0x12
        self.cpu.memory[0x201] = 0x28
        self.cpu.cycle()
        self.assertEqual(self.cpu.pc, 0x228)

    def test_op_2nnn_and_00EE_call_return(self):
        # Call 0x300, then return
        # At 0x200: CALL 0x300 (0x23 0x00)
        # At 0x300: RET (0x00 0xEE)
        self.cpu.memory[0x200] = 0x23
        self.cpu.memory[0x201] = 0x00
        self.cpu.memory[0x300] = 0x00
        self.cpu.memory[0x301] = 0xEE

        # Execute CALL
        self.cpu.cycle()
        self.assertEqual(self.cpu.pc, 0x300)
        self.assertEqual(self.cpu.sp, 1)
        self.assertEqual(self.cpu.stack[0], 0x202) # CALL was at 0x200, so next PC was 0x202

        # Execute RET
        self.cpu.cycle()
        self.assertEqual(self.cpu.pc, 0x202)
        self.assertEqual(self.cpu.sp, 0)

    def test_op_6xkk_and_7xkk_ld_add(self):
        # LD V1, 0xFE (0x61 0xFE)
        # ADD V1, 0x05 (0x71 0x05)
        self.cpu.memory[0x200] = 0x61
        self.cpu.memory[0x201] = 0xFE
        self.cpu.memory[0x202] = 0x71
        self.cpu.memory[0x203] = 0x05

        self.cpu.cycle() # LD V1, 0xFE
        self.assertEqual(self.cpu.V[1], 0xFE)

        self.cpu.cycle() # ADD V1, 0x05 (should overflow 255 to 0x03)
        self.assertEqual(self.cpu.V[1], 0x03)
        self.assertEqual(self.cpu.V[0xF], 0) # VF must remain unchanged (0)

    def test_op_8xy4_add_carry(self):
        # LD V1, 0xC8 (200)
        # LD V2, 0x64 (100)
        # ADD V1, V2 (0x81 0x24) -> sum = 300 (over 255), V1=44, VF=1
        self.cpu.V[1] = 200
        self.cpu.V[2] = 100
        
        self.cpu.memory[0x200] = 0x81
        self.cpu.memory[0x201] = 0x24
        
        self.cpu.cycle()
        self.assertEqual(self.cpu.V[1], 44)
        self.assertEqual(self.cpu.V[0xF], 1)

    def test_op_8xy5_sub_borrow(self):
        # Case 1: V1 >= V2 (No borrow, VF = 1)
        self.cpu.V[1] = 100
        self.cpu.V[2] = 40
        self.cpu.memory[0x200] = 0x81
        self.cpu.memory[0x201] = 0x25
        self.cpu.cycle()
        self.assertEqual(self.cpu.V[1], 60)
        self.assertEqual(self.cpu.V[0xF], 1)

        # Case 2: V1 < V2 (Borrow, VF = 0)
        self.cpu.V[1] = 30
        self.cpu.V[2] = 40
        self.cpu.pc = 0x202
        self.cpu.memory[0x202] = 0x81
        self.cpu.memory[0x203] = 0x25
        self.cpu.cycle()
        self.assertEqual(self.cpu.V[1], 246) # (30 - 40) & 0xFF
        self.assertEqual(self.cpu.V[0xF], 0)

    def test_op_Fx55_and_Fx65_store_load_registers(self):
        # Set registers
        for i in range(5):
            self.cpu.V[i] = i * 10
        self.cpu.I = 0x400

        # F455: Store V0-V4 in mem[I]
        self.cpu.memory[0x200] = 0xF4
        self.cpu.memory[0x201] = 0x55
        self.cpu.cycle()

        # Check memory
        for i in range(5):
            self.assertEqual(self.cpu.memory[0x400 + i], i * 10)

        # Reset registers to 0
        for i in range(5):
            self.cpu.V[i] = 0

        # F465: Load V0-V4 from mem[I]
        self.cpu.memory[0x202] = 0xF4
        self.cpu.memory[0x203] = 0x65
        self.cpu.cycle()

        # Check registers
        for i in range(5):
            self.assertEqual(self.cpu.V[i], i * 10)

    def test_save_load_state(self):
        # Set some state
        self.cpu.V[1] = 0xBB
        self.cpu.I = 0x777
        self.cpu.pc = 0x333
        self.cpu.display[5][5] = True

        filename = "test_state.ch8state"
        save_state(self.cpu, filename)

        # Create new CPU and load state into it
        new_cpu = Chip8()
        load_state(new_cpu, filename)

        self.assertEqual(new_cpu.V[1], 0xBB)
        self.assertEqual(new_cpu.I, 0x777)
        self.assertEqual(new_cpu.pc, 0x333)
        self.assertTrue(new_cpu.display[5][5])

        # Cleanup file
        if os.path.exists(filename):
            os.remove(filename)

if __name__ == "__main__":
    unittest.main()
