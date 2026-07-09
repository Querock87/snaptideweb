@import os
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

# 🔑 REEMPLAZA ESTO: Tu clave exacta y limpia de RapidAPI (sin la T al principio)
RAPIDAPI_KEY = "d4055fc609mshc798e684649e1dfp15e096jsn072162488ad6"

class VideoRequest(BaseModel):
    url: str

@app.post("/api/download")
async def get_video_info(request: VideoRequest):
    url_usuario = request.url.strip()
    
    api_url = "https://auto-download-all-in-one.p.rapidapi.com/v1/social/autolink"
    
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY.replace('"', '').replace("'", "").strip(),
        "x-rapidapi-host": "auto-download-all-in-one.p.rapidapi.com",
        "Content-Type": "application/json"
    }
    
    payload = {"url": url_usuario}
    
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=25)
        
        # Si la respuesta no es exitosa, arrojamos el estatus explícito
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code, 
                detail=f"La API respondió con error de sistema (Código {response.status_code})."
            )
            
        data = response.json()
        
        # Extracción segura según la documentación oficial de la API
        title = data.get("title") or data.get("caption") or data.get("description") or "Video Detectado"
        thumbnail = data.get("thumbnail") or data.get("cover") or "https://placeholder.com"
        
        # Estructura del formato nativo de la API: data["medias"] es una lista de diccionarios
        lista_calidades = data.get("medias") or []
        download_url = data.get("url") or data.get("video")
        
        # Si la lista contiene elementos, extraemos de forma segura el primer enlace como principal
        if isinstance(lista_calidades, list) and len(lista_calidades) > 0:
            primer_elemento = lista_calidades[0]
            if isinstance(primer_elemento, dict):
                download_url = primer_elemento.get("url") or download_url
            
        if not download_url:
            raise HTTPException(status_code=400, detail="No se localizó un enlace MP4 en la respuesta.")
            
        return {
            "title": title,
            "thumbnail": thumbnail,
            "download_url": download_url,
            "medias": lista_calidades  # Mandamos la lista limpia a la interfaz
        }
        
    except requests.exceptions.JSONDecodeError:
        raise HTTPException(status_code=502, detail="Error de respuesta de red. Intenta nuevamente.")
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fallo del sistema: {str(e)}")
# NUEVA RUTA: Entrega el logo de la pestaña al navegador de forma segura
@app.get("/favicon.png")
async def get_favicon():
    return FileResponse('favicon.png')

@app.get("/")
async def read_index():
    return FileResponse('index.html')

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
