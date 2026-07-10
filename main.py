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

# 🔑 REEMPLAZA ESTO: Tu clave limpia (la que empieza con d4055f... en tu captura)
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
        
        # 🎯 EXTRACCIÓN DIRECTA DESDE LA RAÍZ DEL JSON
        # Esta API entrega los links principales directamente en la base del objeto
        download_url = data.get("url") or data.get("video") or data.get("download_url")
        title = data.get("title") or data.get("caption") or data.get("description") or "Video Detectado"
        thumbnail = data.get("thumbnail") or data.get("cover") or "https://placeholder.com"
        
        # Guardamos calidades secundarias si existieran
        lista_calidades = data.get("medias") or []
        
        # Si la URL principal no apareció arriba pero sí hay datos en 'medias', la extraemos de ahí
        if not download_url and isinstance(lista_calidades, list) and len(lista_calidades) > 0:
            primer_elemento = lista_calidades[0]
            if isinstance(primer_elemento, dict):
                download_url = primer_elemento.get("url") or primer_elemento.get("video")

        if not download_url:
            raise HTTPException(status_code=400, detail="La API no devolvió una URL válida de descarga para este video.")
            
        return {
            "title": title,
            "thumbnail": thumbnail,
            "download_url": download_url,
            "medias": lista_calidades if isinstance(lista_calidades, list) else []
        }
        
    except requests.exceptions.JSONDecodeError:
        raise HTTPException(status_code=502, detail="Error de procesamiento: La API no envió un formato legible.")
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fallo de servidor: {str(e)}")

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
