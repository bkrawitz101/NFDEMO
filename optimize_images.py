import argparse
from pathlib import Path
from PIL import Image

def parse_aspect_ratio(ar_str):
    """Parses a string like '16:9' into a float ratio."""
    if not ar_str:
        return None
    try:
        w, h = map(float, ar_str.split(':'))
        return w / h
    except ValueError:
        raise ValueError("Aspect ratio must be in the format 'W:H', e.g., '16:9'")

def crop_to_aspect_ratio(image, target_ratio):
    """Center-crops an image to the target aspect ratio."""
    orig_w, orig_h = image.size
    orig_ratio = orig_w / orig_h

    if abs(orig_ratio - target_ratio) < 0.01:
        return image  # Already at the correct ratio

    if orig_ratio > target_ratio:
        # Image is wider than target ratio, crop the width (left/right)
        new_w = int(orig_h * target_ratio)
        left = (orig_w - new_w) / 2
        top = 0
        right = left + new_w
        bottom = orig_h
    else:
        # Image is taller than target ratio, crop the height (top/bottom)
        new_h = int(orig_w / target_ratio)
        left = 0
        top = (orig_h - new_h) / 2
        right = orig_w
        bottom = top + new_h

    return image.crop((left, top, right, bottom))

def process_image(input_path, output_path, max_width, quality, target_ratio=None):
    try:
        with Image.open(input_path) as img:
            # Convert to RGBA first if it has transparency, otherwise RGB
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                img = img.convert('RGBA')
            else:
                img = img.convert('RGB')

            # 1. Apply aspect ratio crop if specified
            if target_ratio:
                img = crop_to_aspect_ratio(img, target_ratio)

            # 2. Resize to max width
            orig_w, orig_h = img.size
            if orig_w > max_width:
                new_h = int((max_width / orig_w) * orig_h)
                img = img.resize((max_width, new_h), Image.Resampling.LANCZOS)

            # 3. Save as WebP
            img.save(output_path, 'WEBP', quality=quality)
            print(f"Optimized: {input_path.name} -> {output_path.name}")
            
    except Exception as e:
        print(f"Error processing {input_path.name}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Optimize images to WebP format for the web.")
    parser.add_argument('-i', '--input', default='./Media', help='Input directory (default: ./Media)')
    parser.add_argument('-o', '--output', default='./Media/optimized', help='Output directory (default: ./Media/optimized)')
    parser.add_argument('-w', '--width', type=int, default=1200, help='Max width of optimized image (default: 1200)')
    parser.add_argument('-q', '--quality', type=int, default=80, help='WebP compression quality 1-100 (default: 80)')
    parser.add_argument('-a', '--aspect_ratio', type=str, help='Force a specific aspect ratio (e.g. 16:9, 1:1). Omit to keep original aspect ratio.')

    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    target_ratio = parse_aspect_ratio(args.aspect_ratio)
    
    # Supported input formats
    valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}

    for file_path in input_dir.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in valid_extensions:
            output_path = output_dir / f"{file_path.stem}.webp"
            process_image(file_path, output_path, args.width, args.quality, target_ratio)

if __name__ == "__main__":
    main()