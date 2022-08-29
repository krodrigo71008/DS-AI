from PIL import Image, ImageDraw

# (65, 190), (65, 890) closed crafting tabs
# (420, 1010), (1500, 1010) inventory
# (900, 460), (1015, 615) character
# (1680, 0), (1920, 290) status
# (1780, 950), (1920, 1080) map icons
# considering 1920x1080

if __name__ == "__main__":
    image_path = "tests/0872.jpg"
    points = [(960, 550)]
    with Image.open(image_path) as image:
        draw = ImageDraw.Draw(image)
        for point in points:
            draw.ellipse((point[0]-5, point[1]-5, point[0]+5, point[1]+5), fill=128)
        del draw
        image.save("result_points.png")
