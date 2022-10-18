from PIL import Image, ImageTk

def open_image(path) -> ImageTk.PhotoImage:
    return ImageTk.PhotoImage(Image.open(path))