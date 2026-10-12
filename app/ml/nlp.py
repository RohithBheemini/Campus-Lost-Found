import re
from typing import Dict, Any, List, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Comprehensive campus brand dictionary
CAMPUS_BRANDS = [
    # Computing & Tech
    "apple", "macbook", "ipad", "iphone", "airpods", "dell", "xps", "alienware",
    "hp", "pavilion", "envy", "spectre", "lenovo", "thinkpad", "ideapad", "yoga",
    "asus", "rog", "zenbook", "acer", "swift", "aspire", "samsung", "galaxy",
    "sony", "bose", "jbl", "sennheiser", "anker", "boat", "noise", "logitech",
    "casio", "texas instruments", "kindle",
    # Bags & Bottles
    "hydro flask", "hydroflask", "milton", "tupperware", "klean kanteen",
    "jansport", "north face", "wildcraft", "nike", "adidas", "puma", "under armour",
    "american tourister", "skybags",
    # Watches & Accessories
    "fastrack", "fossil", "titan", "casio", "timex", "ray-ban", "oakley"
]

# Color keywords mapped to canonical names
COLOR_KEYWORDS = {
    "space gray": "Space Gray",
    "space grey": "Space Gray",
    "gray": "Space Gray",
    "grey": "Space Gray",
    "silver": "Silver",
    "metallic": "Silver",
    "black": "Black",
    "matte black": "Black",
    "white": "White",
    "blue": "Navy Blue",
    "navy": "Navy Blue",
    "navy blue": "Navy Blue",
    "royal blue": "Royal Blue",
    "sky blue": "Sky Blue",
    "cyan": "Sky Blue",
    "red": "Crimson Red",
    "crimson": "Crimson Red",
    "maroon": "Maroon / Burgundy",
    "burgundy": "Maroon / Burgundy",
    "green": "Forest Green",
    "dark green": "Forest Green",
    "lime": "Lime Green",
    "yellow": "Gold / Yellow",
    "gold": "Gold / Yellow",
    "golden": "Gold / Yellow",
    "orange": "Orange",
    "purple": "Purple",
    "violet": "Purple",
    "pink": "Pink",
    "rose gold": "Pink",
    "brown": "Brown",
    "tan": "Brown",
}

# Category rules
CATEGORY_KEYWORDS = {
    "Electronics & Gadgets": [
        "laptop", "macbook", "computer", "notebook", "charger", "adapter", "phone",
        "smartphone", "iphone", "android", "tablet", "ipad", "headphones", "earphones",
        "airpods", "earbuds", "calculator", "mouse", "keyboard", "cable", "usb",
        "pendrive", "hard drive", "smartwatch", "watch", "power bank", "kindle"
    ],
    "ID Cards & Wallets": [
        "id card", "identity card", "student id", "campus id", "badge", "lanyard",
        "wallet", "purse", "money clip", "driver license", "library card", "metro card",
        "credit card", "debit card", "atm card"
    ],
    "Books & Stationery": [
        "book", "textbook", "notebook", "diary", "journal", "binder", "folder",
        "pen", "pencil", "pencil case", "highlighter", "calculator", "notes", "spiral", "novel"
    ],
    "Bags & Backpacks": [
        "bag", "backpack", "tote bag", "duffel", "laptop bag", "pouch", "sack",
        "briefcase", "messenger bag", "rucksack"
    ],
    "Personal Accessories": [
        "glasses", "spectacles", "sunglasses", "shades", "umbrella", "ring", "chain",
        "bracelet", "necklace", "earrings", "helmet", "cap", "hat", "muffler"
    ],
    "Keys & Keychains": [
        "key", "keys", "keychain", "bike key", "room key", "car key", "fob", "ring of keys"
    ],
    "Clothing & Wearables": [
        "jacket", "hoodie", "sweater", "coat", "scarf", "gloves", "cap", "t-shirt",
        "jersey", "sweatshirt", "shoes"
    ],
    "Bottles & Containers": [
        "bottle", "water bottle", "flask", "tumbler", "sipper", "mug", "thermos",
        "lunch box", "container"
    ]
}

FEATURE_TRIGGERS = [
    r"sticker[s]?(?:\s+of|\s+on|\s+with)?\s+([a-zA-Z0-9\s\-]+)",
    r"scratched?\s+([a-zA-Z0-9\s\-]+)",
    r"dent(?:ed)?\s+([a-zA-Z0-9\s\-]+)",
    r"cracked?\s+([a-zA-Z0-9\s\-]+)",
    r"keychain(?:\s+with)?\s+([a-zA-Z0-9\s\-]+)",
    r"case(?:\s+with)?\s+([a-zA-Z0-9\s\-]+)",
    r"engrav(?:ed|ing)?\s+([a-zA-Z0-9\s\-]+)",
    r"initials?\s+([a-zA-Z0-9\s\-]+)",
    r"lanyard(?:\s+with)?\s+([a-zA-Z0-9\s\-]+)"
]

class NLPEngine:
    def __init__(self):
        # Character subword n-gram vectorizer (3 to 5-grams) for typo resilience without unigram noise
        self.vectorizer = TfidfVectorizer(
            ngram_range=(3, 5),
            analyzer="char_wb",
            min_df=1,
            sublinear_tf=True
        )

    def extract_brand(self, text: str) -> Optional[str]:
        text_lower = text.lower()
        for brand in CAMPUS_BRANDS:
            # Word boundary check
            pattern = r"\b" + re.escape(brand) + r"\b"
            if re.search(pattern, text_lower):
                return brand.title()
        return None

    def extract_colors(self, text: str) -> List[str]:
        text_lower = text.lower()
        found = []
        # Sort keys longest first so "space gray" matches before "gray"
        for kw, canonical in sorted(COLOR_KEYWORDS.items(), key=lambda x: len(x[0]), reverse=True):
            pattern = r"\b" + re.escape(kw) + r"\b"
            if re.search(pattern, text_lower) and canonical not in found:
                found.append(canonical)
        return found

    def infer_category(self, text: str, fallback: str = "Other") -> str:
        text_lower = text.lower()
        scores = {}
        for cat, keywords in CATEGORY_KEYWORDS.items():
            count = 0
            for kw in keywords:
                if re.search(r"\b" + re.escape(kw) + r"\b", text_lower):
                    count += 1
            if count > 0:
                scores[cat] = count
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        return fallback

    def extract_distinguishing_features(self, text: str) -> List[str]:
        features = []
        text_lower = text.lower()
        for pattern in FEATURE_TRIGGERS:
            matches = re.finditer(pattern, text_lower)
            for m in matches:
                feat = m.group(0).strip()
                if len(feat) > 3 and feat not in features:
                    features.append(feat)
                    
        # Also check for specific notable terms
        keywords = ["sticker", "cracked", "scratched", "initials", "dent", "lanyard", "keychain", "engraved"]
        for kw in keywords:
            if kw in text_lower and not any(kw in f for f in features):
                # Grab surrounding phrase
                sub_pattern = rf"([^,\.;]*{kw}[^,\.;]*)"
                sub_match = re.search(sub_pattern, text_lower)
                if sub_match:
                    features.append(sub_match.group(1).strip())
                    
        return features[:5]

    def extract_attributes(self, text: str, title: str = "") -> Dict[str, Any]:
        combined = f"{title} {text}".strip()
        brand = self.extract_brand(combined)
        colors = self.extract_colors(combined)
        category = self.infer_category(combined)
        features = self.extract_distinguishing_features(combined)
        
        return {
            "brand": brand,
            "primary_color": colors[0] if colors else None,
            "secondary_color": colors[1] if len(colors) > 1 else None,
            "category": category,
            "distinguishing_features": features,
            "extracted_colors": colors
        }

    def compute_text_similarity(self, text1: str, text2: str) -> float:
        """Computes TF-IDF char n-gram cosine similarity between two texts."""
        if not text1.strip() or not text2.strip():
            return 0.0
        try:
            tfidf_mat = self.vectorizer.fit_transform([text1, text2])
            sim = float(cosine_similarity(tfidf_mat[0:1], tfidf_mat[1:2])[0][0])
            return max(0.0, min(1.0, sim))
        except Exception:
            # Fallback simple Jaccard word similarity
            words1 = set(re.findall(r"\w+", text1.lower()))
            words2 = set(re.findall(r"\w+", text2.lower()))
            if not words1 or not words2:
                return 0.0
            intersection = len(words1.intersection(words2))
            union = len(words1.union(words2))
            return float(intersection / union)

_nlp_engine = None

def get_nlp_engine() -> NLPEngine:
    global _nlp_engine
    if _nlp_engine is None:
        _nlp_engine = NLPEngine()
    return _nlp_engine
