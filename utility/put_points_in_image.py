from PIL import Image, ImageDraw

# (65, 190), (65, 890) closed crafting tabs
# (420, 1010), (1500, 1010) inventory
# (900, 460), (1015, 615) character
# (1680, 0), (1920, 290) status
# (1780, 950), (1920, 1080) map icons

if __name__ == "__main__":
    image_path = "perception/bg_images/out886.png"
    points = [(65, 190), (65, 890), (420, 1010), (1500, 1010), (900, 460), (1015, 615), (1680, 290), (1780, 950)]
    with Image.open(image_path) as image:
        draw = ImageDraw.Draw(image)
        for point in points:
            draw.ellipse((point[0]-5, point[1]-5, point[0]+5, point[1]+5), fill=128)
        del draw
        image.save("result_points.png")
