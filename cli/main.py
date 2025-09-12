import click
import os

def validate_json(ctx, param, value):
    """
    Checks end of file for .json
    If not applicable, throws BadParameter error
    If applicable, returns value to main function
    """
    # value is an open file object from click.File("r")
    name = getattr(value, "name", "")
    if not name.lower().endswith(".json"):
        raise click.BadParameter("File must have a .json extension.")
    return value


def validate_directory(ctx, param, value):
    """
    Checks directory for atleast one file inside
    If not applicable, throws BadParameter error
    If applicable, returns value to main function
    """
    if not os.listdir(value):
        raise click.BadParameter("Directory is empty.")
    return value


# CLI Command Line Arguments
@click.command()
@click.option(
    "-i",
    "--input_dir",
    type=click.Path(exists=True, file_okay=False),  # Type must be an existing directory
    required=True,  # Required
    help="Input valid directory path. Directory must not be empty.",
    callback=validate_directory
)
@click.option(
    "-j",
    "--json_schema",
    type=click.File("r"),
    required=True,  # Required
    help="Input JSON schema path.",
    callback=validate_json,  # Calls JSON Validation function
)
@click.option(
    "-s", 
    "--save", 
    is_flag=True, # Boolean value
    help="Saves result to file.")


def main(input_dir, json_schema, save):
    click.echo(f"Directory: {input_dir}")
    click.echo(f"JSON schema: {json_schema}")
    click.echo(f"Save:  {save}")

    print("Hello from the HSDS Validator!")

    # JSON validation and File IO


if __name__ == "__main__":
    main()
