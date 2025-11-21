# HSDS Validator

Validate files against the Human Services Data Specification (HSDS) and return a detailed report if validation fails.

The validator can be accessed via the Command Line Interface (CLI) or deployed as an API.

**Important**: Every file in the input directory must be of a single object type specified in the name of the directory.

## Installation
```bash
pip install hsds-validator
```

With API support:
```bash
pip install hsds-validator[api]
```

## Usage

### CLI

Run `hsds-validate --help` to see options and instructions.
```bash
hsds-validate <path/to/input-directory> <path/to/schema-directory> [-o]
```

#### Parameters
- `<input_directory>`: Path to directory containing JSON files to validate. Directory name must match the object type (required)
- `<schema_directory>`: Path to directory containing JSON schema files (required)
- `-o, --save`: Optional flag to save validation results to `validation_results.json` in the input directory

#### Examples
```bash
# Validate organization files
hsds-validate ./organization ./schemas

# Validate and save results
hsds-validate ./organization ./schemas --save
```

### API Server
```bash
hsds-api
```

API available at `http://localhost:8000`. Visit `http://localhost:8000/docs` for interactive documentation.

**Note**: The API accepts two ZIP files: the data to validate and the schemas.

## Requirements

- Python >= 3.13

## License

MIT

## Contact

Stevens Blueprint - blueprint@stevens.edu

## About HSDS

Learn more about the Human Services Data Specification at [docs.openreferral.org](https://docs.openreferral.org/).
