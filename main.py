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

# 🔑 Pega aquí adentro tu clave secreta "X-RapidAPI-Key"
RAPIDAPI_KEY = "Td4055fc609mshc798e684649e1dfp15e096jsn072162488ad6"

class VideoRequest(BaseModel):
    url: str

@app.post("/api/download")
async def get_video_info(request: VideoRequest):
    url_usuario = request.url.strip()
    
    # Endpoint oficial según la documentación de "Auto Download All In One"
    api_url = "https://rapidapi.com"
    
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": "download-all-in-one-reseller.p.rapidapi.com",
        "Content-Type": "application/json"
    }
    
    # El parámetro exacto que requiere esta API es "url"
    payload = {"url": url_usuario}
    
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=20)
        
        # 🔍 IMPRESIÓN DE SEGURIDAD: Esto se reflejará en la consola negra de Render
        print(f"ESTATUS DE RESPUESTA: {response.status_code}")
        print(f"TEXTO RECIBIDO: {response.text}")
        
        # Validamos si la API nos bloqueó temporalmente o envió error de servidor
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code, 
                detail=f"La API respondió con código {response.status_code}. Revisa tu suscripción en RapidAPI."
            )
            
        data = response.json()
        
        # La API suele estructurar todo dentro de un diccionario principal
        if not data:
            raise HTTPException(status_code=400, detail="La API devolvió un objeto vacío.")
            
        # Intentamos extraer los datos dinámicamente buscando variantes comunes del formato
        title = data.get("title") or data.get("description")
        thumbnail = data.get("thumbnail") or data.get("cover") or "https://placeholder.com"
        download_url = data.get("video_url") or data.get("url") or data.get("medias", [{}])[0].get("url")
        
        # Si los datos están dentro de un sub-bloque llamado 'result' o 'data'
        if "result" in data and isinstance(data["result"], dict):
            res = data["result"]
            title = title or res.get("title") or res.get("description")
            thumbnail = thumbnail or res.get("thumbnail") or res.get("cover")
            download_url = download_url or res.get("video_url") or res.get("url")
            
        if not download_url:
            raise HTTPException(status_code=400, detail="No se encontró un enlace directo para el archivo MP4.")
            
        return {
            "title": title or "Video de Redes Sociales",
            "thumbnail": thumbnail,
            "download_url": download_url
        }
        
    except requests.exceptions.JSONDecodeError:
        # Aquí atrapamos el error "line 1 column 1" y mostramos el texto real que causó la falla
        snippet = response.text[:100] if 'response' in locals() else "Sin respuesta"
        raise HTTPException(
            status_code=502, 
            detail=f"La API no envió un JSON válido. Envió: {snippet}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la petición: {str(e)}")

@app.get("/")
async def read_index():
    return FileResponse('index.html')

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
