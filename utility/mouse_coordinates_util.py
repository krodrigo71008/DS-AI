import mouse


def print_mouse_coords():
    print(mouse.get_position())


mouse.on_button(print_mouse_coords, buttons="left", types="down")

while True:
    pass
