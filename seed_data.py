import os
from PIL import Image, ImageDraw
from app.config import SAMPLE_IMG_DIR
from app.database import init_db, insert_item, list_items
from app.ml.vision import analyze_image
from app.ml.nlp import get_nlp_engine

def generate_sample_image(filename: str, bg_color: tuple, text: str, shape_type: str = "rect") -> str:
    """Generates a synthetic item image for CV testing and visual display."""
    os.makedirs(SAMPLE_IMG_DIR, exist_ok=True)
    filepath = os.path.join(SAMPLE_IMG_DIR, filename)
    
    # 400x300 image
    img = Image.new("RGB", (400, 300), color=(240, 242, 245))
    draw = ImageDraw.Draw(img)
    
    # Draw item shape
    if shape_type == "laptop":
        # Laptop base and screen
        draw.rounded_rectangle([60, 50, 340, 210], radius=10, fill=bg_color, outline=(40, 40, 40), width=3)
        draw.rounded_rectangle([75, 65, 325, 195], radius=5, fill=(30, 35, 45))
        # Screen logo / text
        draw.ellipse([185, 115, 215, 145], fill=(220, 220, 230))
        # Base
        draw.polygon([(40, 210), (360, 210), (380, 240), (20, 240)], fill=(bg_color[0]-20, bg_color[1]-20, bg_color[2]-20))
        draw.rectangle([160, 230, 240, 235], fill=(180, 180, 180)) # trackpad notch
    elif shape_type == "id_card":
        draw.rounded_rectangle([80, 40, 320, 250], radius=12, fill=bg_color, outline=(150, 150, 150), width=2)
        # Photo placeholder
        draw.rectangle([105, 70, 175, 150], fill=(200, 210, 225), outline=(100, 100, 100))
        draw.ellipse([125, 85, 155, 115], fill=(120, 140, 160)) # avatar
        # ID text lines
        draw.rectangle([190, 75, 300, 85], fill=(40, 50, 70))
        draw.rectangle([190, 95, 280, 103], fill=(80, 90, 110))
        draw.rectangle([190, 113, 260, 120], fill=(120, 130, 150))
        # Barcode at bottom
        for bx in range(105, 295, 6):
            draw.line([(bx, 210), (bx, 235)], fill=(30, 30, 30), width=3)
    elif shape_type == "bottle":
        # Bottle body
        draw.rounded_rectangle([140, 60, 260, 260], radius=20, fill=bg_color, outline=(30, 30, 30), width=3)
        # Cap
        draw.rectangle([165, 30, 235, 60], fill=(40, 40, 45))
        draw.ellipse([175, 15, 225, 35], fill=(70, 70, 75))
        # Logo band
        draw.rectangle([140, 140, 260, 170], fill=(bg_color[0]+30, bg_color[1]+30, bg_color[2]+30))
    elif shape_type == "headphones":
        # Headband
        draw.arc([100, 40, 300, 220], start=180, end=0, fill=bg_color, width=16)
        # Earcups
        draw.ellipse([80, 130, 140, 230], fill=bg_color, outline=(30, 30, 30), width=3)
        draw.ellipse([260, 130, 320, 230], fill=bg_color, outline=(30, 30, 30), width=3)
        draw.ellipse([95, 145, 125, 215], fill=(30, 30, 30))
        draw.ellipse([275, 145, 305, 215], fill=(30, 30, 30))
    elif shape_type == "calculator":
        draw.rounded_rectangle([110, 30, 290, 270], radius=12, fill=bg_color, outline=(20, 20, 20), width=3)
        # LCD display
        draw.rectangle([130, 50, 270, 95], fill=(175, 195, 170), outline=(50, 50, 50), width=2)
        # Solar panel
        draw.rectangle([210, 55, 260, 70], fill=(80, 50, 40))
        # Button matrix
        for row in range(5):
            for col in range(4):
                bx = 135 + col * 35
                by = 115 + row * 28
                draw.rectangle([bx, by, bx + 25, by + 18], fill=(60, 65, 75), outline=(30, 30, 30))
    elif shape_type == "backpack":
        draw.ellipse([100, 50, 300, 260], fill=bg_color, outline=(20, 20, 20), width=3)
        draw.rounded_rectangle([120, 140, 280, 240], radius=15, fill=(bg_color[0]-15, bg_color[1]-15, bg_color[2]-15), outline=(20, 20, 20), width=2)
        # Zipper lines
        draw.line([(135, 155), (265, 155)], fill=(180, 180, 180), width=3)
        draw.arc([160, 30, 240, 80], start=180, end=0, fill=(30, 30, 30), width=8) # handle
    else: # Default accessory / keys
        draw.rounded_rectangle([90, 60, 310, 230], radius=15, fill=bg_color, outline=(30, 30, 30), width=3)
        
    img.save(filepath, "PNG")
    return f"/static/sample_images/{filename}"

SAMPLE_ITEMS = [
    # 1. Matched Pair: MacBook
    {
        "title": "Lost Space Gray MacBook Pro 14",
        "description": "Lost my 14-inch Apple MacBook Pro in space gray color. Has a GitHub Octocat sticker and a yellow JS sticker on the lid. Left at Central Library 2nd floor desk 14.",
        "category": "Electronics & Gadgets",
        "location": "Central Library",
        "specific_spot": "2nd Floor Study Desk 14",
        "date_time": "2026-10-10 14:00",
        "item_type": "lost",
        "contact_name": "Alex Chen",
        "contact_email": "alex.chen@campus.edu",
        "contact_phone": "+1-555-0192",
        "brand": "Apple",
        "primary_color": "Space Gray",
        "secondary_color": "Black",
        "distinguishing_features": ["GitHub Octocat sticker", "yellow JS sticker"],
        "secret_verification_question": "What sticker is next to the GitHub Octocat?",
        "secret_verification_answer": "yellow JS sticker",
        "image_file": ("macbook_lost.png", (75, 75, 80), "MacBook Pro", "laptop")
    },
    {
        "title": "Found Space Gray Apple Laptop",
        "description": "Found a space gray Apple MacBook Pro with developer stickers on the top casing at Central Library study cubicle.",
        "category": "Electronics & Gadgets",
        "location": "Central Library",
        "specific_spot": "Library Quiet Zone",
        "date_time": "2026-10-10 15:15",
        "item_type": "found",
        "contact_name": "Library Security Desk",
        "contact_email": "security.library@campus.edu",
        "contact_phone": "+1-555-0100",
        "brand": "Apple",
        "primary_color": "Space Gray",
        "secondary_color": "Black",
        "distinguishing_features": ["developer stickers", "github sticker"],
        "secret_verification_question": "What is the lockscreen profile image or name?",
        "secret_verification_answer": "Alex Chen avatar",
        "image_file": ("macbook_found.png", (78, 78, 83), "Apple MacBook", "laptop")
    },
    
    # 2. Matched Pair: Student ID Card
    {
        "title": "Lost Student ID Card - Priya Sharma",
        "description": "Lost student identification card for Priya Sharma, Roll 2024EE088 in a blue campus lanyard.",
        "category": "ID Cards & Wallets",
        "location": "Tech Hub / Engineering Block",
        "specific_spot": "Near Embedded Systems Lab 304",
        "date_time": "2026-10-09 11:30",
        "item_type": "lost",
        "contact_name": "Priya Sharma",
        "contact_email": "priya.s@campus.edu",
        "brand": None,
        "primary_color": "Navy Blue",
        "distinguishing_features": ["blue campus lanyard", "student ID 2024EE088"],
        "secret_verification_question": "What is the last 3 digits of the student roll number?",
        "secret_verification_answer": "088",
        "image_file": ("id_lost.png", (220, 235, 245), "Student ID", "id_card")
    },
    {
        "title": "Found Student ID Card with Blue Lanyard",
        "description": "Student ID card found on the corridor bench outside engineering lab. Has blue neck ribbon lanyard.",
        "category": "ID Cards & Wallets",
        "location": "Tech Hub / Engineering Block",
        "specific_spot": "3rd floor corridor bench",
        "date_time": "2026-10-09 12:45",
        "item_type": "found",
        "contact_name": "Prof. Davis",
        "contact_email": "davis.eng@campus.edu",
        "brand": None,
        "primary_color": "Navy Blue",
        "distinguishing_features": ["blue neck ribbon lanyard"],
        "secret_verification_question": "What department is printed on the card?",
        "secret_verification_answer": "Electrical Engineering",
        "image_file": ("id_found.png", (225, 235, 250), "Found ID", "id_card")
    },

    # 3. Matched Pair: Hydro Flask Bottle
    {
        "title": "Lost Black Hydro Flask Water Bottle",
        "description": "Matte black insulated 32oz Hydro Flask with a small bottom dent and Yosemite national park sticker.",
        "category": "Bottles & Containers",
        "location": "Sports Complex & Gymnasium",
        "specific_spot": "Basketball Court Bleachers",
        "date_time": "2026-10-08 17:00",
        "item_type": "lost",
        "contact_name": "Marcus Vance",
        "contact_email": "marcus.v@campus.edu",
        "brand": "Hydro Flask",
        "primary_color": "Black",
        "distinguishing_features": ["bottom dent", "yosemite sticker"],
        "secret_verification_question": "What national park sticker is on the flask?",
        "secret_verification_answer": "Yosemite",
        "image_file": ("bottle_lost.png", (35, 35, 35), "Hydro Flask", "bottle")
    },
    {
        "title": "Found Matte Black Metal Bottle",
        "description": "Black vacuum water flask found by gym staff near court bleachers with a visible dent on the base.",
        "category": "Bottles & Containers",
        "location": "Sports Complex & Gymnasium",
        "specific_spot": "Court 1",
        "date_time": "2026-10-08 18:20",
        "item_type": "found",
        "contact_name": "Gym Front Desk",
        "contact_email": "gym.staff@campus.edu",
        "brand": "Hydro Flask",
        "primary_color": "Black",
        "distinguishing_features": ["dent on base"],
        "secret_verification_question": "What color is the silicone loop strap?",
        "secret_verification_answer": "black loop",
        "image_file": ("bottle_found.png", (38, 38, 40), "Water Flask", "bottle")
    },

    # 4. Matched Pair: Sony Headphones
    {
        "title": "Lost White Sony WH-1000XM4 Headphones",
        "description": "White/silver Sony wireless noise cancelling headphones in a grey zippered hard shell case.",
        "category": "Electronics & Gadgets",
        "location": "Student Center & Union",
        "specific_spot": "2nd Floor Lounge Sofa",
        "date_time": "2026-10-10 10:30",
        "item_type": "lost",
        "contact_name": "Sarah Lin",
        "contact_email": "sarah.lin@campus.edu",
        "brand": "Sony",
        "primary_color": "White",
        "secondary_color": "Silver",
        "distinguishing_features": ["grey zippered hard case"],
        "secret_verification_question": "What audio cable is stored inside the case zipper pocket?",
        "secret_verification_answer": "gold plated 3.5mm cable and airplane adapter",
        "image_file": ("sony_lost.png", (220, 220, 225), "Sony Headphones", "headphones")
    },
    {
        "title": "Found Sony Wireless Over-Ear Headphones",
        "description": "Silver/white Sony headphones left on sofa in student union lounge, stored in protective case.",
        "category": "Electronics & Gadgets",
        "location": "Student Center & Union",
        "specific_spot": "Lounge Area",
        "date_time": "2026-10-10 11:45",
        "item_type": "found",
        "contact_name": "Union Info Desk",
        "contact_email": "union.info@campus.edu",
        "brand": "Sony",
        "primary_color": "White",
        "secondary_color": "Silver",
        "distinguishing_features": ["protective case"],
        "secret_verification_question": "What is inside the case mesh pocket?",
        "secret_verification_answer": "airplane adapter and auxiliary cord",
        "image_file": ("sony_found.png", (215, 215, 220), "Sony Headset", "headphones")
    },

    # 5. Casio Scientific Calculator
    {
        "title": "Lost Casio fx-991CW Calculator",
        "description": "Black Casio scientific calculator with initials 'RK' scratched on back slider casing.",
        "category": "Electronics & Gadgets",
        "location": "Science Hall",
        "specific_spot": "Room 204 Physics",
        "date_time": "2026-10-09 14:00",
        "item_type": "lost",
        "contact_name": "Rahul Kapoor",
        "contact_email": "rahul.k@campus.edu",
        "brand": "Casio",
        "primary_color": "Black",
        "distinguishing_features": ["initials RK on back"],
        "secret_verification_question": "What initials are engraved on the back cover?",
        "secret_verification_answer": "RK",
        "image_file": ("casio_lost.png", (45, 45, 50), "Casio fx-991CW", "calculator")
    },
    {
        "title": "Found Black Scientific Calculator",
        "description": "Black Casio engineering calculator found on physics lecture room table.",
        "category": "Electronics & Gadgets",
        "location": "Science Hall",
        "specific_spot": "Physics Lecture 204",
        "date_time": "2026-10-09 15:30",
        "item_type": "found",
        "contact_name": "Physics TA",
        "contact_email": "ta.physics@campus.edu",
        "brand": "Casio",
        "primary_color": "Black",
        "distinguishing_features": ["markings on back cover"],
        "secret_verification_question": "What two letters are on the back casing?",
        "secret_verification_answer": "RK",
        "image_file": ("casio_found.png", (40, 40, 45), "Casio Calculator", "calculator")
    },

    # 6. Additional Unclaimed & Active Campus Items
    {
        "title": "Lost North Face Black Recon Backpack",
        "description": "Heavy black nylon backpack with laptop compartment, containing biology textbooks and blue pencil case.",
        "category": "Bags & Backpacks",
        "location": "North Hostels & Dormitories",
        "specific_spot": "Dorm B Common Room",
        "date_time": "2026-10-10 18:00",
        "item_type": "lost",
        "contact_name": "David Miller",
        "contact_email": "david.m@campus.edu",
        "brand": "North Face",
        "primary_color": "Black",
        "distinguishing_features": ["biology textbook inside", "blue pencil case"],
        "secret_verification_question": "What textbook is in the main compartment?",
        "secret_verification_answer": "Campbell Biology",
        "image_file": ("backpack_lost.png", (30, 30, 35), "North Face Bag", "backpack")
    },
    {
        "title": "Found Brown Leather Fossil Wallet",
        "description": "Men's brown bi-fold wallet left at the dining hall checkout tray. Contains multiple cards.",
        "category": "ID Cards & Wallets",
        "location": "Campus Cafeteria & Food Court",
        "specific_spot": "Register 2",
        "date_time": "2026-10-10 13:30",
        "item_type": "found",
        "contact_name": "Dining Staff",
        "contact_email": "dining.staff@campus.edu",
        "brand": "Fossil",
        "primary_color": "Brown",
        "distinguishing_features": ["cards inside"],
        "secret_verification_question": "What is the bank name on the primary debit card?",
        "secret_verification_answer": "Chase",
        "image_file": ("wallet_found.png", (110, 65, 40), "Leather Wallet", "id_card")
    },
    {
        "title": "Found Keychain with Red Honda Fob",
        "description": "Set of 3 keys with a rubber Honda wing keychain and a brass locker key found near hostel bicycle stand.",
        "category": "Keys & Keychains",
        "location": "North Hostels & Dormitories",
        "specific_spot": "Hostel Bike Stand Block A",
        "date_time": "2026-10-09 19:15",
        "item_type": "found",
        "contact_name": "Hostel Warden Office",
        "contact_email": "warden.north@campus.edu",
        "brand": None,
        "primary_color": "Crimson Red",
        "distinguishing_features": ["Honda wing keychain", "brass locker key"],
        "secret_verification_question": "How many total keys are on the ring?",
        "secret_verification_answer": "3 keys",
        "image_file": ("keys_found.png", (180, 25, 35), "Keys", "rect")
    }
]

def seed_database():
    print("Initializing database...")
    init_db()
    
    existing = list_items(limit=10)
    if len(existing) >= len(SAMPLE_ITEMS):
        print(f"Database already populated with {len(existing)} items.")
        return

    print("Generating sample campus visual items & extracting multimodal features...")
    nlp = get_nlp_engine()
    
    for item in SAMPLE_ITEMS:
        # Generate image asset
        img_fn, bg_col, label, shape = item["image_file"]
        img_url = generate_sample_image(img_fn, bg_col, label, shape)
        
        # Analyze image with CV pipeline
        abs_img_path = os.path.join(SAMPLE_IMG_DIR, img_fn)
        vis_features = analyze_image(abs_img_path)
        
        item_data = {
            "title": item["title"],
            "description": item["description"],
            "category": item["category"],
            "location": item["location"],
            "specific_spot": item["specific_spot"],
            "date_time": item["date_time"],
            "item_type": item["item_type"],
            "contact_name": item["contact_name"],
            "contact_email": item["contact_email"],
            "contact_phone": item.get("contact_phone"),
            "brand": item.get("brand"),
            "primary_color": item.get("primary_color") or vis_features.get("primary_color"),
            "secondary_color": item.get("secondary_color") or vis_features.get("secondary_color"),
            "distinguishing_features": item.get("distinguishing_features", []),
            "secret_verification_question": item.get("secret_verification_question"),
            "secret_verification_answer": item.get("secret_verification_answer"),
            "image_url": img_url,
            "status": "active",
            "vision_embedding": vis_features,
            "vision_features_extracted": 1,
            "nlp_features_extracted": 1,
            "created_at": item["date_time"]
        }
        
        insert_item(item_data)
        
    print(f"Successfully seeded {len(SAMPLE_ITEMS)} campus lost and found items!")

if __name__ == "__main__":
    seed_database()
