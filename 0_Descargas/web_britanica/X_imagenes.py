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
carpeta_descargas = r'C:\Users\Usuario\Desktop\TFG\Documentos_para_percepción_tiempo\Imagenes_crudas'
os.makedirs(carpeta_descargas, exist_ok=True)

# Lote de prueba súper rápido (¡Para descargar solo 1 imagen!)
PAGINA_INICIO = 15     # ¿Por qué página empezamos?
CUANTAS_DESCARGAR = 1  # ¿Cuántas descargamos en total?

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Referer': f'https://eap.bl.uk/archive-file/{id_coleccion}'
}

def descargar_imagen_prueba():
    manifest_url = f"https://eap.bl.uk/archive-file/{id_coleccion}/manifest"
    
    logging.info(f"Conectando al Archivo: {id_coleccion}...")
    
    try:
        respuesta = requests.get(manifest_url, headers=HEADERS, timeout=15)
        respuesta.raise_for_status()
        manifest = respuesta.json()
        
        # --- BUSCADOR TODOTERRENO DE PÁGINAS ---
        canvases = []
        if 'items' in manifest:
            canvases = manifest['items']
        elif 'sequences' in manifest:
            canvases = manifest['sequences'][0].get('canvases', [])
        
        total_reales = len(canvases)
        
        if total_reales == 0:
            return logging.error("❌ El mapa del archivo está vacío. Revisa el enlace.")

        # Aplicamos el recorte (Pág 15 a 15)
        inicio = PAGINA_INICIO - 1
        fin = inicio + CUANTAS_DESCARGAR
        fotos_seleccionadas = canvases[inicio:fin]
        
        logging.info(f"✅ ¡Conexión lograda! Detectadas {total_reales} páginas en total.")
        logging.info(f"🚀 Bajando lote de prueba ({len(fotos_seleccionadas)} imagen).\n")
        
        for i, item in enumerate(fotos_seleccionadas):
            num_pag_real = PAGINA_INICIO + i
            nombre_img = f"{id_coleccion}_{num_pag_real:03d}.jpg"
            ruta_guardado = os.path.join(carpeta_descargas, nombre_img)
            
            if os.path.exists(ruta_guardado):
                logging.info(f"Saltando {nombre_img}, ya existe.")
                continue
                
            try:
                # Extraer URL: El formato varía entre versiones, cubrimos ambas
                img_url_base = ""
                if 'items' in item: # Estructura v3
                    img_url_base = item['items'][0]['items'][0]['body']['service'][0]['@id']
                elif 'images' in item: # Estructura v2
                    img_url_base = item['images'][0]['resource']['service']['@id']
                
                if not img_url_base:
                    logging.error(f"No se encontró la imagen en la pág {num_pag_real}")
                    continue

                img_url = f"{img_url_base}/full/max/0/default.jpg"
                
                logging.info(f"Descargando: {nombre_img}...")
                
                img_req = requests.get(img_url, headers=HEADERS, stream=True, timeout=30)
                
                if img_req.status_code != 200:
                    img_url = f"{img_url_base}/full/full/0/default.jpg"
                    img_req = requests.get(img_url, headers=HEADERS, stream=True)

                img_req.raise_for_status()
                
                with open(ruta_guardado, 'wb') as f:
                    for chunk in img_req.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                time.sleep(1.5) 
                
            except Exception as e:
                logging.error(f"❌ Error en pág {num_pag_real}: {e}")

    except Exception as e:
        return logging.error(f"❌ Error de conexión: {e}")

    logging.info(f"\n✅ PROCESO COMPLETADO. Revisa tu carpeta 'Imagenes_crudas'.")

if __name__ == "__main__":
    descargar_imagen_prueba()