
# json2csv

`json2csv` is a Python script that converts JSON data into CSV format. This script is designed to handle various JSON structures and allows users to select specific keys to include in the CSV output. Additionally, it provides an option to escape characters that may be interpreted as HTML, ensuring compatibility with systems that process HTML content.

## Features

- **Dynamic Key Selection**: Automatically extracts keys from the JSON data and prompts the user to select which keys to include in the CSV.
- **HTML Character Escaping**: Optionally escape characters that may be interpreted as HTML to ensure data integrity.
- **Progress Tracking**: displays a progress bar while converting JSON to CSV.
- **Flexible Input Handling**: Supports both JSON arrays and JSON objects containing a `data` key.

## Usage

1. **Clone the Repository**:
   ```sh
   git clone https://github.com/yourusername/your-repo.git
   cd your-repo
   ```

2. **Run the Script**:
   ```sh
   python json2csv.py <json_file>
   ```

   Replace `<json_file>` with the path to your JSON file.

3. **Follow the Prompts**:
   - The script will display available keys and prompt you to select which keys to include in the CSV.
   - You can type `all` to include all keys.
   - The script will also ask if you want to escape characters that may be interpreted as HTML. The default choice is `Y` (Yes).

## Example

```sh
python json2csv.py data.json
```

Output:
```
Available keys:
1. key1
2. key2
3. key3
Enter the numbers of the keys you want to include, separated by commas, or type 'all' to include all keys: all
Would you like to escape characters that may be interpreted as HTML? (Y/n): Y
Opening JSON file...
Loading JSON data...
JSON data loaded, processing 100 items...
Converting JSON to CSV: 100%|███████████████████████████████████████████████████████████

