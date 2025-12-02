# HSDS Validator

The HSDS validator validates provided files against Human Services Data Specification (HSDS), ensuring that they have no extra or missing fields and returning a report if the validation fails.

The validator will be accessed via the Command Line Interface (CLI) locally or deployed as an API using Docker. 

# Set up

Clone the repository: `git clone https://github.com/stevensblueprint/hsds-validator.git`

Switch into the project directory: `cd hsds-validator`

Create a virtual environment: `python -m venv .venv` (powershell) or `python3 -m venv .venv` (bash)

Make sure you have a version of python >= 3.13 and pip installed.

Run `pip install -r requirements.txt`

Or:

Install uv via `pip install uv` and run `uv sync` to install dependencies.

##  Run the API

### On macOS/Linux
`source .venv/bin/activate`   # Activate the virtual environment

`cd api`                      # Navigate to the API folder

`uv run api`                  # Start the API server (Press Ctrl + C in the terminal to stop)

`deactivate`                  # Deactivate the virtual environment

### On Windows (PowerShell)
`.venv\Scripts\activate`     # Activate the virtual environment

`cd api`                     # Navigate to the API folder

`uv run api`                  # Start the API server (Press Ctrl + C in the terminal to stop)

`deactivate`                  # Deactivate the virtual environment

## Run the CLI

### On macOS/Linux
```bash
source .venv/bin/activate   # Activate the virtual environment

python3 -m cli.main <input_directory> <schema_directory> [-o]

deactivate                  # Deactivate the virtual environment
```

### On Windows (PowerShell)
```powershell
.venv\Scripts\activate      # Activate the virtual environment

python3 -m cli.main <input_directory> <schema_directory> [-o]

deactivate                  # Deactivate the virtual environment
```

### Parameters
- `<input_directory>`: Path to directory containing JSON files to validate (required)
- `<schema_directory>`: Path to directory containing JSON schema files (required)
- `-o, --save`: Optional flag to save validation results to `validation_results.json` in the input directory

### Example
```bash
python3 -m hsds_validator.cli.main examples/program examples/json_schema
python3 -m hsds_validator.cli.main examples/program examples/json_schema -o
```