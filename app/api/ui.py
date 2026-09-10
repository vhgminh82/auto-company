from fastapi import APIRouter
from fastapi.responses import FileResponse, HTMLResponse

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def index_page():
    return FileResponse("app/static/index.html")
