# capitals.py -- the sentences of train_lora.py: forty countries to
# train on and eight that the adapter never sees.
CAPITALS = {
    "Germany": "Berlin", "Spain": "Madrid", "Portugal": "Lisbon",
    "Russia": "Moscow", "China": "Beijing", "India": "New Delhi",
    "Ireland": "Dublin", "Sweden": "Stockholm", "Finland": "Helsinki",
    "Denmark": "Copenhagen", "Belgium": "Brussels", "Hungary": "Budapest",
    "Turkey": "Ankara", "Iran": "Tehran", "Iraq": "Baghdad",
    "Thailand": "Bangkok", "Vietnam": "Hanoi", "Cuba": "Havana",
    "Mexico": "Mexico City", "Chile": "Santiago",
    "Argentina": "Buenos Aires",
    "Colombia": "Bogota", "Kenya": "Nairobi",
    "Ethiopia": "Addis Ababa",
    "Ghana": "Accra", "Morocco": "Rabat", "Ukraine": "Kyiv",
    "Romania": "Bucharest", "Bulgaria": "Sofia", "Serbia": "Belgrade",
    "Croatia": "Zagreb", "Iceland": "Reykjavik", "Lebanon": "Beirut",
    "Syria": "Damascus", "Nepal": "Kathmandu", "Indonesia": "Jakarta",
    "South Korea": "Seoul", "the Philippines": "Manila",
    "the Netherlands": "Amsterdam", "the Czech Republic": "Prague",
    # held out: the adapter never sees these eight
    "France": "Paris", "Japan": "Tokyo", "Italy": "Rome",
    "Egypt": "Cairo",
    "Peru": "Lima", "Norway": "Oslo", "Poland": "Warsaw",
    "Greece": "Athens",
}
HELD_OUT = list(CAPITALS)[-8:]
