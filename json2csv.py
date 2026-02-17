#!/usr/bin/env python3

import argparse
import csv
import json
import sys
import html
import shutil
import subprocess

# Optional tqdm progress bar (falls back to plain iteration if missing)
try:
    from tqdm import tqdm  # type: ignore
except Exception:  # pragma: no cover
    tqdm = None


def iter_rows(iterable, desc="Converting JSON to CSV", unit="rows"):
    if tqdm is None:
        return iterable
    return tqdm(iterable, desc=desc, unit=unit)


def get_keys_from_json(json_data):
    keys = set()
    if isinstance(json_data, list):
        for item in json_data:
            if isinstance(item, dict):
                keys.update(item.keys())
    elif isinstance(json_data, dict):
        keys.update(json_data.keys())
    return list(keys)


def prompt_for_keys(keys):
    print("Available keys:")
    for i, key in enumerate(keys):
        print(f"{i + 1}. {key}")

    selected_keys = input(
        "Enter the numbers of the keys you want to include, separated by commas, or type 'all': "
    ).strip().lower()

    if selected_keys == "all":
        return keys

    selected = []
    for part in selected_keys.split(","):
        part = part.strip()
        if not part.isdigit():
            continue
        idx = int(part) - 1
        if 0 <= idx < len(keys):
            selected.append(keys[idx])
    return selected


def prompt_for_escape():
    choice = input("Escape HTML characters? (Y/n): ").strip().lower()
    return choice == "" or choice == "y"


def prompt_for_column_renames(selected_keys):
    print("You have selected the following columns:")
    rename_map = {}
    for key in selected_keys:
        new_name = input(f"Enter a new name for '{key}' or press Enter to keep it: ").strip()
        rename_map[key] = new_name if new_name else key
    return rename_map


def check_available_compressors():
    compressors = []
    if shutil.which("gzip"):
        compressors.append("gz")
    if shutil.which("zip"):
        compressors.append("zip")
    if shutil.which("bzip2"):
        compressors.append("bz2")
    return compressors


def prompt_for_zipping():
    choice = input("Zip the CSV file? (N/y): ").strip().lower()
    if choice == "" or choice == "n":
        return None

    compressors = check_available_compressors()
    if not compressors:
        print("No compression tools found; skipping compression.")
        return None

    default_method = "gz" if "gz" in compressors else compressors[0]
    method_choice = input(
        f"Choose compression method {compressors} [default={default_method}]: "
    ).strip().lower()

    if not method_choice:
        method_choice = default_method

    if method_choice not in compressors:
        print("Unavailable method; skipping compression.")
        return None

    return method_choice


def compress_csv(csv_path, method):
    if method == "gz":
        subprocess.run(["gzip", csv_path], check=False)
    elif method == "zip":
        subprocess.run(["zip", csv_path + ".zip", csv_path], check=False)
    elif method == "bz2":
        subprocess.run(["bzip2", csv_path], check=False)


def _node_type_label(node):
    if isinstance(node, dict):
        return "dict"
    if isinstance(node, list):
        return f"list(len={len(node)})"
    return type(node).__name__


def _preview_child_types(node):
    # For dict: show key -> type
    if isinstance(node, dict):
        out = []
        for k in list(node.keys())[:30]:
            out.append((k, _node_type_label(node[k])))
        more = max(0, len(node.keys()) - len(out))
        return out, more

    # For list: show element types counts (sample)
    if isinstance(node, list):
        counts = {}
        for el in node[:50]:
            t = _node_type_label(el)
            counts[t] = counts.get(t, 0) + 1
        items = sorted(counts.items(), key=lambda x: (-x[1], x[0]))
        return items, 0

    return [], 0


def _is_list_of_dicts(node):
    if not isinstance(node, list) or len(node) == 0:
        return False
    sample = node[:50]
    return all(isinstance(x, dict) for x in sample)


def _find_record_list_candidates(root):
    """
    Return list of (path_tokens, node) where node is list of dicts.
    Limited BFS for friendliness.
    """
    candidates = []
    queue = [([], root)]
    visited = 0
    max_nodes = 400

    while queue and visited < max_nodes:
        path, node = queue.pop(0)
        visited += 1

        if _is_list_of_dicts(node):
            candidates.append((path, node))
            continue

        if isinstance(node, dict):
            for k, v in node.items():
                queue.append((path + [k], v))
        elif isinstance(node, list):
            for i, v in enumerate(node[:10]):
                queue.append((path + [i], v))

    candidates.sort(key=lambda x: (len(x[0]), str(x[0])))
    return candidates


def _path_tokens_to_str(tokens):
    if not tokens:
        return "$"
    s = "$"
    for t in tokens:
        if isinstance(t, int):
            s += f"[{t}]"
        else:
            if str(t).replace("_", "").isalnum():
                s += f".{t}"
            else:
                s += f"['{t}']"
    return s


def _resolve_path(root, path_str):
    """
    Accepts:
      - data
      - data.items
      - $.data.items
      - data[0].items
    Very small parser: dot segments and [index] segments.
    """
    s = path_str.strip()
    if s.startswith("$"):
        s = s[1:]
        if s.startswith("."):
            s = s[1:]

    tokens = []
    buf = ""
    i = 0
    while i < len(s):
        ch = s[i]
        if ch == ".":
            if buf:
                tokens.append(buf)
                buf = ""
            i += 1
            continue
        if ch == "[":
            if buf:
                tokens.append(buf)
                buf = ""
            j = s.find("]", i)
            if j == -1:
                raise ValueError("Invalid records path: missing ']'")
            inside = s[i + 1 : j].strip()
            if not inside.isdigit():
                raise ValueError("Invalid records path: list index must be an integer")
            tokens.append(int(inside))
            i = j + 1
            continue
        buf += ch
        i += 1
    if buf:
        tokens.append(buf)

    node = root
    for t in tokens:
        if isinstance(t, int):
            if not isinstance(node, list):
                raise ValueError(f"Path expects list at {t}, but found {_node_type_label(node)}")
            if t < 0 or t >= len(node):
                raise ValueError(f"List index out of range: {t}")
            node = node[t]
        else:
            if not isinstance(node, dict):
                raise ValueError(f"Path expects dict at '{t}', but found {_node_type_label(node)}")
            if t not in node:
                raise ValueError(f"Key not found in path: '{t}'")
            node = node[t]
    return node


def choose_records_node_interactive(json_data):
    """
    Navigator:
      - shows current node summary
      - descend into dict keys or list indices
      - go up
      - choose current node as records
    """
    candidates = _find_record_list_candidates(json_data)
    if candidates:
        best_path, best_node = candidates[0]
        best_path_str = _path_tokens_to_str(best_path)
        yn = input(f"Found candidate record list at {best_path_str}. Use it? (Y/n): ").strip().lower()
        if yn == "" or yn == "y":
            return best_node, best_path_str

    stack = []  # list of (node, path_tokens)
    node = json_data
    path_tokens = []

    while True:
        path_str = _path_tokens_to_str(path_tokens)
        print("\n=== JSON Navigator ===")
        print(f"Current path: {path_str}")
        print(f"Current type: {_node_type_label(node)}")

        preview, more = _preview_child_types(node)
        if isinstance(node, dict):
            print("Keys (type):")
            for k, t in preview:
                print(f"  - {k}: {t}")
            if more:
                print(f"  ... ({more} more keys)")
            print("\nCommands: d <key> (descend), u (up), r (use as records), q (quit)")
        elif isinstance(node, list):
            print("List element types (sample):")
            for t, cnt in preview:
                print(f"  - {t}: {cnt}")
            print("\nCommands: d <index> (descend), u (up), r (use as records), q (quit)")
        else:
            print("\nCommands: u (up), q (quit)")

        cmd = input("> ").strip()
        if not cmd:
            continue

        lc = cmd.lower()

        if lc == "q":
            print("Quitting.")
            sys.exit(1)

        if lc == "u":
            if not stack:
                print("Already at root.")
                continue
            node, path_tokens = stack.pop()
            continue

        if lc == "r":
            if _is_list_of_dicts(node):
                return node, path_str
            if isinstance(node, dict):
                return [node], path_str
            print("Current node is not usable as records. Choose a list of objects (dicts) or a dict.")
            continue

        if lc.startswith("d "):
            arg = cmd[2:].strip()
            if isinstance(node, dict):
                if arg not in node:
                    print(f"Key not found: {arg}")
                    continue
                stack.append((node, path_tokens))
                node = node[arg]
                path_tokens = path_tokens + [arg]
                continue
            if isinstance(node, list):
                if not arg.isdigit():
                    print("For lists, use an integer index (e.g., d 0).")
                    continue
                idx = int(arg)
                if idx < 0 or idx >= len(node):
                    print(f"Index out of range: {idx}")
                    continue
                stack.append((node, path_tokens))
                node = node[idx]
                path_tokens = path_tokens + [idx]
                continue
            print("Cannot descend into a scalar value.")
            continue

        print("Unrecognized command. Try: d <key|index>, u, r, q")


def json_to_csv(csv_path, data_items, desired_keys, escape_html):
    rename_map = prompt_for_column_renames(desired_keys)
    print(f"Processing {len(data_items)} items...")

    with open(csv_path, "w", newline="", encoding="utf-8") as cfile:
        writer = csv.DictWriter(cfile, fieldnames=[rename_map[k] for k in desired_keys])
        writer.writeheader()

        for item in iter_rows(data_items):
            row = {}
            for k in desired_keys:
                val = item.get(k) if isinstance(item, dict) else None
                val = str(val) if val is not None else ""
                row[rename_map[k]] = html.escape(val) if escape_html else val
            writer.writerow(row)

    print(f"CSV file created at '{csv_path}'")

    method = prompt_for_zipping()
    if method:
        compress_csv(csv_path, method)


def main():
    parser = argparse.ArgumentParser(description="Convert JSON to CSV with interactive record selection.")
    parser.add_argument("json_file", help="Path to JSON file")
    parser.add_argument(
        "--records-path",
        help="Path to the JSON node that contains the records (rows) to export (a list of objects). Example: data exports data[*] as rows.",
    )
    parser.add_argument(
        "--no-navigate",
        action="store_true",
        help="Disable the interactive navigator and use the default/legacy row selection (root list, or data if present).",
    )
    args = parser.parse_args()

    json_file_path = args.json_file
    csv_file_path = json_file_path.rsplit(".", 1)[0] + ".csv"

    try:
        with open(json_file_path, "r", encoding="utf-8") as jfile:
            json_data = json.load(jfile)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        sys.exit(1)
    except IOError as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

    # Determine record list (data_items)
    records_path_used = "$"

    if args.records_path:
        try:
            node = _resolve_path(json_data, args.records_path)
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)

        if _is_list_of_dicts(node):
            data_items = node
        elif isinstance(node, dict):
            data_items = [node]
        else:
            print(f"Error: records node at '{args.records_path}' is not a list of objects or a dict.")
            sys.exit(1)
        records_path_used = args.records_path

    elif args.no_navigate:
        if isinstance(json_data, list):
            data_items = json_data
        elif isinstance(json_data, dict) and "data" in json_data and isinstance(json_data["data"], list):
            data_items = json_data["data"]
            records_path_used = "$.data"
        else:
            print("Error: JSON data format is not supported (try without --no-navigate).")
            sys.exit(1)

    else:
        data_items, records_path_used = choose_records_node_interactive(json_data)

    keys = get_keys_from_json(data_items)
    if not keys:
        print(f"Error: No keys found at records node {records_path_used}.")
        sys.exit(1)

    keys_to_extract = prompt_for_keys(keys)
    if not keys_to_extract:
        print("Error: No keys selected.")
        sys.exit(1)

    escape_html_choice = prompt_for_escape()
    json_to_csv(csv_file_path, data_items, keys_to_extract, escape_html_choice)


if __name__ == "__main__":
    main()
