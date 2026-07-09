import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
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
    # Cabeceras móviles e industriales para simular la app nativa y evitar bloqueos
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9',
        }
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=False)
            video_url = info.get('url') or info.get('formats', [{}])[-1].get('url')
            
            if not video_url:
                raise HTTPException(status_code=400, detail="No se pudo extraer la URL del video.")
            
            # MAGIA TÉCNICA: En lugar de darle la URL cruda de la red social al botón,
            # lo redirigimos a nuestra propia ruta /api/stream pasándole la url encriptada.
            # Esto soluciona de raíz el Error 403 en TikTok, Facebook, Instagram y X.
            dominio = os.environ.get("RENDER_EXTERNAL_URL", "http://localhost:8000")
            puente_url = f"{dominio}/api/stream?url={requests.utils.quote(video_url)}"
                
            return {
                "title": info.get('title', 'Video Detectado'),
                "thumbnail": info.get('thumbnail', 'https://placeholder.com'),
                "download_url": puente_url
            }
    except Exception as e:
        error_msg = str(e)
        if "Sign in to confirm" in error_msg:
            error_msg = "YouTube requiere verificación. Intenta con TikTok, Instagram, Facebook o X por el momento."
        raise HTTPException(status_code=500, detail=error_msg)

# NUEVA FUNCIÓN: Descarga el video en segundo plano y se lo entrega limpio al usuario
@app.get("/api/stream")
async def stream_video(url: str):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    }
    try:
        # Hacemos la petición en modo stream (por fragmentos)
        response = requests.get(url, headers=headers, stream=True, timeout=15)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="El servidor raíz denegó el acceso al archivo.")
        
        # Le enviamos el archivo en chunks de 1MB directo al navegador forzando la descarga
        return StreamingResponse(
            response.iter_content(chunk_size=1024 * 1024),
            media_type="video/mp4",
            headers={"Content-Disposition": "attachment; filename=snaptide_video.mp4"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el puente de descarga: {str(e)}")

@app.get("/")
async def read_index():
    return FileResponse('index.html')

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
