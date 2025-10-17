from fastapi import FastAPI, UploadFile, File, HTTPException
import uvicorn
import json
import zipfile
import io
import os
import tempfile
from lib.error_handling_classes import ValidationResult, ValidationErrorType, FileValidationError
from lib.validate import bulk_validate
from lib.error_handling import validate_json_format

app = FastAPI()


@app.get("/health")
def health():
   return {"ok": True}


@app.post("/validate")
def validate(
   input_dir: UploadFile = File(..., description="ZIP file containing the files to be validated"),
   schema_zip: UploadFile = File(..., description="ZIP file containing JSON schemas to validate against")
):
   """
   Endpoint that validates files in a ZIP archive against JSON schemas in another ZIP file
   
   Args:
       input_dir: ZIP file containing the files to be validated
       schema_zip: ZIP file containing JSON schemas to validate against
   
   Returns:
       JSON response with validation results
   """

   # Basic input validation
   if not input_dir:
      result = ValidationResult.error_result(
         ValidationErrorType.FILE_NOT_FOUND,
         "input_dir",
         "ZIP file is required"
      )
      return {"success": False, "errors": [f"{result.filepath}: {result.error_type.value}"]}
  
   if not schema_zip:
      result = ValidationResult.error_result(
         ValidationErrorType.FILE_NOT_FOUND,
         "schema_zip",
         "Schema ZIP file is required"
      )
      return {"success": False, "errors": [f"{result.filepath}: {result.error_type.value}"]}
   
   # Validate that uploaded files are ZIPs
   if not input_dir.filename.lower().endswith('.zip'):
      result = ValidationResult.error_result(
         ValidationErrorType.FILE_ACCESS_ERROR,
         input_dir.filename,
         "Invalid ZIP file"
      )
      return {"success": False, "errors": [f"{result.filepath}: {result.error_type.value}"]}
      
   if not schema_zip.filename.lower().endswith('.zip'):
      result = ValidationResult.error_result(
         ValidationErrorType.FILE_ACCESS_ERROR,
         schema_zip.filename,
         "Invalid ZIP file for schemas"
      )
      return {"success": False, "errors": [f"{result.filepath}: {result.error_type.value}"]}
      
   # Extract schemas from ZIP file
   schemas = []
   try:
      schema_zip_bytes = schema_zip.file.read()
      with zipfile.ZipFile(io.BytesIO(schema_zip_bytes)) as z:
         schema_file_list = z.namelist()
         if not schema_file_list:
            result = ValidationResult.error_result(
               ValidationErrorType.FILE_EMPTY,
               schema_zip.filename,
               "Schema ZIP file is empty"
            )
            return {"success": False, "errors": [f"{result.filepath}: {result.error_type.value}"]}
         
         schema_errors = []
         for schema_fname in schema_file_list:
            if schema_fname.endswith('/'):
               continue
            # Skip system files
            if (schema_fname.startswith('__MACOSX/') or schema_fname.endswith('.DS_Store') or
                schema_fname.startswith('.') or '/.DS_Store' in schema_fname or
                '/._' in schema_fname or schema_fname.endswith('Thumbs.db') or
                schema_fname.endswith('desktop.ini') or '/Thumbs.db' in schema_fname or
                '/desktop.ini' in schema_fname):
               continue
            if not schema_fname.endswith('.json'):
               result = ValidationResult.error_result(
                  ValidationErrorType.INVALID_JSON,
                  schema_fname,
                  "Not a JSON file"
               )
               schema_errors.append(f"{result.filepath}: {result.error_type.value}")
               continue
               
            try:
               # Use NamedTemporaryFile for cross-platform compatibility
               with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.json') as temp_file:
                  with z.open(schema_fname) as f_in:
                     temp_file.write(f_in.read())
                  file_path = temp_file.name
               
               try:
                  is_valid, error_message = validate_json_format(file_path)
                  if not is_valid:
                     raise FileValidationError(
                        ValidationErrorType.INVALID_JSON,
                        schema_fname,
                        error_message
                     )
                  with open(file_path, 'r', encoding='utf-8') as f:
                     schema_data = json.load(f)
                     schemas.append(schema_data)
               finally:
                  # Clean up the temporary file
                  try:
                     os.unlink(file_path)
                  except OSError:
                     pass  # Ignore cleanup errors
            except FileValidationError as ve:
               result = ValidationResult.error_result(
                  ve.error_type,
                  ve.filepath,
                  ve.message,
                  ve.details
               )
               schema_errors.append(f"{result.filepath}: {result.error_type.value}")
            except Exception as e:
               result = ValidationResult.error_result(
                  ValidationErrorType.UNKNOWN_ERROR,
                  schema_fname,
                  str(e)
               )
               schema_errors.append(f"{result.filepath}: {result.error_type.value} - {result.message}")
               
         if schema_errors:
            return {"success": False, "errors": schema_errors}
            
         if not schemas:
            result = ValidationResult.error_result(
               ValidationErrorType.FILE_EMPTY,
               schema_zip.filename,
               "No valid JSON schemas found in ZIP file"
            )
            return {"success": False, "errors": [f"{result.filepath}: {result.error_type.value}"]}
            
   except zipfile.BadZipFile:
      result = ValidationResult.error_result(
         ValidationErrorType.FILE_ACCESS_ERROR,
         schema_zip.filename,
         "Invalid ZIP file for schemas"
      )
      return {"success": False, "errors": [f"{result.filepath}: {result.error_type.value}"]}
   except Exception as e:
      result = ValidationResult.error_result(
        ValidationErrorType.UNKNOWN_ERROR,
        schema_zip.filename,
        str(e)
      )
      return {"success": False, "errors": [f"{result.filepath}: {result.error_type.value} - {result.message}"]}

   # Unzip files and validate
   input_dir_data = []  # array to store (filename, data) tuples
   try:
      zip_bytes = input_dir.file.read()
      with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
         file_list = z.namelist()
         if not file_list:
            result = ValidationResult.error_result(
               ValidationErrorType.FILE_EMPTY,
               input_dir.filename,
               "ZIP file is empty"
            )
            return {"success": False, "errors": [f"{result.filepath}: {result.error_type.value}"]}
         errors = []
         for fname in file_list:
            if fname.endswith('/'):
               continue
            # skip system files
            if (fname.startswith('__MACOSX/') or fname.endswith('.DS_Store') or fname.startswith('.') or '/.DS_Store' in fname or '/._' in fname or fname.endswith('Thumbs.db') or fname.endswith('desktop.ini') or '/Thumbs.db' in fname or '/desktop.ini' in fname):
               continue
            if not fname.endswith('.json'):
               result = ValidationResult.error_result(
                  ValidationErrorType.INVALID_JSON,
                  fname,
                  "Not a JSON file"
               )
               errors.append(f"{result.filepath}: {result.error_type.value}")
               continue
            try:
               # Use NamedTemporaryFile for cross-platform compatibility
               with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.json') as temp_file:
                  with z.open(fname) as f_in:
                     temp_file.write(f_in.read())
                  file_path = temp_file.name
               
               try:
                  is_valid, error_message = validate_json_format(file_path)
                  if not is_valid:
                     raise FileValidationError(
                        ValidationErrorType.INVALID_JSON,
                        fname,
                        error_message
                     )
                  with open(file_path, 'r', encoding='utf-8') as f:
                     data = json.load(f)
                     input_dir_data.append((fname, data))
               finally:
                  # Clean up the temporary file
                  try:
                     os.unlink(file_path)
                  except OSError:
                     pass  # Ignore cleanup errors
            except FileValidationError as ve:
               result = ValidationResult.error_result(
                  ve.error_type,
                  ve.filepath,
                  ve.message,
                  ve.details
               )
               errors.append(f"{result.filepath}: {result.error_type.value}")
            except Exception as e:
               result = ValidationResult.error_result(
                  ValidationErrorType.UNKNOWN_ERROR,
                  fname,
                  str(e)
               )
               errors.append(f"{result.filepath}: {result.error_type.value} - {result.message}")
         if errors:
            return {"success": False, "errors": errors}
   except zipfile.BadZipFile:
      result = ValidationResult.error_result(
         ValidationErrorType.FILE_ACCESS_ERROR,
         input_dir.filename,
         "Invalid ZIP file"
      )
      return {"success": False, "errors": [f"{result.filepath}: {result.error_type.value}"]}
   except Exception as e:
      result = ValidationResult.error_result(
         ValidationErrorType.UNKNOWN_ERROR,
         input_dir.filename if input_dir else "unknown",
         str(e)
      )
      return {"success": False, "errors": [f"{result.filepath}: {result.error_type.value} - {result.message}"]}
   
   # Validate each JSON object against the provided schemas using bulk_validate
   try:
      results = bulk_validate(input_dir_data, input_dir.filename, schemas)
      
      # Process results to create a summary
      successful_files = []
      failed_files = []
      all_errors = []
      
      for result in results:
         filename = result.get("filename", "unknown")
         if result.get("success", False):
            successful_files.append(filename)
         else:
            failed_files.append(filename)
            all_errors.append({"filename": filename, "errors": result.get("errors", [])})
      
      # Return summary with success status, file lists, errors, and original input data
      return {
         "success": len(failed_files) == 0,
         "summary": {
            "total_files": len(results),
            "successful": len(successful_files),
            "failed": len(failed_files)
         },
         "successful_files": successful_files,
         "failed_files": failed_files,
         "errors": all_errors,
      }
   except Exception as e:
      result = ValidationResult.error_result(
         ValidationErrorType.UNKNOWN_ERROR,
         "validation",
         str(e)
      )
      return {"success": False, "errors": [f"{result.filepath}: {result.error_type.value} - {result.message}"]}

def main():
   uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
   main()
