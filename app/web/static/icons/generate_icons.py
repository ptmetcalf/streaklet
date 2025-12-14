#!/usr/bin/env python3
"""
Generate PWA icons for Streaklet.
Requires Pillow: pip install Pillow
"""

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("Error: Pillow is not installed.")
    print("Install it with: pip install Pillow")
    print("Alternatively, use the generate-icons.html file in a browser.")
    exit(1)

import os

# Icon sizes required by the PWA manifest
SIZES = [72, 96, 128, 144, 152, 192, 384, 512]

# Colors
BG_COLOR = (59, 130, 246)  # #3b82f6 (Streaklet blue)
FG_COLOR = (255, 255, 255)  # White


def draw_checkmark(draw, size):
    """Draw a checkmark symbol on the image."""
    center_x = size // 2
    center_y = size // 2
    check_size = size // 2

    # Checkmark path
    line_width = max(size // 12, 2)
    points = [
        (center_x - check_size * 0.3, center_y),
        (center_x - check_size * 0.05, center_y + check_size * 0.25),
        (center_x + check_size * 0.35, center_y - check_size * 0.25),
    ]

    # Draw checkmark lines
    draw.line(
        [points[0], points[1]],
        fill=FG_COLOR,
        width=line_width,
        joint='curve'
    )
    draw.line(
        [points[1], points[2]],
        fill=FG_COLOR,
        width=line_width,
        joint='curve'
    )


def generate_icon(size):
    """Generate a single icon of the specified size."""
    # Create image with blue background
    img = Image.new('RGB', (size, size), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Draw checkmark
    draw_checkmark(draw, size)

    return img


def main():
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    print("Generating Streaklet PWA icons...")

    for size in SIZES:
        filename = f"icon-{size}x{size}.png"
        filepath = os.path.join(script_dir, filename)

        icon = generate_icon(size)
        icon.save(filepath, 'PNG')

        print(f"✓ Generated {filename}")

    print(f"\nAll {len(SIZES)} icons generated successfully!")
    print(f"Icons saved to: {script_dir}")


if __name__ == "__main__":
    main()
