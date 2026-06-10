import pickle

def save_state(cpu, filename):
    try:
        with open(filename, 'wb') as f:
            pickle.dump(cpu, f)
        print(f"State saved to {filename}")
    except Exception as e:
        print(f"Error saving state: {e}")

def load_state(cpu, filename):
    try:
        with open(filename, 'rb') as f:
            new_cpu = pickle.load(f)
            # Copy all state attributes from deserialized object into current object
            cpu.__dict__.update(new_cpu.__dict__)
            cpu.draw_flag = True   # Force redraw on display
        print(f"State loaded from {filename}")
    except Exception as e:
        print(f"Error loading state: {e}")
