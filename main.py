import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import yt_dlp

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
    # Configuración avanzada para saltar bloqueos de YouTube ("Sign in to confirm you're not a bot")
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
        # Estas 3 líneas le dicen a YouTube que somos un navegador web real y corriente
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        },
        'nocheckcertificate': True,
        'geo_bypass': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=False)
            video_url = info.get('url') or info.get('formats', [{}])[-1].get('url')
            
            if not video_url:
                raise HTTPException(status_code=400, detail="No se pudo obtener la URL de descarga.")
                
            return {
                "title": info.get('title', 'Video Detectado'),
                "thumbnail": info.get('thumbnail', 'https://placeholder.com'),
                "download_url": video_url
            }
    except Exception as e:
        # Simplificamos el error en pantalla si algo falla
        error_msg = str(e)
        if "Sign in to confirm" in error_msg:
            error_msg = "YouTube requiere verificación. Intenta con otro enlace o red social por el momento."
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/")
async def read_index():
    return FileResponse('index.html')

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

