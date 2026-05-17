import threading
import webbrowser
import time
from pathlib import Path
from PIL import Image
from flask import Flask, request, render_template_string

# --- Image Processing Logic ---

def parse_aspect_ratio(ar_str):
    if not ar_str:
        return None
    try:
        w, h = map(float, ar_str.split(':'))
        return w / h
    except ValueError:
        raise ValueError("Aspect ratio must be 'W:H'")

def crop_to_aspect_ratio(image, target_ratio):
    orig_w, orig_h = image.size
    orig_ratio = orig_w / orig_h
    if abs(orig_ratio - target_ratio) < 0.01:
        return image
    if orig_ratio > target_ratio:
        new_w = int(orig_h * target_ratio)
        return image.crop(((orig_w - new_w) / 2, 0, (orig_w - new_w) / 2 + new_w, orig_h))
    else:
        new_h = int(orig_w / target_ratio)
        return image.crop((0, (orig_h - new_h) / 2, orig_w, (orig_h - new_h) / 2 + new_h))

def process_image(input_path, output_path, max_width, quality, target_ratio=None):
    with Image.open(input_path) as img:
        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            img = img.convert('RGBA')
        else:
            img = img.convert('RGB')
            
        if target_ratio:
            img = crop_to_aspect_ratio(img, target_ratio)
            
        orig_w, orig_h = img.size
        if orig_w > max_width:
            new_h = int((max_width / orig_w) * orig_h)
            img = img.resize((max_width, new_h), Image.Resampling.LANCZOS)
            
        img.save(output_path, 'WEBP', quality=quality)

# --- Web Interface Logic ---

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>NF Web Optimizer</title>
  <link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">
  <style>
    body { font-family: 'Space Mono', monospace; background-color: #070709; color: #eae6d9; margin: 0; padding: 3rem 1rem; }
    .container { max-width: 500px; margin: 0 auto; background: rgba(7, 7, 9, 0.75); padding: 2.5rem; border: 1px solid rgba(212, 175, 55, 0.2); box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
    h1 { color: #d4af37; text-align: center; text-transform: uppercase; font-size: 1.5rem; letter-spacing: 0.1em; margin-top: 0; margin-bottom: 2rem; }
    label { display: block; margin-top: 1.2rem; color: #00e5ff; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; }
    input[type="text"], input[type="number"] { width: 100%; padding: 0.75rem; margin-top: 0.5rem; background: #0a0a0d; border: 1px solid rgba(212, 175, 55, 0.2); color: white; font-family: 'Space Mono', monospace; box-sizing: border-box; outline: none; transition: border-color 0.3s; }
    input:focus { border-color: #00e5ff; }
    .help-text { font-size: 0.75rem; color: #8c8980; margin-top: 0.25rem; }
    button { margin-top: 2rem; width: 100%; padding: 1rem; background: transparent; color: #00e5ff; border: 1px solid #00e5ff; font-family: 'Space Mono', monospace; font-weight: bold; text-transform: uppercase; letter-spacing: 0.1em; cursor: pointer; transition: all 0.3s; }
    button:hover { background: rgba(0, 229, 255, 0.1); box-shadow: 0 0 15px rgba(0, 229, 255, 0.2); }
    .message { margin-bottom: 2rem; padding: 1rem; background: rgba(0, 229, 255, 0.1); border: 1px solid #00e5ff; text-align: center; color: #00e5ff; font-size: 0.9rem; }
  </style>
</head>
<body>
  <div class="container">
    <h1>NF Image Optimizer</h1>
    {% if message %}<div class="message">{{ message }}</div>{% endif %}
    <form method="POST">
      <label>Input Folder</label>
      <input type="text" name="input_dir" value="{{ input_dir or './Raw_Images' }}">
      
      <label>Output Folder</label>
      <input type="text" name="output_dir" value="{{ output_dir or './Web_Images' }}">
      
      <label>Max Width (px)</label>
      <input type="number" name="width" value="{{ width or 1200 }}">
      
      <label>Quality (1-100)</label>
      <input type="number" name="quality" value="{{ quality or 80 }}">
      
      <label>Aspect Ratio</label>
      <input type="text" name="aspect_ratio" value="{{ aspect_ratio or '' }}" placeholder="e.g., 16:9 or 1:1">
      <div class="help-text">Leave blank to keep original aspect ratio.</div>
      
      <button type="submit">Optimize Images</button>
    </form>
  </div>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    message = ""
    if request.method == "POST":
        in_dir, out_dir = request.form.get("input_dir"), request.form.get("output_dir")
        w, q, ar = int(request.form.get("width")), int(request.form.get("quality")), request.form.get("aspect_ratio")
        
        in_path, out_path = Path(in_dir), Path(out_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        t_ratio = parse_aspect_ratio(ar.strip()) if ar.strip() else None
        
        count = 0
        if in_path.exists() and in_path.is_dir():
            for f in in_path.iterdir():
                if f.is_file() and f.suffix.lower() in {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}:
                    process_image(f, out_path / f"{f.stem}.webp", w, q, t_ratio)
                    count += 1
            message = f"Success! {count} images optimized to {out_dir}."
        else:
            message = f"Error: '{in_dir}' does not exist."
            
    return render_template_string(HTML_TEMPLATE, message=message, **request.form)

if __name__ == "__main__":
    threading.Timer(1.25, lambda: webbrowser.open("http://127.0.0.1:5000")).start()
    app.run(port=5000, debug=False)