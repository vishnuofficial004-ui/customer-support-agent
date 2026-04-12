from typing import List, Dict

# Replace this with real DB later (PostgreSQL / MongoDB)

PRODUCTS = [
    {
        "id": 1,
        "name": "Ortho Mattress Pro",
        "type": "mattress",
        "price": 22000,
        "features": ["memory foam", "back support"],
        "health_friendly": True
    },
    {
        "id": 2,
        "name": "Basic Spring Mattress",
        "type": "mattress",
        "price": 14000,
        "features": ["spring"],
        "health_friendly": False
    },
    {
        "id": 3,
        "name": "Comfort Sofa 3-Seater",
        "type": "sofa",
        "price": 26000,
        "features": ["foam", "premium fabric"],
        "health_friendly": False
    },
    {
        "id": 4,
        "name": "Ergo Sofa",
        "type": "sofa",
        "price": 20000,
        "features": ["lumbar support"],
        "health_friendly": True
    }
]


def get_products_by_type(product_type: str) -> List[Dict]:
    return [p for p in PRODUCTS if p["type"] == product_type]

def get_all_product_types():
    return list(set([p["type"] for p in PRODUCTS]))