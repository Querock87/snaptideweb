import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import yt_dlp

app = FastAPI()

# Esto permite que tu diseño visual se conecte con el motor Python sin bloqueos
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
    # Configuración inteligente para extraer videos (y TikTok sin marca de agua)
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
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
        raise HTTPException(status_code=500, detail=str(e))

# Le dice al servidor que muestre tu diseño de Claude al abrir la página
@app.get("/")
async def read_index():
    return FileResponse('index.html')

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
