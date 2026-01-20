import tkinter as tk
from tkinter import messagebox
import sys
import random
from server import ServerLogic


EMOJIS = ["✨", "💖", "🦋", "🎀", "👑", "💋", "🌸", "🦄", "💅", "🍒", "💄", "👛", "🧁", "💘"]

class Marquee(tk.Canvas):
    def __init__(self, parent, text, bg, fg):
        super().__init__(parent, bg=bg, height=30, highlightthickness=0)
        self.text = text
        self.fg = fg
        self.width = 600
        self.text_obj = self.create_text(0, 15, text=text, fill=fg, font=("Comic Sans MS", 12, "bold"), anchor='w')
        self.animate()

    def animate(self):
        self.move(self.text_obj, -2, 0)
        bbox = self.bbox(self.text_obj)
        if bbox[2] < 0:
            self.coords(self.text_obj, self.width, 15)
        self.after(50, self.animate)

class TextRedirector(object):
    def __init__(self, widget, tag="stdout"):
        self.widget = widget
        self.tag = tag

    def write(self, str):
        try:
            self.widget.configure(state="normal")
            self.widget.insert("end", str, (self.tag,))
            self.widget.see("end")
            self.widget.configure(state="disabled")
        except:
            pass  

    def flush(self):
        pass

class PinkServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("✨👑 SERVER CONTROL ROOM 👑✨")
        self.root.geometry("700x550")

        self.palette = {
            "light_pink": "#FFCFD8",
            "soft_pink":  "#FFA6CA",
            "hot_pink":   "#FF1695",
            "salmon":     "#FF9CB4",
            "rose":       "#F47EAB",
            "deep_mauve": "#DA4F8E",
            "white":      "#FFFFFF"
        }

        self.root.configure(bg=self.palette["light_pink"])

        
        self.f_header = ("Comic Sans MS", 20, "bold")
        self.f_norm = ("Verdana", 10, "bold")
        self.f_console = ("Courier New", 10, "bold")

        
        self.entry_style = {
            "bg": "white",
            "fg": self.palette["hot_pink"],
            "font": ("Fixedsys", 12),
            "justify": 'center'
        }

        
        self.logic = None

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        
        self.build_config_screen()

    def add_chaos(self, frame):
        for _ in range(20):
            lbl = tk.Label(frame, text=random.choice(EMOJIS),
                           bg=frame.cget("bg"), fg="white",
                           font=("Arial", random.randint(14, 28)))
            x = random.uniform(0.02, 0.95)
            y = random.uniform(0.02, 0.95)
            lbl.place(relx=x, rely=y)

    def clear(self):
        for w in self.root.winfo_children(): w.destroy()

    
    def build_config_screen(self):
        self.clear()

        
        container = tk.Frame(self.root, bg=self.palette["salmon"], bd=10, relief="ridge")
        container.place(relx=0.5, rely=0.5, anchor="center", width=500, height=450)

        self.add_chaos(container)

        content_frame = tk.Frame(container, bg=self.palette["light_pink"], bd=4, relief="solid")
        content_frame.place(relx=0.5, rely=0.5, anchor="center", width=350, height=300)

        tk.Label(content_frame, text="👑 SERVER CONFIG 👑", bg=self.palette["light_pink"],
                 fg=self.palette["hot_pink"], font=self.f_header).pack(pady=20)

        
        tk.Label(content_frame, text="Binding IP Address:", bg=self.palette["light_pink"],
                 fg=self.palette["deep_mauve"], font=self.f_norm).pack()
        self.ent_ip = tk.Entry(content_frame, **self.entry_style)
        self.ent_ip.insert(0, "127.0.0.1")
        self.ent_ip.pack(pady=5)

        
        tk.Label(content_frame, text="Listening Port:", bg=self.palette["light_pink"],
                 fg=self.palette["deep_mauve"], font=self.f_norm).pack()
        self.ent_port = tk.Entry(content_frame, **self.entry_style)
        self.ent_port.insert(0, "55555")
        self.ent_port.pack(pady=5)

        
        btn = tk.Button(content_frame, text="✨ START SERVER ✨",
                        bg=self.palette["hot_pink"], fg="white",
                        font=("Impact", 14), relief="raised", bd=4,
                        command=self.start_server_action)
        btn.pack(pady=25)

    def start_server_action(self):
        ip = self.ent_ip.get().strip()
        port_str = self.ent_port.get().strip()

        if not ip or not port_str.isdigit():
            messagebox.showerror("Oops", "Invalid IP or Port!")
            return

        port = int(port_str)

        
        self.build_console_screen()

        
        sys.stdout = TextRedirector(self.log_area, "stdout")
        sys.stderr = TextRedirector(self.log_area, "stderr")

        
        self.logic = ServerLogic(ip, port)

        
        def log_callback(message):
            self.log_area.configure(state="normal")
            self.log_area.insert("end", message + "\n")
            self.log_area.see("end")
            self.log_area.configure(state="disabled")

        
        self.logic.start_async(on_log=log_callback)

    
    def build_console_screen(self):
        self.clear()
        self.root.configure(bg=self.palette["salmon"])

        
        marquee_txt = "SERVER ONLINE 💖 NO HACKERS ALLOWED 💖 KEEP IT CLEAN 💖 IT BURNS WHEN IP"
        mq = Marquee(self.root, marquee_txt, self.palette["deep_mauve"], "white")
        mq.pack(side="top", fill="x")

        
        container = tk.Frame(self.root, bg=self.palette["light_pink"], bd=5, relief="ridge")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(container, text="💅 SYSTEM LOGS 💅", bg=self.palette["light_pink"],
                 fg=self.palette["hot_pink"], font=self.f_header).pack(pady=10)

        
        console_frame = tk.Frame(container, bg=self.palette["hot_pink"], bd=2)
        console_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.log_area = tk.Text(console_frame, bg="white", fg=self.palette["deep_mauve"],
                                font=self.f_console, state="disabled", bd=5, relief="flat")
        self.log_area.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(self.log_area, command=self.log_area.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_area['yscrollcommand'] = scrollbar.set

        
        btn_frame = tk.Frame(container, bg=self.palette["light_pink"])
        btn_frame.pack(fill="x", pady=10)

        btn_refresh = tk.Button(btn_frame, text="✨ WHO IS ONLINE? ✨",
                                bg=self.palette["hot_pink"], fg="white",
                                font=("Impact", 12), relief="raised", bd=3,
                                command=self.show_users)
        btn_refresh.pack(side="bottom", pady=5)

    def show_users(self):
        if not self.logic:
            print("Server not running!")
            return

        print("\n💕 --- SQUAD CHECK --- 💕")
        users = self.logic.get_online_users()

        if not users:
            print("No BFFs online right now :(")
        else:
            for user in users:
                if user["address"]:
                    print(f"🎀 {user['nickname']} is here! (IP: {user['address']})")
                else:
                    print(f"🎀 {user['nickname']} (Ghost mode)")
        print("💕 --------------------- 💕\n")

    def on_closing(self):
        
        if self.logic:
            self.logic.stop()

        sys.stdout = sys.__stdout__  
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = PinkServerGUI(root)
    root.mainloop()
