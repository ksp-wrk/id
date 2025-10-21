import requests, base64, os, json
from datetime import datetime

PSD_FILE = "Sample_A4.psd"
IMG_DIR = "fingerprints"
OUTPUT_PSD = f"A4_{datetime.now().strftime('%Y%m%d_%H%M')}.psd"

images = [f for f in os.listdir(IMG_DIR)
          if f.lower().endswith(('.png', '.jpg', '.jpeg')) and "_used" not in f]
if not images:
    print("No new images found.")
    exit()

with open(PSD_FILE, "rb") as f:
    psd_data = base64.b64encode(f.read()).decode()

# --- JavaScript for Photopea ---
script_lines = [
    "var doc = app.open(app.openedDocuments[0]);",
    "var groups = doc.layers;",
    "for (var i = 0; i < groups.length; i++) { groups[i].visible = false; }",
]

for i, img_file in enumerate(images):
    last4 = ''.join([c for c in img_file if c.isdigit()])[-4:] or "0000"
    script_lines += [
        f"try {{",
        f'var bmp = doc.layers.getByName("bitmap"); bmp.replaceSmartObject("{IMG_DIR}/{img_file}");',
        f'var txt = doc.layers.getByName("0000"); txt.textItem.contents = "{last4}";',
        f"doc.layers[0].visible = true;",  # just ensure at least one visible
        f"}} catch(e) {{}}",
    ]

script_lines.append(f'app.activeDocument.saveToOE("{OUTPUT_PSD}", "psd");')
script = "\n".join(script_lines)

payload = {"files": {PSD_FILE: psd_data}, "script": script}

print("Sending to Photopea API...")
r = requests.post("https://www.photopea.com/api/", data=json.dumps(payload))

try:
    result = r.json()
except Exception as e:
    print("❌ Could not parse JSON response from Photopea.")
    print("Status:", r.status_code)
    print("Response text:", r.text[:300])
    exit()

if OUTPUT_PSD in result:
    output_data = base64.b64decode(result[OUTPUT_PSD])
    with open(OUTPUT_PSD, "wb") as f:
        f.write(output_data)
    print(f"✅ Saved: {OUTPUT_PSD}")
else:
    print("❌ No output file returned from Photopea.")
    print("Full response keys:", result.keys())
    exit()

# Rename used images
for f in images:
    src = os.path.join(IMG_DIR, f)
    root, ext = os.path.splitext(src)
    dst = root + "_used" + ext
    os.rename(src, dst)

print("✅ All used images renamed successfully.")
