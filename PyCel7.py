class appWrapper:
    def __init__(self):
        self.config = {}
        self.callbacks = {}
        self.code = []
        self.current_callback = None
        
    def set_config(self, **kwargs):
        self.config.update(kwargs)
        
    def _add_code(self, cmd, *args):
        args_str = " ".join(map(str, args))
        self.code.append(f"({cmd} {args_str})")
        
    def color(self, clr):
        self._add_code("color", clr)
        
    def put(self, x, y, text):
        self._add_code("put", x, y, f'"{text}"')
        
    def fill(self, x, y, w, h, char):
        self._add_code("fill", x, y, w, h, f'"{char}"')
        
    def poke(self, addr, value):
        self._add_code("poke", addr, value)
        
    def peek(self, addr, length=None):
        if length:
            self._add_code("peek", addr, length)
        else:
            self._add_code("peek", addr)
    
    def callback(self, name):
        def decorator(f):
            self.current_callback = name
            self.code = []
            f()
            self.callbacks[name] = self.code
            self.current_callback = None
            return f
        return decorator
    
    def build(self, filename):
        with open(filename, "w") as f:
            for k, v in self.config.items():
                if isinstance(v, str):
                    v = f'"{v}"'
                f.write(f"(= {k} {v})\n\n")
            
            for name, code in self.callbacks.items():
                f.write(f"(= {name} (fn []\n")
                f.write("    " + "\n    ".join(code) + "\n))\n\n")
            
            if self.code and not self.current_callback:
                f.write("\n".join(self.code) + "\n")

def quick():
    app = appWrapper()
    app.set_config(title = "App", width = 32, height = 32, debug = False)
    print("Generating callback...")
    @app.callback("init")
    def _():
        app.poke(0x4000, "\\x00\\x01\\x02\\x03")
    print("Generated callback!")
    print("Generating step...")
    @app.callback("step")
    def _():
        app.fill(0, 0, 16, 16, " ")
        app.color(1)
        app.put(5, 5, "PyCel7")
        app.color(4)
        app.put(7, 8, "@dsient")
    print("Generated step!")
    print("Generating keydown...")
    @app.callback("keydown")
    def _():
        app.fill(0, 0, 16, 16, " ")
        app.put(0, 0, "(keydown code here)")
    print("Generated keydown!")
    app.build("app.c7")
    print("App generated! Check PyCel7's directory!")
    mainmenu()
 
def advanced():
    app = appWrapper()
    
    # helpers
    def input_int(prompt, default, min_val=1, max_val=1024):
        while True:
            try:
                value = input(f"{prompt} [{default}]: ") or default
                return max(min(int(value), max_val), min_val)
            except ValueError:
                print(f"Please enter a number between {min_val}-{max_val}")

    def input_hex(prompt, default):
        while True:
            value = input(f"{prompt} [0x{default:04x}]: ").strip()
            if not value:
                return default
            try:
                return int(value, 16)
            except ValueError:
                print("Invalid hexadecimal format (e.g., 4000, 52a0)")

    def input_bool(prompt, default=True):
        res = input(f"{prompt} [{'Y/n' if default else 'Y/N'}]: ").lower()
        return default if res == "" else res.startswith('y')

    # core configs
    title = input("Window title [My Cel7 App]: ") or "PyCel7 Generated App"
    width = input_int("Width (16-64)", 32, 16, 64)
    height = input_int("Height (16-64)", 32, 16, 64)
    debug = input_bool("Enable debug mode", False)

    app.set_config(
        title=title,
        width=width,
        height=height,
        debug="true" if debug else "false"
    )
    
    # memory configs
    print("\n--- Memory Settings ---")
    palette_addr = input_hex("Palette memory address", 0x4000)
    font_addr = input_hex("Font memory address", 0x4040)
    screen_addr = input_hex("Screen buffer address", 0x52a0)
    
    app.set_config(
        palette_addr=palette_addr,
        font_addr=font_addr,
        screen_addr=screen_addr
    )

    # pallette configs
    print("\n--- Color Palette ---")
    if input_bool("Customize palette? (16 colors)", False):
        palette = []
        for i in range(16):
            default = f"{i:02x}"*3  # Grayscale default
            while True:
                col = input(f"Color {i} (RRGGBB hex) [{default}]: ") or default
                if len(col) == 6:
                    try:
                        # Convert to cel7's 2-byte color format
                        r = int(col[0:2], 16) >> 4
                        g = int(col[2:4], 16) >> 4
                        b = int(col[4:6], 16) >> 4
                        palette.append(f"\\x{(g << 4) | r}\\x{b}")
                        break
                    except:
                        pass
                print("Invalid format. Use 6 hex chars like 'ff00ff'")
        app.poke(palette_addr, "".join(palette))
    else:
        # pallette taken from snake example
        app.poke(palette_addr, "\\x00\\x01\\x02\\x03")

    # font configs
    print("\n--- Font Settings ---")
    if input_bool("Load custom font?", False):
        font_data = input("Paste font data (\\x00\\x01... format) [Enter for default]: ")
        if font_data:
            app.poke(font_addr, font_data)
    else:
        # again, snake pallette
        app.poke(font_addr, "\\x00\\x01\\x02\\x03...")

    @app.callback("step")
    def _():
        w = app.config["width"]
        h = app.config["height"]
        custom_text = input("Enter centered text: ") or "My App"
        
        app.fill(0, 0, w, h, " ")
        text_x = (w // 2) - (len(custom_text) // 2)
        text_y = h // 2
        
        app.color(int(input("Text color (0-15): ") or 1))
        app.put(text_x, text_y, custom_text)
        
        if input("Add subtitle? (y/n) ").lower() == 'y':
            sub_text = input("Subtitle text: ")
            sub_x = (w // 2) - (len(sub_text) // 2)
            app.color(int(input("Subtitle color (0-15): ") or 4))
            app.put(sub_x, text_y + 2, sub_text)

    # generate the app
    filename = input("\nOutput filename [app.c7]: ") or "app.c7"
    app.build(filename)
    print(f"\nApp generated to {filename}!)
    mainmenu()

def mainmenu():
    print("Welcome to PyCel7, a quick app generator for the cel7 framework.")
    print("Made by @DSiENT!\n")
    print("About the Cel7 framework - [ https://rxi.itch.io/cel7 ]\n")
    print("- Main Menu -")
    print("[1] Quick Gen")
    print("[2] Advanced Gen")
    mc = int(input(">>> "))
    match mc:
        case 1:
            print("USR selected: Quick Gen!")
            quick()
        case 2:
            print("USR selected: Advanced Gen!")
            advanced()
        case _:
            print(mc + "IS NOT A VALID SELECTION")
            mainmenu()

mainmenu()
