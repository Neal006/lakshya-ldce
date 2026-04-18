FMCG_CORRECTIONS = {
    "parley g": "Parle-G",
    "parle g": "Parle-G",
    "parleji": "Parle-G",
    "curry cure": "Kurkure",
    "kurkure": "Kurkure",
    "maggy": "Maggi",
    "maggi": "Maggi",
    "surf excell": "Surf Excel",
    "surf excel": "Surf Excel",
    "wheel powder": "Wheel",
    "rim power": "Rin",
    "rin power": "Rin",
    "vim dishwash": "Vim",
    "vim liquid": "Vim",
    "dettol soap": "Dettol",
    "lifeboy": "Lifebuoy",
    "lux soap": "Lux",
    "fair and lovely": "Glow & Lovely",
    "fair & lovely": "Glow & Lovely",
    "dairy milk": "Dairy Milk",
    "5 star chocolate": "5 Star",
    "kit kat": "KitKat",
    "red label": "Red Label",
    "green label": "Green Label",
    "tata tea": "Tata Tea",
    "bru coffee": "Bru",
    "nescafe": "Nescafé",
    "moov cream": "Moov",
    "iodex": "Iodex",
    "volini": "Volini",
    "vicks": "Vicks",
    "colgate": "Colgate",
    "pepsodent": "Pepsodent",
    "close up": "Closeup",
    "clinic plus": "Clinic Plus",
    "head and shoulders": "Head & Shoulders",
    "sunsilk": "Sunsilk",
    "dove soap": "Dove",
    "ponds": "Pond's",
    "nyka": "Nykaa",
    "bournvita": "Bournvita",
    "horlicks": "Horlicks",
    "complan": "Complan",
    "boost": "Boost",
    "amul": "Amul",
    "mother dairy": "Mother Dairy",
}


def apply_fmcg_corrections(text: str) -> str:
    """Apply FMCG domain corrections to transcribed text."""
    import re
    corrected = text
    for wrong, right in FMCG_CORRECTIONS.items():
        pattern = re.compile(re.escape(wrong), re.IGNORECASE)
        corrected = pattern.sub(right, corrected)
    return corrected