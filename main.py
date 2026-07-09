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

# 🔑 REEMPLAZA ESTO: Pega aquí adentro tu clave exacta sin modificar nada más
RAPIDAPI_KEY = "d4055fc609mshc798e684649e1dfp15e096jsn072162488ad6"

class VideoRequest(BaseModel):
    url: str

@app.post("/api/download")
async def get_video_info(request: VideoRequest):
    url_usuario = request.url.strip()
    
    api_url = "https://rapidapi.com"
    
    # Limpiamos exhaustivamente la clave para eliminar cualquier espacio fantasma
    llave_limpia = RAPIDAPI_KEY.replace('"', '').replace("'", "").strip()
    
    headers = {
        "x-rapidapi-key": llave_limpia,
        "x-rapidapi-host": "://rapidapi.com",
        "Content-Type": "application/json"
    }
    
    payload = {
        "url": url_usuario
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=25)
        
        if response.status_code == 403:
            raise HTTPException(
                status_code=403,
                detail="RapidAPI rechazó la clave en producción. Verifica que esté bien copiada en tu archivo main.py de GitHub."
            )
            
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code, 
                detail=f"La API respondió con error de sistema (Código {response.status_code})."
            )
            
        data = response.json()
        
        # Mapeo preciso según la estructura de respuesta exitosa de la API
        title = data.get("title") or data.get("caption") or data.get("description") or "Video Detectado"
        thumbnail = data.get("thumbnail") or data.get("cover") or "https://placeholder.com"
        
        # Analizamos la lista 'medias' donde vienen los enlaces de descarga directa
        download_url = None
        medias = data.get("medias")
        
        if isinstance(medias, list) and len(medias) > 0:
            # Buscamos el primer enlace de la lista que contenga la URL de descarga
            download_url = medias[0].get("url")
        else:
            # Respuestas alternativas directas
            download_url = data.get("url") or data.get("video") or data.get("download_url")

        if not download_url:
            raise HTTPException(
                status_code=400, 
                detail="Se procesó la solicitud, pero la API no arrojó un enlace .mp4 válido."
            )
            
        return {
            "title": title,
            "thumbnail": thumbnail,
            "download_url": download_url
        }
        
    except requests.exceptions.JSONDecodeError:
        raise HTTPException(status_code=502, detail="Error de respuesta: Estructura de datos ilegible.")
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fallo del sistema: {str(e)}")

@app.get("/")
async def read_index():
    return FileResponse('index.html')

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
