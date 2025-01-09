#!/usr/bin/env python3

import csv
import json
import sys
from tqdm import tqdm
import html

def get_keys_from_json(json_data):
    keys = set()
    if isinstance(json_data, list):
        for item in json_data:
            keys.update(item.keys())
    elif isinstance(json_data, dict):
        keys.update(json_data.keys())
    return list(keys)

def prompt_for_keys(keys):
    print("Available keys:")
    for i, key in enumerate(keys):
        print(f"{i + 1}. {key}")
    
    selected_keys = input("Enter the numbers of the keys you want to include, separated by commas, or type 'all' to include all keys: ").strip().lower()
    if selected_keys == "all":
        return keys
    else:
        selected_keys = [keys[int(i) - 1] for i in selected_keys.split(",") if i.strip().isdigit()]
        return selected_keys

def prompt_for_escape():
    choice = input("Would you like to escape characters that may be interpreted as HTML? (Y/n): ").strip().lower()
    if choice == '' or choice == 'y':
        return True
    else:
        return False

def json_to_csv(json_path, csv_path, desired_keys, escape_html):
    try:
        print("Opening JSON file...")
        with open(json_path, 'r', encoding='utf-8') as jfile:
            print("Loading JSON data...")
            json_data = json.load(jfile)

        # Check if json_data is a list or a dictionary
        if isinstance(json_data, list):
            data_items = json_data
        elif isinstance(json_data, dict) and 'data' in json_data:
            data_items = json_data['data']
        else:
            raise ValueError("JSON data format is not supported")

        print(f"JSON data loaded, processing {len(data_items)} items...")

        with open(csv_path, 'w', newline='', encoding='utf-8') as cfile:
            writer = csv.DictWriter(cfile, fieldnames=desired_keys)
            writer.writeheader()

            for item in tqdm(data_items, desc="Converting JSON to CSV", unit="rows"):
                if escape_html:
                    row = {key: (html.escape(str(item.get(key))) if item.get(key) is not None else '') for key in desired_keys}
                else:
                    row = {key: (str(item.get(key)) if item.get(key) is not None else '') for key in desired_keys}
                writer.writerow(row)

        print(f"CSV file has been created at '{csv_path}'")

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
    except IOError as e:
        print(f"Error reading or writing files: {e}")
    except KeyError as e:
        print(f"Missing key in JSON data: {e}")
    except ValueError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <json_file>")
        sys.exit(1)

    json_file_path = sys.argv[1]
    csv_file_path = json_file_path.rsplit('.', 1)[0] + '.csv'

    # Load JSON data to get keys
    with open(json_file_path, 'r', encoding='utf-8') as jfile:
        json_data = json.load(jfile)
    
    keys = get_keys_from_json(json_data)
    keys_to_extract = prompt_for_keys(keys)
    escape_html = prompt_for_escape()

    json_to_csv(json_file_path, csv_file_path, keys_to_extract, escape_html)
