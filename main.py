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

# 🔑 REEMPLAZA ESTO: Tu clave limpia (la que se ve en tus capturas)
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
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code, 
                detail=f"La API respondió con código de error {response.status_code}."
            )
            
        data = response.json()
        
        # 🎯 EXTRACCIÓN DE ACUERDO A TU CAPTURA DE POSTMAN
        title = data.get("title") or data.get("caption") or "Video Detectado"
        thumbnail = data.get("thumbnail") or data.get("cover") or "https://placeholder.com"
        
        lista_calidades = data.get("medias") or []
        download_url = None
        
        # Corrección crítica: Extraemos el primer objeto diccionario de la lista de calidades
        if isinstance(lista_calidades, list) and len(lista_calidades) > 0:
            primer_elemento = lista_calidades[0] # <-- Tomamos el primer elemento real [0]
            if isinstance(primer_elemento, dict):
                download_url = primer_elemento.get("url")
        
        # Si no vino en la lista, usamos la URL raíz de respaldo
        if not download_url:
            download_url = data.get("url")

        if not download_url:
            raise HTTPException(status_code=400, detail="No se localizó una URL de descarga válida en la API.")
            
        return {
            "title": title,
            "thumbnail": thumbnail,
            "download_url": download_url,
            "medias": lista_calidades if isinstance(lista_calidades, list) else []
        }
        
    except requests.exceptions.JSONDecodeError:
        raise HTTPException(status_code=502, detail="Error de respuesta: Estructura ilegible de la API.")
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fallo del sistema: {str(e)}")

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
