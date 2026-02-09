import json
import os
from PIL import Image

def analyze_sizes():
    try:
        with open('assets/json/items_db.json', 'r', encoding='utf-8') as f:
            db = json.load(f)
    except Exception as e:
        print(f"Error loading DB: {e}")
        return

    sizes = {'Small': [], 'Medium': [], 'Large': []}
    
    for item in db:
        sz_raw = item.get('size', '')
        if not sz_raw: continue
        
        sz = sz_raw.split('/')[0].strip()
        
        if sz in sizes and len(sizes[sz]) < 5:
            img_path = f"assets/images/card/{item['id']}.webp"
            if os.path.exists(img_path):
                try:
                    with Image.open(img_path) as img:
                        w, h = img.width, img.height
                        ratio = h / w if w > 0 else 0
                        sizes[sz].append({
                            'name': item.get('name_en', 'Unknown'),
                            'w': w,
                            'h': h,
                            'ratio': ratio,
                            'sz': sz
                        })
                except Exception as e:
                    print(f"Error opening image {img_path}: {e}")

    for cat, items in sizes.items():
        print(f"\n--- {cat} ---")
        for x in items:
            print(f"{x['name']}: W={x['w']}, H={x['h']}, Ratio(H/W)={x['ratio']:.2f}")

if __name__ == "__main__":
    analyze_sizes()
