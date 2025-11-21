## HSDS Validator

The HSDS validator validates files against the provided Human Services Data Specification (HSDS), ensuring that they have no extra or missing fields and returns a report if the validation fails.

The validator can be accessed via the Command Line Interface (CLI) locally or deployed as an API using Docker. 

Run `hsds-validate --help` to see option and instructions.

Run 
hsds-validate <path/to/input-directory> <path/to/schema_directory> [-o]

### Parameters
- `<input_directory>`: Path to directory containing JSON files to validate (required)
- `<schema_directory>`: Path to directory containing JSON schema files (required)
- `-o, --save`: Optional flag to save validation results to `validation_results.json` in the input directory

### Example
```bash
python3 -m cli.main examples/program examples/json_schema
python3 -m cli.main examples/program examples/json_schema -o
```