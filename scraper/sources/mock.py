"""Fallback source: realistic SAMPLE data, clearly labelled source = 'Sample Data'.

The assignment allows mock data if scraping is blocked. It is generated from a seeded RNG
so results are reproducible, and the source column makes it impossible to confuse with
real scraped rows (the dashboard shows it as a separate slice).
"""
import random

SOURCE_NAME = "Sample Data"

CITIES = ["Pune", "Mumbai", "Delhi", "Bengaluru", "Hyderabad", "Chennai", "Kolkata", "Ahmedabad"]
CATEGORIES = {
    "Restaurant": ["Spice Garden", "Tandoor House", "Curry Leaf", "The Thali Co", "Bombay Bites"],
    "Cafe": ["Brew Lab", "Chai Point", "Bean There", "Cup & Saucer", "Daily Grind"],
    "Pharmacy": ["Apollo Care", "Wellness Chemist", "City Medico", "HealthPlus", "MedLife"],
    "Gym": ["Iron Temple", "FitZone", "Muscle Mantra", "Pulse Fitness", "Anytime Gym"],
    "Bank": ["Metro Co-op Bank", "Unity Bank", "Prime Savings", "Citizens Bank", "Grameen Bank"],
    "Salon": ["Glow Studio", "Style Hub", "Urban Cuts", "Shear Magic", "Looks Unisex Salon"],
    "Electronics": ["Digi World", "Gadget Galaxy", "Tech Bazaar", "Volt Store", "Circuit City"],
    "Clinic": ["Sunrise Clinic", "CarePoint", "Dr. Rao Clinic", "LifeLine Clinic", "Family Health"],
}
AREAS = ["MG Road", "Station Road", "Market Street", "Park Avenue", "Lake View Road", "Civil Lines", "Ring Road"]


def scrape(cities: list[str] | None, per_city: int, seed: int = 42) -> list[dict]:
    rng = random.Random(seed)
    cities = cities or CITIES
    out = []
    for city in cities:
        for _ in range(per_city):
            category = rng.choice(list(CATEGORIES))
            name = f"{rng.choice(CATEGORIES[category])} {rng.choice(['', 'Plaza', 'Express', 'Central', 'Prime'])}".strip()
            out.append({
                "business_name": f"{name} #{rng.randint(1, 999)}",
                "category": category,
                "city": city,
                "address": f"{rng.randint(1, 250)}, {rng.choice(AREAS)}, {city}",
                "phone": f"+91{rng.choice('6789')}{rng.randint(10**8, 10**9 - 1)}" if rng.random() > 0.15 else None,
                "source": SOURCE_NAME,
            })
    return out
