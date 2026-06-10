import sys
import threading
import queue

class Debugger:
    def __init__(self, cpu):
        self.cpu = cpu
        self.breakpoints = set()
        self.command_queue = queue.Queue()
        self.debug_mode = False
        self.step_requested = False
        self.input_thread = None
        self.stop_thread = False
        
    def is_running(self) -> bool:
        return self.input_thread is not None and self.input_thread.is_alive()
        
    def start(self):
        if self.is_running():
            self.debug_mode = True
            return
            
        self.debug_mode = True
        self.stop_thread = False
        # Clear command queue
        while not self.command_queue.empty():
            try:
                self.command_queue.get_nowait()
            except queue.Empty:
                break
                
        self.input_thread = threading.Thread(target=self._input_loop, daemon=True)
        self.input_thread.start()
        print("\n--- Chip-8 CLI Debugger Started ---")
        print("Type 'help' or 'h' for commands.")
        self._prompt()
        
    def stop(self):
        self.debug_mode = False
        
    def _prompt(self):
        sys.stdout.write("dbg> ")
        sys.stdout.flush()
        
    def _input_loop(self):
        while not self.stop_thread:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                cmd = line.strip()
                self.command_queue.put(cmd)
            except Exception as e:
                print(f"\nDebugger input error: {e}")
                break

    def handle_commands(self):
        """Processes any queued commands. Call from the main thread loop."""
        had_commands = False
        while not self.command_queue.empty():
            had_commands = True
            cmd = self.command_queue.get()
            self.execute_command(cmd)
            
        if had_commands and self.debug_mode:
            self._prompt()

    def execute_command(self, cmd_line: str):
        if not cmd_line:
            return
            
        parts = cmd_line.split()
        cmd = parts[0].lower()
        args = parts[1:]
        
        if cmd in ("help", "h"):
            print("Available Commands:")
            print("  step, s         - Execute exactly one instruction cycle")
            print("  continue, c     - Resume normal execution")
            print("  break, b <addr> - Set a breakpoint at hex address (e.g. b 20a)")
            print("  delbreak, d <ad>- Remove a breakpoint")
            print("  breakpoints, bl - List active breakpoints")
            print("  regs, r         - Inspect CPU registers (PC, I, SP, V0-VF)")
            print("  stack           - Inspect stack levels and SP")
            print("  mem, m <ad> [l] - Inspect memory in hex starting at address (default length 16)")
            print("  quit, q         - Terminate the emulator")
        
        elif cmd in ("step", "s"):
            self.step_requested = True
            
        elif cmd in ("continue", "c"):
            self.debug_mode = False
            print("Resuming execution...")
            
        elif cmd in ("break", "b"):
            if not args:
                print("Error: Specify a hex address (e.g. break 200)")
                return
            try:
                addr = int(args[0], 16)
                self.breakpoints.add(addr)
                print(f"Breakpoint set at 0x{addr:03X}")
            except ValueError:
                print(f"Error: Invalid hex address '{args[0]}'")
                
        elif cmd in ("delbreak", "d"):
            if not args:
                print("Error: Specify a hex address to delete")
                return
            try:
                addr = int(args[0], 16)
                if addr in self.breakpoints:
                    self.breakpoints.remove(addr)
                    print(f"Breakpoint at 0x{addr:03X} removed")
                else:
                    print(f"No breakpoint found at 0x{addr:03X}")
            except ValueError:
                print(f"Error: Invalid hex address '{args[0]}'")
                
        elif cmd in ("breakpoints", "bl"):
            if not self.breakpoints:
                print("No active breakpoints")
            else:
                print("Active Breakpoints:")
                for addr in sorted(self.breakpoints):
                    print(f"  0x{addr:03X}")
                    
        elif cmd in ("regs", "r"):
            print(f"PC: 0x{self.cpu.pc:03X}  I: 0x{self.cpu.I:03X}  SP: {self.cpu.sp}  DT: {self.cpu.delay_timer}  ST: {self.cpu.sound_timer}")
            print("Registers V0-VF:")
            for i in range(8):
                print(f"  V{i:X}: 0x{self.cpu.V[i]:02X}", end="")
            print()
            for i in range(8, 16):
                print(f"  V{i:X}: 0x{self.cpu.V[i]:02X}", end="")
            print()
            
        elif cmd == "stack":
            print(f"Stack Pointer (SP): {self.cpu.sp}")
            if self.cpu.sp == 0:
                print("  Stack is empty")
            else:
                for i in range(self.cpu.sp):
                    print(f"  Stack[{i}]: 0x{self.cpu.stack[i]:03X}")
                    
        elif cmd in ("mem", "m"):
            if not args:
                print("Error: Specify starting hex address (e.g. mem 200)")
                return
            try:
                addr = int(args[0], 16)
                length = int(args[1]) if len(args) > 1 else 16
                if addr < 0 or addr >= 4096:
                    print("Error: Address out of bounds (0 - 4095)")
                    return
                end_addr = min(addr + length, 4096)
                data = self.cpu.memory[addr:end_addr]
                
                # Print hex block format
                for i, byte in enumerate(data):
                    curr_addr = addr + i
                    if i % 16 == 0:
                        if i > 0:
                            print()
                        print(f"0x{curr_addr:03X}: ", end="")
                    print(f"{byte:02X} ", end="")
                print()
            except ValueError:
                print("Error: Invalid address or length format")
                
        elif cmd in ("quit", "q"):
            self.cpu.should_exit = True
            
        else:
            print(f"Unknown command: '{cmd}'. Type 'help' for options.")
