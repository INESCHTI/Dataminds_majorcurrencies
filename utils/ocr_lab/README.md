# OCR Lab

OCR robuste pour extraction de texte, avec focus sur interpretation correcte.

## Cas d'usage
- Lecture de texte depuis captures/ecrans.
- Extraction de champs login (mode `login`).
- Extraction alphanumerique stricte (mode `alnum`).

## Pourquoi l'interpretation est critique
L'OCR confond souvent certains caracteres:
- `0` vs `O`
- `1` vs `I` vs `l`
- `5` vs `S`

Le pipeline applique:
1. pretraitements multiples (grayscale, sharpen, contrast, binaire),
2. execution multi-approches OCR (tesseract + easyocr optionnel),
3. score de confiance + regles de qualite,
4. normalisation des caracteres ambigus selon le mode.

## Installation
Ajouter dependances Python:
- `Pillow`
- `pytesseract`
- `easyocr` (optionnel)

Note: `pytesseract` requiert aussi le binaire Tesseract installe sur la machine.

## Usage
Depuis la racine du projet:

```bash
python -m utils.ocr_lab.ocr_once --image path/to/image.png --mode login --engine auto
```

Resultat:
- texte final,
- score de confiance,
- moteur et variante gagnante,
- top candidats,
- warnings si confiance faible.

## Recommandation login
Toujours verifier humainement si `confidence < 0.45`.
