from fastapi import FastAPI, UploadFile, File, HTTPException
import uvicorn
import json
import zipfile
import io
from jsonschema import validate as js_validate, ValidationError
app = FastAPI()


@app.get("/health")
def health():
   return {"ok": True}


@app.post("/validate")
def validate(
   input_dir: UploadFile = File(..., description="ZIP file containing the files to be validated"),
   json_schema: UploadFile = File(..., description="JSON schema to validate against")
):
   """
   Endpoint that validates files in a ZIP archive against a JSON schema
  
   Args:
       input_dir: ZIP file containing the files to be validated
       json_schema: JSON schema to validate against
  
   Returns:
       JSON response with validation results
   """
   # Basic input validation
   if not input_dir:
      raise HTTPException(status_code=400, detail="ZIP file is required")
  
   if not json_schema:
      raise HTTPException(status_code=400, detail="JSON schema is required")
   
   # Validate that uploaded file is a ZIP
   if not input_dir.filename.lower().endswith('.zip'):
      raise HTTPException(status_code=400, detail="Uploaded input_dir file must be a ZIP file")
   
   # Load JSON schema
   try:
      schema = json.load(json_schema.file)
   except Exception as e:
      raise HTTPException(status_code=400, detail=f"Invalid JSON schema: {str(e)}")
   
   # Unzip files and validate
   try:
      zip_bytes = input_dir.file.read()
      with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
         file_list = z.namelist()
         if not file_list:
               raise HTTPException(status_code=400, detail="ZIP file is empty")
         
         errors = []
         for fname in file_list:
               if fname.endswith('/'):  # skip directories
                  continue

               if (fname.startswith('__MACOSX/') or  # skip system files
                   fname.endswith('.DS_Store') or
                   fname.startswith('.') or
                   '/.DS_Store' in fname or
                   '/._' in fname or
                   fname.endswith('Thumbs.db') or
                   fname.endswith('desktop.ini') or
                   '/Thumbs.db' in fname or
                   '/desktop.ini' in fname):
                  continue

               print(f"Processing file: {fname}") # debug

               if not fname.endswith('.json'):  # Add error for non-JSON files
                    errors.append(f"{fname}: Not a JSON file")
                    continue
               try:
                  with z.open(fname) as f:
                     data = json.load(f)
                     js_validate(instance=data, schema=schema)
               except ValidationError as ve: # Add error if validation fails
                  errors.append(f"{fname}: {ve.message}")
               except Exception as e:
                  errors.append(f"{fname}: {str(e)}")
         
         if errors:
               return {"success": False, "errors": errors}
         return {"success": True}
         
   except zipfile.BadZipFile:
      raise HTTPException(status_code=400, detail="Invalid ZIP file")
   except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))

def main():
   uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
   main()
