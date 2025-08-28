# SignalOCR (macOS Vision OCR)

Batch-OCR Signal screenshots on macOS using Apple’s **Vision** framework, export them as searchable text, and automatically extract URLs.

## ✨ Features
- Supports `.png`, `.jpg`, `.jpeg`, `.tif`, `.tiff`, `.bmp`, `.gif`, `.heic`
- Runs OCR with macOS **Vision** (high accuracy, multi-language)
- Outputs:
  - Per-image `.txt` files
  - Combined `all_text.md` (with markdown formatting)
  - Combined `all_text.txt` (plain text)
  - `urls.txt` (deduplicated list of links)
  - `urls.csv` (mapping file → URL)

## 🛠 Requirements
- macOS (uses Quartz & Vision frameworks)
- Python 3.9+  
- Install dependencies:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  pip install pyobjc
```

## 📂 Project Structure

```
signalocr/
│── app.py          # main script
│── images/         # put your Signal screenshots here
│── output/         # results will be written here
│── README.md
```

## ▶️ Usage

Run the script with:

```bash
python3 app.py images output "en-US,pl-PL"
```

Arguments:

1. `images` – input directory with your screenshots
2. `output` – output directory for OCR results
3. `"en-US,pl-PL"` – comma-separated list of BCP-47 language codes
   (default: English + Polish)

Example:

```bash
python3 app.py ~/Documents/signalocr/images ~/Documents/signalocr/output "en-US,pl-PL"
```

## 📑 Example Output

After running:

* `output/txt/IMG_9101.txt` – OCR per screenshot
* `output/all_text.md` – combined markdown
* `output/all_text.txt` – combined plain text
* `output/urls.txt` – deduplicated URLs
* `output/urls.csv` – mapping of file → URL

Terminal log:

```
OCR: IMG_9101.PNG -> output/txt/IMG_9101.txt (245 chars, 2 links)
OCR: IMG_9102.PNG -> output/txt/IMG_9102.txt (532 chars, 0 links)

Done.
- Images: 83
- Per-image text: output/txt
- Combined markdown: output/all_text.md
- Combined text: output/all_text.txt
- URLs (dedup): output/urls.txt
- URL map CSV: output/urls.csv
```

## ⚡️ Why?

Signal does not provide an easy export for conversations. With this tool, you can:

* Archive chats in plain text
* Extract links from long conversations
* Make chats searchable and analyzable

---
