# Streaklet PWA Icons

This directory contains the app icons for the Streaklet Progressive Web App.

## Generating Icons

### Option 1: HTML Icon Generator (Recommended)

1. Open `generate-icons.html` in your browser
2. The icons will be automatically generated and displayed
3. Click "Download All Icons" to download all required sizes
4. Move the downloaded PNG files to this directory

### Option 2: Use an Online Tool

1. Visit [PWA Image Generator](https://www.pwabuilder.com/imageGenerator) or [RealFaviconGenerator](https://realfavicongenerator.net/)
2. Upload a source image (minimum 512x512px recommended)
3. Generate icons for all required sizes
4. Download and place them in this directory

### Option 3: Use ImageMagick (Command Line)

If you have ImageMagick installed:

```bash
# From a source image (e.g., source-icon.png)
for size in 72 96 128 144 152 192 384 512; do
  convert source-icon.png -resize ${size}x${size} icon-${size}x${size}.png
done
```

## Required Icon Sizes

The PWA manifest requires the following icon sizes:

- icon-72x72.png
- icon-96x96.png
- icon-128x128.png
- icon-144x144.png
- icon-152x152.png
- icon-192x192.png (maskable)
- icon-384x384.png
- icon-512x512.png (maskable)

## Icon Design Guidelines

- **Simple and recognizable**: The icon should be clear at all sizes
- **Brand colors**: Use Streaklet's blue theme (#3b82f6)
- **Maskable icons**: 192x192 and 512x512 should include safe zone (80% of canvas)
- **Contrast**: Ensure good contrast for visibility

## Current Design

The included generator creates a blue gradient background with a white checkmark, representing daily streak completion.
