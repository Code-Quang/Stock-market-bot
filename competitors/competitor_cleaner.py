import json

def clean_competitor_data(input_file, output_file):
    # Load the raw JSON data
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Clean the data
    cleaned_data = {}

    for company, competitors in data.items():
        cleaned_competitors = []

        for competitor in competitors:
            name = competitor.get("name", "").strip()
            ticker = competitor.get("ticker", "").strip()

            # Check if both name and ticker meet the criteria
            if name and ticker.isupper() and len(ticker.split()) == 1 and len(name.split()) <= 5:
                cleaned_competitors.append(competitor)

        if cleaned_competitors:
            cleaned_data[company] = cleaned_competitors

    # Save the cleaned data to a new JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, ensure_ascii=False, indent=4)

    print(f"Cleaned data saved to {output_file}.")

# Usage
input_json_file = 'competitors.json'  # Path to the raw JSON file
output_json_file = 'cleaned_competitors.json'  # Path for cleaned JSON file

clean_competitor_data(input_json_file, output_json_file)
