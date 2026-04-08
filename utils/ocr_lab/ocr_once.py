from __future__ import annotations

import argparse

from .ocr_pipeline import extract_text, pretty_json


def main():
    parser = argparse.ArgumentParser(description="Run OCR on a single image with robust interpretation.")
    parser.add_argument("--image", required=True, help="Path to image file")
    parser.add_argument("--mode", choices=["free", "login", "alnum"], default="free")
    parser.add_argument("--engine", choices=["auto", "tesseract", "easyocr"], default="auto")
    args = parser.parse_args()

    result = extract_text(image_path=args.image, mode=args.mode, engine=args.engine)
    print(pretty_json(result))


if __name__ == "__main__":
    main()
