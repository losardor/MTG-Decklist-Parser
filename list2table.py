import requests
import pandas as pd
import time
import re

# Define Scryfall API URL
SCRYFALL_API = "https://api.scryfall.com/cards/named"

# Load decklist from a text file
def load_decklist(filename):
    """Reads a decklist from a file, one card per line, handling empty lines."""
    with open(filename, "r") as file:
        return [line.strip() for line in file.readlines() if line.strip()]


# Function to fetch card data
def fetch_card_data(card_name):
    """Fetch metadata from Scryfall for a given card name, handling missing data gracefully."""
    try:
        response = requests.get(SCRYFALL_API, params={"exact": card_name})
        response.raise_for_status()
        card_data = response.json()
        return {
            "Card Name": card_data.get("name", ""),
            "Mana Cost": card_data.get("mana_cost", ""),
            "CMC": card_data.get("cmc", ""),
            "Type": card_data.get("type_line", ""),
            "Oracle Text": card_data.get("oracle_text", ""),
            "Power": card_data.get("power", ""),  # Only for creatures
            "Toughness": card_data.get("toughness", ""),  # Only for creatures
            "Rarity": card_data.get("rarity", "").capitalize(),
            "Price (USD)": card_data.get("prices", {}).get("usd", ""),
            "Role": classify_card_role(card_data)
        }
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {card_name}: {e}")
        return None

# Function to classify card roles
def classify_card_role(card_data):
    """Classifies the card into roles based on keywords in type and text."""
    types = card_data.get("type_line", "").lower()
    oracle_text = card_data.get("oracle_text", "").lower()

    if "land" in types:
        return "Land"
    elif (
        "{T}: add" in oracle_text  # Explicit mana abilities
        or "add {" in oracle_text  # Covers "Add {G}{G}, Add {U}"
        or "create a treasure token" in oracle_text  # Treasures are ramp
        or "search your library for a land card and put it onto the battlefield" in oracle_text  # Land ramp
    ):
        return "Ramp"
    elif "search your library" in oracle_text:
        return "Tutor"
    elif "destroy all" in oracle_text or "each creature" in oracle_text:
        return "Sweeper"
    elif "counter target spell" in oracle_text:
        return "Counterspell"
    elif "draw" in oracle_text and "card" in oracle_text:
        return "Card Draw"
    elif "deal" in oracle_text and "damage" in oracle_text:
        return "Direct Damage"
    elif "sacrifice" in oracle_text:
        return "Sacrifice Synergy"
    elif "exile target" in oracle_text:
        return "Removal"
    else:
        return "Other"

def process_decklist(decklist):
    """Parses decklist, extracts quantities, card names, and categories."""
    sections = {"Commander": [], "Deck": [], "Sideboard": []}
    current_section = None  # Ensure we have a valid section before adding cards

    for line in decklist:
        line = line.strip()

        # Identify sections
        if line.lower() == "commander":
            current_section = "Commander"
            continue
        elif line.lower() == "deck":
            current_section = "Deck"
            continue
        elif line.lower() == "sideboard":
            current_section = "Sideboard"
            continue

        # If no valid section has been set yet, print a warning and skip this line
        if current_section is None:
            print(f"Warning: Card '{line}' appears before a valid section header (Commander, Deck, Sideboard). Skipping.")
            continue

        # Extract quantity and card name
        match = re.match(r"(\d+)\s+(.+)", line)
        if match:
            quantity = int(match.group(1))
            card_name = match.group(2)
        else:
            # If no quantity is found, assume it's a single copy
            quantity = 1
            card_name = line

        sections[current_section].append((quantity, card_name))

    return sections

# Function to fetch all cards and create a dataframe
def process_full_deck(decklist):
    """Fetch data for each card in decklist and create a structured dataframe."""
    structured_deck = process_decklist(decklist)
    card_rows = []

    for category, cards in structured_deck.items():
        for quantity, card_name in cards:
            card_data = fetch_card_data(card_name)
            if card_data:
                card_data["Quantity"] = quantity
                card_data["Category"] = category  # Commander, Deck, Sideboard
                card_rows.append(card_data)
            time.sleep(0.1)  # Avoids Scryfall rate limits

    return pd.DataFrame(card_rows)

# Main execution
if __name__ == "__main__":
    decklist_file = "decklist.txt"  # Change this to your decklist file
    decklist = load_decklist(decklist_file)
    
    df = process_full_deck(decklist)
    
    # Save as CSV for Excel or Pandas
    df.to_csv("decklist_analysis.csv", index=False)

    print("Deck analysis saved as 'decklist_analysis.csv'")