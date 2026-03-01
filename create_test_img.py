from PIL import Image, ImageDraw, ImageFont

img = Image.new('RGB', (400, 200), color = (255, 255, 255))
d = ImageDraw.Draw(img)
d.text((10,10), "This is a test of the handwriting extraction.", fill=(0,0,0))
img.save('test_handwriting.png')
print("Test image created.")
