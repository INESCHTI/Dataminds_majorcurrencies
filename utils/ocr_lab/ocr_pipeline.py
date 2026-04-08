from __future__ import annotations

from dataclasses import dataclass
import json
import re
from pathlib import Path
from typing import Literal

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

try:
    import pytesseract
    from pytesseract import Output

    TESSERACT_AVAILABLE = True
except Exception:
    pytesseract = None
    Output = None
    TESSERACT_AVAILABLE = False

try:
    import easyocr

    EASYOCR_AVAILABLE = True
except Exception:
    easyocr = None
    EASYOCR_AVAILABLE = False


Mode = Literal["free", "login", "alnum"]
Engine = Literal["tesseract", "easyocr", "auto"]


@dataclass
class OcrResult:
    text: str
    confidence: float
    engine: str
    variant: str


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def _clean_for_mode(text: str, mode: Mode) -> str:
    t = _normalize_whitespace(text)
    if mode == "free":
        return t
    if mode == "alnum":
        return re.sub(r"[^A-Za-z0-9._\-@]", "", t)

    # mode=login: keep allowed login/email symbols only.
    return re.sub(r"[^A-Za-z0-9._\-@]", "", t)


def _disambiguate_common_ocr_confusions(text: str, mode: Mode) -> str:
    # Conservative replacements for login-like fields.
    if mode == "free":
        return text

    out = text
    replacements = {
        "|": "I",
        "l": "I",
        "O": "0",
        "o": "0",
        "S": "5",
    }

    # For email-like strings, preserve letters around '@'.
    if "@" in out:
        replacements = {
            "|": "l",
            "0": "o",
        }

    for src, dst in replacements.items():
        out = out.replace(src, dst)
    return out


def _variants(img: Image.Image) -> dict[str, Image.Image]:
    gray = ImageOps.grayscale(img)
    sharp = gray.filter(ImageFilter.SHARPEN)
    contrast = ImageEnhance.Contrast(gray).enhance(2.0)
    bw = contrast.point(lambda p: 255 if p > 150 else 0)

    return {
        "gray": gray,
        "sharp": sharp,
        "high_contrast": contrast,
        "binary": bw,
    }


def _score_text_quality(text: str, confidence: float, mode: Mode) -> float:
    clean = _normalize_whitespace(text)
    if not clean:
        return 0.0

    bonus = 0.0
    if mode == "login":
        if re.match(r"^[A-Za-z0-9._\-@]+$", clean):
            bonus += 0.08
        if len(clean) >= 4:
            bonus += 0.05
    elif mode == "alnum":
        if re.match(r"^[A-Za-z0-9._\-]+$", clean):
            bonus += 0.08

    length_factor = min(1.0, len(clean) / 16.0)
    return max(0.0, min(1.0, confidence * 0.75 + bonus + length_factor * 0.1))


def _run_tesseract(img: Image.Image, mode: Mode) -> tuple[str, float]:
    if not TESSERACT_AVAILABLE:
        return "", 0.0

    config = "--oem 3 --psm 7"
    if mode in {"login", "alnum"}:
        config += " -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._-@"

    data = pytesseract.image_to_data(img, config=config, output_type=Output.DICT)
    words = []
    confs = []

    for txt, conf in zip(data.get("text", []), data.get("conf", [])):
        t = str(txt).strip()
        if not t:
            continue
        try:
            c = float(conf)
        except Exception:
            c = -1.0
        if c >= 0:
            confs.append(c / 100.0)
        words.append(t)

    text = " ".join(words).strip()
    confidence = sum(confs) / len(confs) if confs else 0.0
    return text, confidence


def _run_easyocr(img: Image.Image, mode: Mode) -> tuple[str, float]:
    if not EASYOCR_AVAILABLE:
        return "", 0.0

    reader = easyocr.Reader(["en"], gpu=False)
    lines = reader.readtext(img)
    tokens = []
    confs = []
    for _, txt, conf in lines:
        if not txt:
            continue
        tokens.append(str(txt))
        confs.append(float(conf))

    text = " ".join(tokens).strip()
    confidence = sum(confs) / len(confs) if confs else 0.0
    return text, confidence


def extract_text(image_path: str | Path, mode: Mode = "free", engine: Engine = "auto") -> dict:
    p = Path(image_path)
    if not p.exists():
        raise FileNotFoundError(f"Image not found: {p}")

    img = Image.open(p)
    variants = _variants(img)

    engines: list[Engine]
    if engine == "auto":
        engines = ["tesseract", "easyocr"]
    else:
        engines = [engine]

    candidates: list[OcrResult] = []

    for eng in engines:
        for name, vimg in variants.items():
            if eng == "tesseract":
                text, conf = _run_tesseract(vimg, mode)
            elif eng == "easyocr":
                text, conf = _run_easyocr(vimg, mode)
            else:
                text, conf = "", 0.0

            cleaned = _clean_for_mode(text, mode)
            cleaned = _disambiguate_common_ocr_confusions(cleaned, mode)
            q = _score_text_quality(cleaned, conf, mode)
            if cleaned:
                candidates.append(OcrResult(text=cleaned, confidence=q, engine=eng, variant=name))

    if not candidates:
        return {
            "success": False,
            "text": "",
            "confidence": 0.0,
            "mode": mode,
            "warning": "No OCR text extracted. Check engine installation or image quality.",
            "candidates": [],
        }

    best = sorted(candidates, key=lambda x: x.confidence, reverse=True)[0]
    warnings = []
    if best.confidence < 0.45:
        warnings.append("Low confidence OCR: manual verification recommended")

    return {
        "success": True,
        "text": best.text,
        "confidence": round(best.confidence, 4),
        "engine": best.engine,
        "variant": best.variant,
        "mode": mode,
        "warnings": warnings,
        "candidates": [
            {
                "text": c.text,
                "confidence": round(c.confidence, 4),
                "engine": c.engine,
                "variant": c.variant,
            }
            for c in sorted(candidates, key=lambda x: x.confidence, reverse=True)[:6]
        ],
    }


def pretty_json(payload: dict) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=True)
