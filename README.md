# json2csv

`json2csv` is a Python script that converts JSON data into CSV format. It is built to handle nested JSON when you are not sure where the “rows” live: you can **drill down** into keys/indices, **go up** to the parent, and preview what is below before selecting the list of objects to export.

Once you select the **records node** (the list of objects), those object keys become the candidate CSV columns.

## Features

- **Guided records (row) selection**
  - Auto-detects a likely **records node** (a list of objects) and shows a preview of potential column headers + sample values.
  - Interactive navigator lets you **drill down** and **go up** until you reach the list of objects you want to export.
  - Supports selecting keys by **name** or by **number** (for faster exploration).
- **Column selection with examples**
  - Prompts: `Keep Column1? example - "<value row 1 column 1>": (Y/n)`
  - Defaults to **Yes** so you can press Enter to keep a column, or `n` to drop it.
  - You can type `all` once to keep all columns without prompting.
- **Column renaming**: Optionally rename selected columns interactively.
- **HTML character escaping**: Optional.
- **Progress bar**: Uses `tqdm` if installed; otherwise runs without it.
- **Optional compression**: Optionally compress the output CSV (`gz`, `zip`, `bz2`) if tools are available.

## Requirements

- Python 3
- Optional: `tqdm` (progress bar)
  ```sh
  python3 -m pip install --user tqdm
````

## Usage

1. **Clone the repository**

   ```sh
   git clone https://github.com/Pb-22/json2csv.py.git
   cd json2csv.py
   ```

2. **Run the script**

   ```sh
   python3 json2csv.py <json_file>
   ```

   Replace `<json_file>` with the path to your JSON file.

## Options

* `--records-path RECORDS_PATH`
  Use this when you already know where the list of records is.
  The path should point to a **list of objects** (each object becomes one CSV row).
  Examples:

  * `--records-path data` exports `data[*]` as rows
  * `--records-path $.data.items` exports `data.items[*]` as rows

* `--no-navigate`
  Disable the interactive navigator and use the default/legacy row selection (root list, or `data` if present).

## Examples

### Guided explorer (recommended when you are not sure where the rows are)

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

## Typical prompt flow

1. Script suggests a candidate records node and shows a preview (potential column headers + sample values)
2. If you reject it, you can drill down / go up until you find the right records node
3. Column selection (default yes):

   * `Keep colA? example - "<value>": (Y/n)`
4. Optional column renames
5. Optional HTML escaping
6. Writes CSV and optionally compresses it

````

**One command (after you paste/save README.md):**
```bash
git diff
