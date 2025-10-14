import fitz  # PyMuPDF
import re
import os
import pandas as pd

# ===== CONFIG =====
input_folder = "./nid"          # PDFs folder
output_excel = "./nid/output.xlsx"
portraits_folder = "./portraits"
fingerprints_folder = "./fingerprints"

os.makedirs(portraits_folder, exist_ok=True)
os.makedirs(fingerprints_folder, exist_ok=True)
# ==================

patterns = {
    "National ID": re.compile(r"National\s*ID\s*[: ]*\s*([0-9A-Z]+)", re.IGNORECASE),
    "PIN": re.compile(r"Pin\s*[: ]*\s*([0-9]+)", re.IGNORECASE),
    "Date of Birth": re.compile(r"Date\s*of\s*Birth\s*[: ]*\s*([0-9]{4}-[0-9]{2}-[0-9]{2})", re.IGNORECASE),
    "Name (English)": re.compile(r"Name\s*\(English\)\s*[: ]*([A-Z \-\.]+)", re.IGNORECASE),
    "Birth Registration No": re.compile(r"Birth\s*Registration\s*No\s*[: ]*\s*([0-9]+)", re.IGNORECASE),
}

# Load existing Excel if exists
existing_records = {}
if os.path.exists(output_excel):
    df_existing = pd.read_excel(output_excel)
    for idx, row in df_existing.iterrows():
        existing_records[row["File Name"]] = row.to_dict()

results = []

for filename in sorted(os.listdir(input_folder)):
    if not filename.lower().endswith(".pdf"):
        continue

    # Skip already processed PDFs
    if filename in existing_records:
        print(f"⏭ Skipping {filename}, already processed")
        results.append(existing_records[filename])
        continue

    pdf_path = os.path.join(input_folder, filename)
    print(f"🔍 Processing {filename}")

    record = {
        "File Name": filename,
        "National ID": "",
        "PIN": "",
        "Date of Birth": "",
        "Name (English)": "",
        "Birth Registration No": "",
        "Portrait Image": "",
        "Fingerprint Image": "",
    }

    pdf_basename = os.path.splitext(filename)[0]

    with fitz.open(pdf_path) as doc:
        text = ""
        for page in doc:
            text += page.get_text("text")

        # Extract text fields
        for key, pattern in patterns.items():
            m = pattern.search(text)
            if m:
                record[key] = m.group(1).strip()

        # Extract images only if missing
        images = []
        for page in doc:
            for img in page.get_images(full=True):
                xref = img[0]
                base_image = doc.extract_image(xref)
                img_data = base_image["image"]
                ext = base_image["ext"]

                # Decide folder
                if len(images) == 0:
                    folder = portraits_folder
                else:
                    folder = fingerprints_folder

                img_name = f"{pdf_basename}_{len(images)+1}.{ext}"
                img_path = os.path.join(folder, img_name)

                if not os.path.exists(img_path):
                    with open(img_path, "wb") as f:
                        f.write(img_data)
                images.append(img_path)

        # Assign first to portrait, second to fingerprint
        if len(images) >= 1:
            record["Portrait Image"] = os.path.basename(images[0])
        if len(images) >= 2:
            record["Fingerprint Image"] = os.path.basename(images[1])

    results.append(record)

# Save all records to Excel
df = pd.DataFrame(results, columns=[
    "File Name", "National ID", "PIN", "Date of Birth",
    "Name (English)", "Birth Registration No",
    "Portrait Image", "Fingerprint Image"
])
df.to_excel(output_excel, index=False)

print("\n✅ Done!")
print(f"Excel saved: {output_excel}")
print(f"Portraits folder: {portraits_folder}")
print(f"Fingerprints folder: {fingerprints_folder}")
