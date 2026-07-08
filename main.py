import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
import yt_dlp
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VideoRequest(BaseModel):
    url: str

@app.post("/api/download")
async def get_video_info(request: VideoRequest):
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=False)
            video_url = info.get('url') or info.get('formats', [{}])[-1].get('url')
            
            if not video_url:
                raise HTTPException(status_code=400, detail="No se pudo obtener la URL de descarga.")
            
            # ATENCIÓN: En lugar de darle la URL de TikTok al botón verde,
            # lo mandamos a nuestra propia ruta interna para evadir el Error 403.
            servidor_url = f"/api/stream?url={requests.utils.quote(video_url)}"
                
            return {
                "title": info.get('title', 'Video Detectado'),
                "thumbnail": info.get('thumbnail', 'https://placeholder.com'),
                "download_url": servidor_url
            }
    except Exception as e:
        error_msg = str(e)
        if "Sign in to confirm" in error_msg:
            error_msg = "YouTube requiere verificación. Intenta con TikTok, Instagram o Facebook."
        raise HTTPException(status_code=500, detail=error_msg)

# NUEVA FUNCIÓN: Sirve como puente para descargar el video sin que TikTok lo bloquee
@app.get("/api/stream")
async def stream_video(url: str):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    try:
        req = requests.get(url, headers=headers, stream=True)
        if req.status_code != 200:
            raise HTTPException(status_code=400, detail="Error al conectar con el servidor raíz del video.")
            
        return StreamingResponse(
            req.iter_content(chunk_size=1024*1024), 
            media_type="video/mp4",
            headers={"Content-Disposition": "attachment; filename=video.mp4"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def read_index():
    return FileResponse('index.html')

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)


