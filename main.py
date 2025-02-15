from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp
from fastapi.responses import StreamingResponse
import requests

app = FastAPI()

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class DownloadRequest(BaseModel):
    url: str

@app.post("/get-download-link")
async def get_download_link(request: DownloadRequest = Body(...)):
    try:
        ydl_opts = {
            'format': '18/best',  # Using format 18 (360p mp4) as first choice
            'quiet': True,
            'no_warnings': True,
            'extractor_args': {'youtube': {'player_client': ['android']}},  # Try using android client
            'no_check_certificates': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=False)
            return {
                "title": info.get('title', 'video'),
                "url": info['url'],
            }
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/download")
async def download_video(url: str, title: str):
    try:
        def iterfile():
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        yield chunk

        headers = {
            'Content-Disposition': f'attachment; filename="{title}.mp4"'
        }
        
        return StreamingResponse(iterfile(), headers=headers, media_type='video/mp4')
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))