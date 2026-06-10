import pygame
import sys
import numpy as np
import asyncio
from chip8 import Chip8
from debugger import Debugger
from savestate import save_state, load_state

# --- Window Layout Constants ---
WINDOW_W = 960
WINDOW_H = 480

SCREEN_X = 40
SCREEN_Y = 80
SCREEN_SCALE = 10
SCREEN_W = 64 * SCREEN_SCALE
SCREEN_H = 32 * SCREEN_SCALE

# --- Theme Colors ---
BG_COLOR = (18, 18, 20)           # Deep charcoal black
PANEL_BG = (26, 26, 30)           # Medium dark grey
BORDER_COLOR = (46, 47, 56)       # Subtle grey
TEXT_COLOR = (224, 224, 230)      # Clean off-white
TEXT_MUTED = (140, 142, 153)      # Muted grey
PIXEL_ON = (0, 229, 255)          # Vibrant Neon Cyan
PIXEL_OFF = (26, 26, 30)          # Matches panel bg (screen interior)

# --- Key Mapping ---
KEY_MAP = {
    pygame.K_1: 0x1, pygame.K_2: 0x2, pygame.K_3: 0x3, pygame.K_4: 0xC,
    pygame.K_q: 0x4, pygame.K_w: 0x5, pygame.K_e: 0x6, pygame.K_r: 0xD,
    pygame.K_a: 0x7, pygame.K_s: 0x8, pygame.K_d: 0x9, pygame.K_f: 0xE,
    pygame.K_z: 0xA, pygame.K_x: 0x0, pygame.K_c: 0xB, pygame.K_v: 0xF,
}

def generate_beep(frequency=440, duration=1.0) -> pygame.mixer.Sound:
    """Synthesizes a simple square wave beep using numpy."""
    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    t = np.arange(n_samples) / sample_rate
    wave = np.sign(np.sin(2 * np.pi * frequency * t))
    # Scale to 16-bit signed integers (moderate volume)
    audio_data = (wave * 8000).astype(np.int16)
    
    # Check actual mixer configuration channels (mono vs stereo)
    init_params = pygame.mixer.get_init()
    actual_channels = init_params[2] if init_params else 1
    if actual_channels == 2:
        audio_data = np.column_stack((audio_data, audio_data))
        
    return pygame.sndarray.make_sound(audio_data)

def draw_text(surface, text, x, y, color, font):
    text_surface = font.render(text, True, color)
    surface.blit(text_surface, (x, y))

def draw_keypad(surface, keys, font):
    start_x = 720
    start_y = 200
    box_size = 35
    spacing = 6
    
    # Key layout values (in 4x4 visual order)
    visual_layout = [
        [("1", 0x1), ("2", 0x2), ("3", 0x3), ("C", 0xC)],
        [("4", 0x4), ("5", 0x5), ("6", 0x6), ("D", 0xD)],
        [("7", 0x7), ("8", 0x8), ("9", 0x9), ("E", 0xE)],
        [("A", 0xA), ("0", 0x0), ("B", 0xB), ("F", 0xF)]
    ]
    
    for r, row in enumerate(visual_layout):
        for c, (label, val) in enumerate(row):
            x = start_x + c * (box_size + spacing)
            y = start_y + r * (box_size + spacing)
            
            # Highlight if key is currently pressed
            if keys[val]:
                color = PIXEL_ON
                text_color = BG_COLOR
            else:
                color = BORDER_COLOR
                text_color = TEXT_COLOR
                
            pygame.draw.rect(surface, color, (x, y, box_size, box_size), border_radius=4)
            
            lbl_surf = font.render(label, True, text_color)
            lbl_rect = lbl_surf.get_rect(center=(x + box_size/2, y + box_size/2))
            surface.blit(lbl_surf, lbl_rect)

def render_display(screen, display):
    """Renders the Chip-8 screen frame and pixels."""
    # Draw screen border frame
    pygame.draw.rect(screen, BORDER_COLOR, (SCREEN_X - 4, SCREEN_Y - 4, SCREEN_W + 8, SCREEN_H + 8), width=2, border_radius=6)
    pygame.draw.rect(screen, PIXEL_OFF, (SCREEN_X, SCREEN_Y, SCREEN_W, SCREEN_H))
    
    # Draw active pixels
    for y in range(32):
        for x in range(64):
            if display[y][x]:
                pygame.draw.rect(screen, PIXEL_ON, 
                                 (SCREEN_X + x * SCREEN_SCALE, SCREEN_Y + y * SCREEN_SCALE, SCREEN_SCALE, SCREEN_SCALE))

async def main():
    pygame.init()
    pygame.mixer.init(frequency=44100, size=-16, channels=1)
    
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("Chip-8 Enhanced Emulator")
    
    # Load Fonts
    try:
        font_mono = pygame.font.SysFont("Courier New", 16)
        font_bold = pygame.font.SysFont("Courier New", 18, bold=True)
        font_large = pygame.font.SysFont("Courier New", 28, bold=True)
    except Exception:
        # Fallback if SysFont fails
        font_mono = pygame.font.Font(None, 22)
        font_bold = pygame.font.Font(None, 24)
        font_large = pygame.font.Font(None, 36)
        
    cpu = Chip8()
    
    # Load ROM
    rom_path = "roms/ibm_logo.ch8"
    if len(sys.argv) > 1:
        rom_path = sys.argv[1]
        
    try:
        cpu.load_rom(rom_path)
        print(f"Loaded ROM: {rom_path}")
    except Exception as e:
        print(f"Failed to load ROM: {e}")
        # Try loading default
        try:
            cpu.load_rom("roms/ibm_logo.ch8")
            print("Loaded fallback ROM: roms/ibm_logo.ch8")
        except Exception:
            pass

    debugger = Debugger(cpu)
    
    # Audio Setup
    continuous_beep = generate_beep(440, 1.0)
    sound_playing = False
    
    clock = pygame.time.Clock()
    target_cpu_hz = 700  # Default emulation speed
    
    cpu_speed_accumulator = 0.0
    timer_accumulator = 0.0
    timer_rate = 1000.0 / 60.0  # 60 Hz timer ticks in ms
    
    last_time = pygame.time.get_ticks()
    running = True
    
    while running:
        current_time = pygame.time.get_ticks()
        dt = current_time - last_time
        last_time = current_time
        
        # --- Handle Input Events ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F12:     # Toggle Debugger
                    if debugger.debug_mode:
                        debugger.stop()
                        print("\nDebugger stopped. Resuming CPU...")
                    else:
                        debugger.start()
                elif event.key == pygame.K_F10:   # Step instruction
                    if debugger.debug_mode:
                        debugger.step_requested = True
                elif event.key == pygame.K_F5:    # Quick Save
                    save_state(cpu, "quicksave.ch8state")
                elif event.key == pygame.K_F6:    # Quick Load
                    load_state(cpu, "quicksave.ch8state")
                else:
                    if event.key in KEY_MAP:
                        cpu.keys[KEY_MAP[event.key]] = True
                        
            elif event.type == pygame.KEYUP:
                if event.key in KEY_MAP:
                    cpu.keys[KEY_MAP[event.key]] = False
                    
        # Process external quit request from debugger command
        if cpu.should_exit:
            running = False
            
        # --- Handle Debugger Commands ---
        debugger.handle_commands()
        
        # --- Execute CPU Cycles ---
        if not debugger.debug_mode:
            # Emulate standard instruction cycles matching target HZ
            cpu_speed_accumulator += target_cpu_hz * (dt / 1000.0)
            while cpu_speed_accumulator >= 1.0:
                # Check for breakpoints
                if cpu.pc in debugger.breakpoints:
                    print(f"\n[Breakpoint] Hit address 0x{cpu.pc:03X}!")
                    debugger.start()
                    cpu_speed_accumulator = 0.0
                    break
                    
                cpu.cycle()
                cpu_speed_accumulator -= 1.0
        else:
            # Step one instruction if requested
            if debugger.step_requested:
                cpu.cycle()
                debugger.step_requested = False
                
        # --- Process 60 Hz Timers ---
        timer_accumulator += dt
        while timer_accumulator >= timer_rate:
            if cpu.delay_timer > 0:
                cpu.delay_timer -= 1
            if cpu.sound_timer > 0:
                cpu.sound_timer -= 1
            timer_accumulator -= timer_rate
            
        # --- Sound Buzzer Control ---
        if cpu.sound_timer > 0 and not debugger.debug_mode:
            if not sound_playing:
                continuous_beep.play(-1)
                sound_playing = True
        else:
            if sound_playing:
                continuous_beep.stop()
                sound_playing = False
                
        # --- Rendering Dashboard & UI ---
        screen.fill(BG_COLOR)
        
        # 1. Draw Title Header
        draw_text(screen, "CHIP-8 ENHANCED EMULATOR", SCREEN_X, 25, PIXEL_ON, font_large)
        
        # 2. Draw Screen Grid
        render_display(screen, cpu.display)
        
        # 3. Draw Sidebar background panel
        pygame.draw.rect(screen, PANEL_BG, (700, 80, 230, 328), border_radius=6)
        pygame.draw.rect(screen, BORDER_COLOR, (700, 80, 230, 328), width=2, border_radius=6)
        
        # 4. Draw Status Box
        status_x, status_y = 715, 95
        status_w, status_h = 200, 40
        if debugger.debug_mode:
            status_text = "STATUS: PAUSED / DBG"
            status_color = (255, 153, 0)
        else:
            status_text = "STATUS: RUNNING"
            status_color = (0, 255, 102)
            
        pygame.draw.rect(screen, BG_COLOR, (status_x, status_y, status_w, status_h), border_radius=4)
        pygame.draw.rect(screen, status_color, (status_x, status_y, status_w, status_h), width=2, border_radius=4)
        
        status_surf = font_bold.render(status_text, True, status_color)
        status_rect = status_surf.get_rect(center=(status_x + status_w/2, status_y + status_h/2))
        screen.blit(status_surf, status_rect)
        
        # 5. Draw Registers & CPU Info
        draw_text(screen, f"PC: 0x{cpu.pc:03X}", 720, 150, TEXT_COLOR, font_mono)
        draw_text(screen, f"I : 0x{cpu.I:03X}", 830, 150, TEXT_COLOR, font_mono)
        
        # 6. Draw Keypad Grid
        draw_keypad(screen, cpu.keys, font_bold)
        
        # 7. Draw Footer Info
        footer_y = 425
        draw_text(screen, "F5: Quick Save  |  F6: Quick Load  |  F10: Step  |  F12: Open CLI Debugger", SCREEN_X, footer_y, TEXT_MUTED, font_mono)
        
        # Render update
        pygame.display.flip()
        await asyncio.sleep(0)
        clock.tick(60)
        
    # Cleanup on close
    continuous_beep.stop()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    asyncio.run(main())
