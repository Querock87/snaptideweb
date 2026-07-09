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
    # Forzamos a yt-dlp a buscar el formato directo de video más compatible y limpio
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Origin': 'https://tiktok.com',
            'Referer': 'https://tiktok.com/',
        }
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=False)
            
            # Buscamos la URL directa del archivo mp4 libre de marcas de agua
            video_url = None
            if 'formats' in info:
                # Buscamos formatos que no requieran procesamiento extra del servidor
                for f in reversed(info['formats']):
                    if f.get('vcodec') != 'none' and f.get('acodec') != 'none' and f.get('url'):
                        video_url = f['url']
                        break
            
            if not video_url:
                video_url = info.get('url')

            if not video_url:
                raise HTTPException(status_code=400, detail="No se pudo extraer la URL del video.")
                
            return {
                "title": info.get('title', 'Video Detectado'),
                "thumbnail": info.get('thumbnail', 'https://placeholder.com'),
                "download_url": video_url
            }
    except Exception as e:
        error_msg = str(e)
        if "Sign in to confirm" in error_msg:
            error_msg = "YouTube requiere verificación de seguridad. Intenta con otra red social."
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/")
async def read_index():
    return FileResponse('index.html')

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
