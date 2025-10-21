import requests, base64, os, json
from datetime import datetime

# Configuration
PSD_FILE = "Sample_A4.psd"
IMG_DIR = "fingerprints"
OUTPUT_PSD = f"A4_{datetime.now().strftime('%Y%m%d_%H%M')}.psd"

# Collect all unused image files
images = [f for f in os.listdir(IMG_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg')) and "_used" not in f]
if not images:
    print("No new images found.")
    exit()

# Read PSD base64
with open(PSD_FILE, "rb") as f:
    psd_data = base64.b64encode(f.read()).decode()

# Build JavaScript script for Photopea
script_lines = [
    f'app.open("{PSD_FILE}");',
    'var doc = app.activeDocument;',
    'var groups = doc.layers;',
    'for (var i = 0; i < groups.length; i++) { groups[i].visible = false; }',  # সব group invisible
]

# Process each image
for i, img_file in enumerate(images):
    last4 = ''.join([c for c in img_file if c.isdigit()])[-4:] or "0000"
    script_lines += [
        f'var grp = doc.layers[{i}]; if (grp) grp.visible = true;',
        'try {',
        f'var bmp = doc.layers.getByName("bitmap"); bmp.replaceSmartObject("{IMG_DIR}/{img_file}");',
        f'var txt = doc.layers.getByName("0000"); txt.textItem.contents = "{last4}";',
        '} catch(e) {{}}',
    ]

# Save new PSD
script_lines.append(f'app.activeDocument.saveToOE("{OUTPUT_PSD}", "psd");')
script = "\n".join(script_lines)

# Prepare payload for Photopea API
payload = {
    "files": {PSD_FILE: psd_data},
    "script": script,
}

print("Sending to Photopea API...")
r = requests.post("https://www.photopea.com/api/", data=json.dumps(payload))
result = r.json()

if OUTPUT_PSD in result:
    output_data = base64.b64decode(result[OUTPUT_PSD])
    with open(OUTPUT_PSD, "wb") as f:
        f.write(output_data)
    print(f"✅ Saved: {OUTPUT_PSD}")
else:
    print("❌ Failed to generate output:", result)
    exit()

# Rename used images
for f in images:
    src = os.path.join(IMG_DIR, f)
    dst = os.path.join(IMG_DIR, f.replace(".png", "_used.png").replace(".jpg", "_used.jpg"))
    os.rename(src, dst)

print("✅ All used images renamed successfully.")
