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

# 🔑 REEMPLAZA ESTO: Tu clave exacta de RapidAPI (la que empieza con d4055f...)
RAPIDAPI_KEY = "d4055fc609mshc798e684649e1dfp15e096jsn072162488ad6"

class VideoRequest(BaseModel):
    url: str

@app.post("/api/download")
async def get_video_info(request: VideoRequest):
    url_usuario = request.url.strip()
    
    api_url = "https://rapidapi.com"
    
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY.replace('"', '').replace("'", "").strip(),
        "x-rapidapi-host": "://rapidapi.com",
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
        
        # Extracción base desde tu captura de Postman
        title = data.get("title") or data.get("caption") or "Video Detectado"
        thumbnail = data.get("thumbnail") or data.get("cover") or "https://placeholder.com"
        
        lista_calidades = data.get("medias") or []
        download_url = None
        formatos_filtrados = []
        
        if isinstance(lista_calidades, list) and len(lista_calidades) > 0:
            # 🕵️‍♂️ FILTRADO SEGURO DE CÓDECS (Evita AV1 y formatos rotos)
            for media in lista_calidades:
                if not isinstance(media, dict):
                    continue
                
                url_formato = media.get("url")
                quality = str(media.get("quality", "")).lower()
                
                if not url_formato:
                    continue
                    
                # Si el formato es AV1 (deja pantalla negra en celulares), lo saltamos
                if "av1" in quality or "av01" in quality:
                    continue
                
                # Guardamos el formato en nuestra lista limpia de MP4 seguros
                formatos_filtrados.append(media)
            
            # Si nos quedaron formatos limpios tras el filtro, extraemos el primero
            if formatos_filtrados:
                download_url = formatos_filtrados[0].get("url")
        
        # Si la lista vino vacía o no hallamos el enlace en el filtro, usamos el enlace raíz de la API
        if not download_url:
            download_url = data.get("url") or data.get("video")

        if not download_url:
            raise HTTPException(status_code=400, detail="No se localizó una URL de descarga compatible en la API.")
            
        return {
            "title": title,
            "thumbnail": thumbnail,
            "download_url": download_url,
            "medias": formatos_filtrados if formatos_filtrados else lista_calidades
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
