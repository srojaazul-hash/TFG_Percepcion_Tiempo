import os
import requests
import time
import logging

# ==========================================
# 0. CONFIGURACIÓN
# ==========================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# El ID de la colección
id_coleccion = "EAP782-1-1-1"

# La misma carpeta donde tu Archivero (Script 1) va a leer las fotos
carpeta_descargas = r'C:\Users\Usuario\Desktop\TFG\Documentos_para_percepción_tiempo\Imagenes_crudas'
os.makedirs(carpeta_descargas, exist_ok=True)

# Disfraz de navegador para no ser bloqueados
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Referer': f'https://eap.bl.uk/archive-file/{id_coleccion}'
}

def descargar_coleccion_completa():
    manifest_url = f"https://eap.bl.uk/archive-file/{id_coleccion}/manifest"
    
    logging.info(f"Conectando al archivo británico: {id_coleccion}")
    
    try:
        respuesta = requests.get(manifest_url, headers=HEADERS, timeout=15)
        respuesta.raise_for_status()
        manifest = respuesta.json()
        
        # Buscador todoterreno
        canvases = []
        if 'items' in manifest:
            canvases = manifest['items']
        elif 'sequences' in manifest:
            canvases = manifest['sequences'][0].get('canvases', [])
            
        total_imagenes = len(canvases)
        
        if total_imagenes == 0:
            return logging.error("❌ El mapa del archivo está vacío. Revisa el enlace.")
            
        logging.info(f"✅ ¡Se han detectado {total_imagenes} imágenes! Empezando descarga masiva...\n")
        
        for i, item in enumerate(canvases):
            nombre_img = f"{id_coleccion}_{i+1:03d}.jpg"
            ruta_guardado = os.path.join(carpeta_descargas, nombre_img)
            
            # Escudo antigasto
            if os.path.exists(ruta_guardado):
                logging.info(f"Saltando {nombre_img}, ya está en tu disco duro.")
                continue
                
            try:
                # Extraer URL (todoterreno)
                img_url_base = ""
                if 'items' in item: 
                    img_url_base = item['items'][0]['items'][0]['body']['service'][0]['@id']
                elif 'images' in item: 
                    img_url_base = item['images'][0]['resource']['service']['@id']
                
                if not img_url_base:
                    logging.error(f"No se encontró la imagen en la pág {i+1}")
                    continue

                img_url = f"{img_url_base}/full/max/0/default.jpg"
                
                logging.info(f"Descargando [{i+1}/{total_imagenes}]: {nombre_img}...")
                
                img_req = requests.get(img_url, headers=HEADERS, stream=True, timeout=30)
                
                if img_req.status_code != 200:
                    img_url = f"{img_url_base}/full/full/0/default.jpg"
                    img_req = requests.get(img_url, headers=HEADERS, stream=True)

                img_req.raise_for_status()
                
                with open(ruta_guardado, 'wb') as f:
                    for chunk in img_req.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # Pausa de cortesía
                time.sleep(1.5) 
                
            except Exception as e:
                logging.error(f"❌ Error en pág {i+1}: {e}")

    except Exception as e:
        return logging.error(f"❌ Error de conexión: {e}")

    logging.info("\n✅ DESCARGA COMPLETADA. Ya puedes lanzar el Script 1 (El Archivero).")

if __name__ == "__main__":
    descargar_coleccion_completa()