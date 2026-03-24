#!/usr/bin/env python3
"""
Create a test image for Instagram posting
"""
import sys
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

# Create a 1080x1080 image (Instagram square format)
img = Image.new('RGB', (1080, 1080), color='#1E3A8A')  # Blue background

# Add text
draw = ImageDraw.Draw(img)

# Try to use a nice font, fallback to default
try:
    font_large = ImageFont.truetype("arial.ttf", 80)
    font_medium = ImageFont.truetype("arial.ttf", 50)
except:
    font_large = ImageFont.load_default()
    font_medium = ImageFont.load_default()

# Add text to image
text1 = "🤖 AI Employee"
text2 = "Powered by Claude Code"
text3 = "Automating Business Operations"

# Center the text
draw.text((540, 400), text1, fill='white', font=font_large, anchor='mm')
draw.text((540, 540), text2, fill='white', font=font_medium, anchor='mm')
draw.text((540, 640), text3, fill='white', font=font_medium, anchor='mm')

# Save image
output_path = Path('instagram_test_post.jpg')
img.save(output_path, 'JPEG', quality=95)

print(f"✅ Test image created: {output_path}")
print(f"   Size: 1080x1080 pixels")
print(f"   Format: JPEG")
