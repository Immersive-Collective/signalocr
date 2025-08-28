# app.py
import sys, os, re, csv
from typing import List
from CoreFoundation import (
    CFURLCreateFromFileSystemRepresentation,
    kCFAllocatorDefault,
)
from Quartz import (
    CGImageSourceCreateWithURL,
    CGImageSourceCreateImageAtIndex,
)
import Vision

# case-insensitive via lowercasing
SUPPORTED_EXTS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".gif", ".heic"}

URL_REGEX = re.compile(
    r"""(?xi)
    \b(
        (?:https?://|www\.)                # scheme or www
        [^\s<>"'()]+
        (?:\([^\s<>"']*\)[^\s<>"']*)*      # allow balanced parens inside
    )
    """
)

def list_images(in_dir: str) -> List[str]:
    in_dir = os.path.expanduser(in_dir)
    if not os.path.isdir(in_dir):
        return []
    files = []
    with os.scandir(in_dir) as it:
        for entry in it:
            if not entry.is_file():
                continue
            name = entry.name
            if name.startswith("."):
                continue
            ext = os.path.splitext(name)[1].lower()
            if ext in SUPPORTED_EXTS:
                files.append(entry.path)
    files.sort(key=lambda p: os.path.basename(p).lower())
    return files

def cgimage_from_path(path: str):
    url = CFURLCreateFromFileSystemRepresentation(
        kCFAllocatorDefault, path.encode(), len(path), False
    )
    src = CGImageSourceCreateWithURL(url, None)
    if not src:
        return None
    return CGImageSourceCreateImageAtIndex(src, 0, None)

def ocr_with_vision(path: str, langs: List[str]) -> str:
    cgimg = cgimage_from_path(path)
    if cgimg is None:
        return ""

    request = Vision.VNRecognizeTextRequest.alloc().init()
    request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
    request.setUsesLanguageCorrection_(True)
    # for long chats, accurate + line recognition improves order
    try:
        request.setRecognitionLanguages_(langs)
    except Exception:
        pass

    handler = Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(cgimg, None)
    ok, err = handler.performRequests_error_([request], None)
    if not ok:
        return ""

    results = list(request.results() or [])
    # sort top-to-bottom (y desc), then left-to-right (x asc)
    def _key(obs):
        bb = obs.boundingBox()
        return (-bb.origin.y, bb.origin.x)
    results.sort(key=_key)

    lines = []
    for obs in results:
        # VNRecognizedTextObservation -> take best candidate
        cands = obs.topCandidates_(1)
        if cands and len(cands) > 0:
            s = cands[0].string()
            if s:
                lines.append(s)
    return "\n".join(lines)

def extract_urls(text: str) -> List[str]:
    urls = []
    for m in URL_REGEX.finditer(text):
        u = m.group(1).rstrip(".,;:!)?]")
        if u.startswith("www."):
            u = "http://" + u
        urls.append(u)
    return urls

def write_text(path: str, content: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def ensure_dir(d: str):
    os.makedirs(d, exist_ok=True)

def run(in_dir: str, out_dir: str, lang_str: str):
    out_dir = os.path.expanduser(out_dir)
    ensure_dir(out_dir)

    imgs = list_images(in_dir)
    if not imgs:
        print("No images found.")
        return

    # Accept comma-separated BCP-47 language tags
    langs = [s.strip() for s in lang_str.split(",") if s.strip()] if lang_str else []
    if not langs:
        langs = ["en-US", "pl-PL"]

    all_sections = []
    all_urls = []
    txt_dir = os.path.join(out_dir, "txt")
    ensure_dir(txt_dir)

    for p in imgs:
        base = os.path.splitext(os.path.basename(p))[0]
        text = ocr_with_vision(p, langs)

        txt_path = os.path.join(txt_dir, base + ".txt")
        write_text(txt_path, text)

        urls = extract_urls(text)
        all_urls.extend([(base, u) for u in urls])

        section = f"## {base}\n\n```\n{text}\n```\n"
        if urls:
            section += "\n**Links detected:**\n" + "\n".join(f"- {u}" for u in urls) + "\n"
        all_sections.append(section)

        print(f"OCR: {os.path.basename(p)} -> {txt_path} ({len(text)} chars, {len(urls)} links)")

    combined_md = "# OCR Output\n\n" + "\n\n---\n\n".join(all_sections) + "\n"
    write_text(os.path.join(out_dir, "all_text.md"), combined_md)

    # also emit a flat .txt without markdown code fences
    plain_blocks = []
    for section in all_sections:
        lines = []
        for ln in section.splitlines():
            if ln.startswith("```") or ln.startswith("**Links detected:**"):
                continue
            lines.append(ln)
        plain_blocks.append("\n".join(lines).strip())
    write_text(os.path.join(out_dir, "all_text.txt"), ("\n\n---\n\n").join(plain_blocks) + "\n")

    dedup_urls = []
    seen = set()
    for _, u in all_urls:
        if u not in seen:
            seen.add(u)
            dedup_urls.append(u)
    write_text(os.path.join(out_dir, "urls.txt"), "\n".join(dedup_urls) + ("\n" if dedup_urls else ""))

    with open(os.path.join(out_dir, "urls.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["file", "url"])
        for fname, u in all_urls:
            w.writerow([fname, u])

    print(
        f"\nDone.\n"
        f"- Images: {len(imgs)}\n"
        f"- Per-image text: {txt_dir}\n"
        f"- Combined markdown: {os.path.join(out_dir,'all_text.md')}\n"
        f"- Combined text: {os.path.join(out_dir,'all_text.txt')}\n"
        f"- URLs (dedup): {os.path.join(out_dir,'urls.txt')}\n"
        f"- URL map CSV: {os.path.join(out_dir,'urls.csv')}"
    )

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print('Usage: python3 app.py <input_dir> <output_dir> "en-US,pl-PL"')
        sys.exit(1)
    in_dir = os.path.expanduser(sys.argv[1])
    out_dir = os.path.expanduser(sys.argv[2])
    lang_str = sys.argv[3] if len(sys.argv) >= 4 else "en-US,pl-PL"
    run(in_dir, out_dir, lang_str)
