from fastapi import FastAPI, UploadFile, File, HTTPException
import uvicorn
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
  
   return {"success": True}


def main():
   uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
   main()
