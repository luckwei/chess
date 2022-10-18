import tkinter as tk


class Root(tk.Tk):
    def __init__(self, title="CHESS", icon="res/chess.ico", **kwargs):
        super().__init__(**kwargs)
        self.title(title)
        self.iconbitmap(icon)

        self.bind("<KeyPress>", lambda event: print(event))
        self.bind("<KeyPress-Escape>", lambda event: self.quit())
        
        