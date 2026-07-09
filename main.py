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

# 🔑 REEMPLAZA ESTO: Asegúrate de pegar bien tu clave sin la "T" extra
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
                detail=f"La API respondió con error de sistema (Código {response.status_code})."
            )
            
        data = response.json()
        
        # 🕵️‍♂️ BÚSQUEDA INTELIGENTE DE ENLACES (Proxy Adaptable)
        download_url = None
        title = "Video Detectado"
        thumbnail = "https://placeholder.com"
        
        # Escenario 1: Si la API devuelve los enlaces en una lista llamada 'medias'
        if "medias" in data and isinstance(data["medias"], list) and len(data["medias"]) > 0:
            # Buscamos el enlace dentro del primer objeto de la lista
            primer_medio = data["medias"][0]
            download_url = primer_medio.get("url") or primer_medio.get("video")
        
        # Escenario 2: Si la API mete la información dentro de un contenedor llamado 'result' o 'data'
        elif "result" in data and isinstance(data["result"], dict):
            res = data["result"]
            download_url = res.get("video") or res.get("url") or res.get("download_url")
            title = res.get("title") or res.get("description") or title
            thumbnail = res.get("thumbnail") or res.get("cover") or thumbnail
            
            # Revisamos si dentro de result también venía la lista de medias
            if not download_url and "medias" in res and isinstance(res["medias"], list) and len(res["medias"]) > 0:
                download_url = res["medias"][0].get("url")
                
        # Escenario 3: Si la API entrega los datos de forma directa en la raíz
        else:
            download_url = data.get("video") or data.get("url") or data.get("download_url")
            
        # Rescatamos título o miniatura genéricos si están en la raíz
        title = data.get("title") or data.get("description") or data.get("caption") or title
        thumbnail = data.get("thumbnail") or data.get("cover") or thumbnail

        # 🚨 Si después de buscar por todos lados no hay URL, te mostramos la respuesta real para saber qué campos usa
        if not download_url:
            # Cortamos el texto por si es muy largo
            snippet = str(data)[:150]
            raise HTTPException(
                status_code=422, 
                detail=f"Enlace no hallado en la respuesta. Estructura recibida: {snippet}"
            )
            
        return {
            "title": title,
            "thumbnail": thumbnail,
            "download_url": download_url
        }
        
    except requests.exceptions.JSONDecodeError:
        raise HTTPException(status_code=502, detail="Error de formato: Respuesta ilegible de la API.")
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
