#!/usr/bin/env python3

import csv
import json
import sys
from tqdm import tqdm
import html
import shutil
import subprocess

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
    
    selected_keys = input("Enter the numbers of the keys you want to include, separated by commas, or type 'all': ").strip().lower()
    if selected_keys == "all":
        return keys
    else:
        selected_keys = [keys[int(i) - 1] for i in selected_keys.split(",") if i.strip().isdigit()]
        return selected_keys

def prompt_for_escape():
    choice = input("Escape HTML characters? (Y/n): ").strip().lower()
    return (choice == '' or choice == 'y')

def prompt_for_column_renames(selected_keys):
    print("You have selected the following columns:")
    rename_map = {}
    for key in selected_keys:
        new_name = input(f"Enter a new name for '{key}' or press Enter to keep it: ").strip()
        rename_map[key] = new_name if new_name else key
    return rename_map

def check_available_compressors():
    compressors = []
    if shutil.which('gzip'):
        compressors.append('gz')
    if shutil.which('zip'):
        compressors.append('zip')
    if shutil.which('bzip2'):
        compressors.append('bz2')
    return compressors

def prompt_for_zipping():
    choice = input("Zip the CSV file? (N/y): ").strip().lower()
    if choice == '' or choice == 'n':
        return None
    compressors = check_available_compressors()
    if not compressors:
        print("No compression tools found; skipping compression.")
        return None
    default_method = 'gz' if 'gz' in compressors else compressors[0]
    method_choice = input(f"Choose compression method {compressors} [default={default_method}]: ").strip().lower()
    if not method_choice:
        method_choice = default_method
    if method_choice not in compressors:
        print("Unavailable method; skipping compression.")
        return None
    return method_choice

def compress_csv(csv_path, method):
    if method == 'gz':
        subprocess.run(['gzip', csv_path])
    elif method == 'zip':
        subprocess.run(['zip', csv_path + '.zip', csv_path])
    elif method == 'bz2':
        subprocess.run(['bzip2', csv_path])

def json_to_csv(json_path, csv_path, desired_keys, escape_html):
    try:
        print("Opening JSON file...")
        with open(json_path, 'r', encoding='utf-8') as jfile:
            print("Loading JSON data...")
            json_data = json.load(jfile)

        # Check if json_data is a list or dict
        if isinstance(json_data, list):
            data_items = json_data
        elif isinstance(json_data, dict) and 'data' in json_data:
            data_items = json_data['data']
        else:
            raise ValueError("JSON data format is not supported")

        rename_map = prompt_for_column_renames(desired_keys)
        print(f"JSON data loaded, processing {len(data_items)} items...")

        with open(csv_path, 'w', newline='', encoding='utf-8') as cfile:
            writer = csv.DictWriter(cfile, fieldnames=[rename_map[k] for k in desired_keys])
            writer.writeheader()

            for item in tqdm(data_items, desc="Converting JSON to CSV", unit="rows"):
                row = {}
                for k in desired_keys:
                    val = str(item.get(k)) if item.get(k) is not None else ''
                    row[rename_map[k]] = html.escape(val) if escape_html else val
                writer.writerow(row)

        print(f"CSV file created at '{csv_path}'")

        # Prompt for zipping
        method = prompt_for_zipping()
        if method:
            compress_csv(csv_path, method)

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
    except IOError as e:
        print(f"Error reading or writing files: {e}")
    except KeyError as e:
        print(f"Missing key in JSON: {e}")
    except ValueError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <json_file>")
        sys.exit(1)

    json_file_path = sys.argv[1]
    csv_file_path = json_file_path.rsplit('.', 1)[0] + '.csv'

    with open(json_file_path, 'r', encoding='utf-8') as jfile:
        json_data = json.load(jfile)
    keys = get_keys_from_json(json_data)
    keys_to_extract = prompt_for_keys(keys)
    escape_html_choice = prompt_for_escape()

    json_to_csv(json_file_path, csv_file_path, keys_to_extract, escape_html_choice)
