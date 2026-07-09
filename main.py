import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔑 REEMPLAZA ESTO: Pega aquí adentro tu clave "X-RapidAPI-Key"
RAPIDAPI_KEY = "Td4055fc609mshc798e684649e1dfp15e096jsn072162488ad6"

class VideoRequest(BaseModel):
    url: str

@app.post("/api/download")
async def get_video_info(request: VideoRequest):
    url_usuario = request.url.strip()
    
    # URL oficial del endpoint de la API que seleccionaste
    api_url = "https://rapidapi.com"
    
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": "download-all-in-one-reseller.p.rapidapi.com",
        "Content-Type": "application/json"
    }
    
    payload = {
        "url": url_usuario
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=15)
        data = response.json()
        
        # Estructura típica de respuesta exitosa de esta API
        if response.status_code != 200 or not data.get("success", True):
            raise HTTPException(status_code=400, detail="La API no logró extraer este video. Revisa que no sea privado.")
        
        # Extraemos la información del video procesado
        result = data.get("result", {})
        
        # Buscamos el enlace del video (priorizando links de alta calidad)
        video_url = result.get("video_url") or result.get("url")
        if isinstance(result.get("links"), list) and len(result["links"]) > 0:
            video_url = result["links"][0].get("url") or video_url

        if not video_url:
            raise HTTPException(status_code=400, detail="No se localizó un enlace de descarga válido.")

        return {
            "title": result.get("title") or result.get("description") or "Video Detectado",
            "thumbnail": result.get("thumbnail") or result.get("cover") or "https://placeholder.com",
            "download_url": video_url
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el puente de la API: {str(e)}")

@app.get("/")
async def read_index():
    return FileResponse('index.html')

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
