# json2csv

`json2csv` is a Python script that converts JSON data into CSV format. It can handle nested JSON by letting you choose **which JSON node contains the records (rows)** to export. The keys of those records become the CSV column headers.

## Features

- **Record (row) selection**
  - Interactive navigator lets you move **down into** keys/indices and **back up** until you reach the list of objects you want to export.
  - Optional `--records-path` lets you skip prompts by specifying the JSON path to the records node.
- **Dynamic Key Selection**: Extracts keys from the selected records and prompts you to select which keys to include in the CSV output.
- **Column Renaming**: Optionally rename selected columns interactively.
- **HTML Character Escaping**: Optionally escape characters that may be interpreted as HTML to ensure data integrity.
- **Progress Tracking**: Displays a progress bar while converting JSON to CSV.
- **Optional Compression**: Optionally compress the output CSV (`gz`, `zip`, `bz2`) if tools are available.

## Requirements

- Python 3
- `tqdm`:
  ```sh
  python3 -m pip install --user tqdm
````

## Usage

1. **Clone the Repository**:

   ```sh
   git clone https://github.com/Pb-22/json2csv.py.git
   cd json2csv.py
   ```

2. **Run the Script**:

   ```sh
   python3 json2csv.py <json_file>
   ```

   Replace `<json_file>` with the path to your JSON file.

### Options

* `--records-path RECORDS_PATH`
  Path to the JSON node that contains the **records (rows)** to export (a list of objects). The objects under that path become the CSV rows and headers.
  Examples:

  * `--records-path data` exports `data[*]` as rows
  * `--records-path $.data.items` exports `data.items[*]` as rows

* `--no-navigate`
  Disable the interactive navigator and use the default/legacy row selection (root list, or `data` if present).

## Examples

### Interactive selection (recommended when you are not sure where the rows are)

```sh
python3 json2csv.py data.json
```

### Non-interactive: export from `data`

```sh
python3 json2csv.py data.json --records-path data
```

### Non-interactive: export from a deeper path

```sh
python3 json2csv.py data.json --records-path $.data.items
```

## Prompt flow (typical)

* The script selects the record node (interactive navigator or `--records-path`)
* It shows available keys and asks which columns to include (`all` for all keys)
* It offers optional column renames
* It asks whether to escape HTML characters
* It writes the CSV and optionally compresses it

```
Available keys:
1. key1
2. key2
3. key3
Enter the numbers of the keys you want to include, separated by commas, or type 'all': all
Escape HTML characters? (Y/n): Y
Converting JSON to CSV: 100%|███████████████████████████████████████████████████████████
```

````

Next command (one at a time) to verify the README edit is staged cleanly after you paste it:

```bash
git diff

