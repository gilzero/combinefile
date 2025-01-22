from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
import pathlib
import logging

from app.core.concatenator import FileConcatenator
from app.models.schemas import ConcatenateRequest, FileConcatenationError

logger = logging.getLogger(__name__)

app = FastAPI(title="File Concatenator", description="Concatenates files respecting .gitignore rules")
templates = Jinja2Templates(directory="templates")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the home page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/concatenate")
async def concatenate_files(request: ConcatenateRequest):
    """Concatenate files in the specified directory."""
    try:
        concatenator = FileConcatenator(
            base_dir=request.directory,
            additional_ignores=request.additional_ignores
        )
        output_file = await concatenator.concatenate_files()
        
        return {
            "status": "success",
            "message": "Files concatenated successfully",
            "output_file": output_file,
            "statistics": concatenator.stats
        }
    except FileConcatenationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during concatenation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/download/{file_path:path}")
async def download_file(file_path: str):
    """Download a concatenated file."""
    try:
        # Ensure the file path is within the output directory
        output_dir = pathlib.Path(__file__).parent.parent.parent / "output"
        file_path = output_dir / file_path
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
            
        return FileResponse(
            path=file_path,
            filename=file_path.name,
            media_type="text/plain"
        )
    except Exception as e:
        logger.error(f"Error serving file: {e}")
        raise HTTPException(status_code=500, detail="Error serving file") 