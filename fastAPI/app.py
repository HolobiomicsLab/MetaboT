from fastapi import (
    FastAPI,
    UploadFile,
    File,
    Form,
    Header,
)
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from ..app.core.session import setup_logger
from ..app.core.session import create_user_session
from .models import WorkflowRequest


from .pipe import create_zip_buffer, process_workflow_request


logger = setup_logger("API logger")

app = FastAPI(title="MetaboT API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Specify the exact frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/workflow")
async def workflow_route(
    request_data: WorkflowRequest, authorization: str = Header(None)
) -> StreamingResponse:
    generator = process_workflow_request(
        request_data.prompt,
        request_data.session_id,
        authorization,
        request_data.endpoint_url,
    )
    return StreamingResponse(generator, media_type="text/event-stream")


@app.get("/api/download")
async def download_files(session_id: str) -> StreamingResponse:
    zip_buffer = create_zip_buffer(session_id)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="result.zip"'},
    )


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), session_id: str = Form(...)):
    # Import create_user_session from session module for file storage

    # Get the user input directory for the session (this call should create the directory if needed)
    user_input_dir = create_user_session(session_id, input_dir=True)
    user_input_dir.mkdir(parents=True, exist_ok=True)

    # Save the uploaded file to the session's input directory
    file_location = user_input_dir / file.filename
    with open(file_location, "wb") as f:
        content = await file.read()
        f.write(content)

    return {"message": "File uploaded and processed successfully"}
