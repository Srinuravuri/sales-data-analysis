"""Generate a realistic Indian retail sales dataset (reproducible).

Output: data/sales_data.csv
3 years of transactions (2022-01-01 to 2024-12-31) with:
  order_id, order_date, region, state, city, category, sub_category,
  product_name, units, unit_price, discount_pct, sales, profit
"""

import random
from datetime import date, timedelta

import pandas as pd

random.seed(42)

# ---------------------------------------------------------------------
# Data dimensions (Indian retail)
# ---------------------------------------------------------------------
REGIONS = {
    "South": ["Andhra Pradesh", "Telangana", "Karnataka", "Tamil Nadu", "Kerala"],
    "North": ["Delhi", "Uttar Pradesh", "Haryana", "Punjab", "Rajasthan"],
    "West": ["Maharashtra", "Gujarat", "Goa", "Madhya Pradesh"],
    "East": ["West Bengal", "Odisha", "Bihar", "Assam"],
}

CITIES = {
    "Andhra Pradesh": ["Vijayawada", "Visakhapatnam", "Guntur", "Tirupati"],
    "Telangana": ["Hyderabad", "Warangal", "Karimnagar"],
    "Karnataka": ["Bengaluru", "Mysuru", "Hubballi"],
    "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai"],
    "Kerala": ["Kochi", "Thiruvananthapuram", "Kozhikode"],
    "Delhi": ["New Delhi", "Dwarka"],
    "Uttar Pradesh": ["Lucknow", "Kanpur", "Varanasi", "Noida"],
    "Haryana": ["Gurugram", "Faridabad"],
    "Punjab": ["Chandigarh", "Ludhiana", "Amritsar"],
    "Rajasthan": ["Jaipur", "Jodhpur", "Udaipur"],
    "Maharashtra": ["Mumbai", "Pune", "Nagpur", "Nashik"],
    "Gujarat": ["Ahmedabad", "Surat", "Vadodara"],
    "Goa": ["Panaji", "Margao"],
    "Madhya Pradesh": ["Indore", "Bhopal"],
    "West Bengal": ["Kolkata", "Howrah", "Siliguri"],
    "Odisha": ["Bhubaneswar", "Cuttack"],
    "Bihar": ["Patna", "Gaya"],
    "Assam": ["Guwahati", "Dibrugarh"],
}

CATALOG = {
    "Electronics": {
        "Mobile Phones": ["Samsung Galaxy A54", "Redmi Note 13", "iPhone 14", "OnePlus 12R"],
        "Laptops": ["Dell Inspiron 15", "HP Pavilion", "Lenovo IdeaPad", "Asus Vivobook"],
        "Accessories": ["Wireless Earbuds", "Smart Watch", "Bluetooth Speaker", "Power Bank"],
        "Televisions": ["Sony Bravia 43\"", "LG 55\" UHD", "Samsung 50\" Crystal"],
    },
    "Furniture": {
        "Sofas": ["3-Seater Fabric Sofa", "L-Shaped Sofa", "Recliner Sofa"],
        "Tables": ["Dining Table 6-Seater", "Coffee Table", "Office Desk"],
        "Chairs": ["Ergonomic Office Chair", "Gaming Chair", "Wooden Dining Chair"],
        "Storage": ["Wardrobe 4-Door", "Bookshelf", "TV Unit"],
    },
    "Office Supplies": {
        "Stationery": ["A4 Paper Ream", "Gel Pen Pack", "Notebook Bundle"],
        "Printers": ["HP Inkjet Printer", "Canon Laser Printer"],
        "Ink & Toner": ["HP Ink Cartridge", "Canon Toner"],
    },
    "Clothing": {
        "Menswear": ["Formal Shirt", "Jeans", "Casual T-Shirt", "Sherwani"],
        "Womenswear": ["Kurti", "Saree", "Dress", "Ethnic Set"],
        "Footwear": ["Running Shoes", "Formal Shoes", "Sandals"],
    },
}

# Seasonality: festival months sell more (India: Diwali ~Oct-Nov, etc.)
MONTH_WEIGHT = {
    1: 0.8, 2: 0.8, 3: 1.0, 4: 1.0, 5: 1.1, 6: 1.0,
    7: 1.0, 8: 1.2, 9: 1.2, 10: 1.6, 11: 1.5, 12: 1.3,
}


def pick_city(state: str) -> str:
    return random.choice(CITIES[state])


def pick_product(category: str):
    sub = random.choice(list(CATALOG[category].keys()))
    product = random.choice(CATALOG[category][sub])
    return category, sub, product


def main():
    rows = []
    order_id = 1000
    start = date(2022, 1, 1)
    end = date(2024, 12, 31)
    n_days = (end - start).days

    for _ in range(5000):
        # Pick a date biased by festival months
        while True:
            d = start + timedelta(days=random.randint(0, n_days))
            if random.random() < MONTH_WEIGHT[d.month] / 1.6:
                break

        region = random.choice(list(REGIONS.keys()))
        state = random.choice(REGIONS[region])
        city = pick_city(state)
        category, sub, product = pick_product(random.choice(list(CATALOG.keys())))

        units = random.randint(1, 6)
        # Base price varies by category
        base_price = {
            "Electronics": random.randint(8000, 75000),
            "Furniture": random.randint(3000, 45000),
            "Office Supplies": random.randint(150, 12000),
            "Clothing": random.randint(250, 5000),
        }[category]
        discount_pct = random.choice([0, 0, 5, 10, 10, 15, 20, 25, 30, 40])
        unit_price = base_price * (1 - discount_pct / 100)
        sales = round(unit_price * units, 2)

        # Profit varies: electronics thin margin, clothing healthier
        margin_pct = random.uniform(0.02, 0.16) if category == "Electronics" else \
                     random.uniform(0.05, 0.28)
        profit = round(sales * margin_pct, 2)

        rows.append({
            "order_id": order_id,
            "order_date": d.isoformat(),
            "region": region,
            "state": state,
            "city": city,
            "category": category,
            "sub_category": sub,
            "product_name": product,
            "units": units,
            "unit_price": round(unit_price, 2),
            "discount_pct": discount_pct,
            "sales": sales,
            "profit": profit,
        })
        order_id += 1

    df = pd.DataFrame(rows)
    df.to_csv("data/sales_data.csv", index=False)
    print(f"Generated {len(df):,} transactions -> data/sales_data.csv")
    print(df.head(3).to_string(index=False))
    print("\nDate range:", df["order_date"].min(), "->", df["order_date"].max())


if __name__ == "__main__":
    main()
