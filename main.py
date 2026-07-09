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

# 🔑 REEMPLAZA ESTO: Pega aquí adentro tu clave secreta "X-RapidAPI-Key"
RAPIDAPI_KEY = "Td4055fc609mshc798e684649e1dfp15e096jsn072162488ad6"

class VideoRequest(BaseModel):
    url: str

@app.post("/api/download")
async def get_video_info(request: VideoRequest):
    url_usuario = request.url.strip()
    
    # 🎯 DATOS EXACTOS QUE ENCONTRASTE EN LA PÁGINA DE LA API
    api_url = "https://auto-download-all-in-one.p.rapidapi.com/v1/social/autolink"
    
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": "auto-download-all-in-one.p.rapidapi.com",
        "Content-Type": "application/json"
    }
    
    payload = {
        "url": url_usuario
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=25)
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code, 
                detail=f"La API respondió con error {response.status_code}. Verifica tu clave de RapidAPI."
            )
            
        data = response.json()
        
        # Analizamos la respuesta típica de este endpoint específico
        # Normalmente devuelven un objeto con la información del video
        title = data.get("title") or data.get("caption") or "Video Descargado"
        thumbnail = data.get("thumbnail") or data.get("cover") or "https://placeholder.com"
        
        # Buscamos el enlace del video dentro de la respuesta (puede venir directo o en una lista)
        download_url = data.get("video") or data.get("url") or data.get("download_url")
        
        # Si viene dentro de una lista de medios/links ("medias" o "links")
        if not download_url and "medias" in data:
            medias = data["medias"]
            if isinstance(medias, list) and len(medias) > 0:
                download_url = medias[0].get("url")
        
        if not download_url:
            # Si la estructura es un poco diferente, intentamos buscar cualquier campo que tenga la URL
            raise HTTPException(status_code=400, detail="No se encontró un enlace MP4 directo en la respuesta de la API.")
            
        return {
            "title": title,
            "thumbnail": thumbnail,
            "download_url": download_url
        }
        
    except requests.exceptions.JSONDecodeError:
        raise HTTPException(
            status_code=502, 
            detail="Error de formato: La API sigue sin responder en formato JSON limpio."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar: {str(e)}")

@app.get("/")
async def read_index():
    return FileResponse('index.html')

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
