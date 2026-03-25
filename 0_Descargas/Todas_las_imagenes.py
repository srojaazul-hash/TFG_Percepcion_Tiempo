import os
import requests
import time
import logging

# ==========================================
# 0. CONFIGURACIÓN
# ==========================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# El enlace exacto que quieres descargar (puedes cambiarlo por el de otras cartas en el futuro)
enlace_archivo = "https://eap.bl.uk/archive-file/EAP782-1-1-1"

# La misma carpeta donde tu Archivero (Script 1) va a leer las fotos
carpeta_descargas = r'C:\Users\Usuario\Desktop\TFG\Documentos_para_percepción_tiempo\Imagenes_crudas'
os.makedirs(carpeta_descargas, exist_ok=True)

def descargar_coleccion():
    # El truco para acceder a las tripas del museo: añadir "/manifest" al final
    manifest_url = enlace_archivo.rstrip('/') + "/manifest"
    nombre_coleccion = enlace_archivo.split('/')[-1]
    
    logging.info(f"Conectando al archivo británico: {nombre_coleccion}")
    
    try:
        respuesta = requests.get(manifest_url)
        respuesta.raise_for_status()
        manifest = respuesta.json()
    except Exception as e:
        return logging.error(f"❌ No se pudo conectar con el archivo. ¿Es correcto el enlace? Error: {e}")

    # Buceamos en el código del museo para encontrar la lista de páginas
    canvases = manifest.get('sequences', [{}])[0].get('canvases', [])
    total_imagenes = len(canvases)
    
    if total_imagenes == 0:
        return logging.warning("❌ No se han encontrado imágenes en este documento.")
        
    logging.info(f"✅ ¡Se han detectado {total_imagenes} imágenes! Empezando descarga masiva...\n")
    
    for i, canvas in enumerate(canvases):
        # Nombramos la foto con formato ordenado: EAP782-1-1-1_001.jpg
        nombre_img = f"{nombre_coleccion}_{i+1:03d}.jpg"
        ruta_guardado = os.path.join(carpeta_descargas, nombre_img)
        
        # El mismo escudo antigasto: si la foto ya está descargada, la saltamos
        if os.path.exists(ruta_guardado):
            logging.info(f"Saltando {nombre_img}, ya está en tu disco duro.")
            continue
            
        try:
            # Magia IIIF para pedir la foto a máxima resolución sin marcas de agua
            resource = canvas['images'][0]['resource']
            if 'service' in resource and '@id' in resource['service']:
                base_img_url = resource['service']['@id']
                # Intentamos sacar la versión gigante ('max')
                img_url = f"{base_img_url}/full/max/0/default.jpg"
            else:
                img_url = resource['@id']
                
            logging.info(f"Descargando [{i+1}/{total_imagenes}]: {nombre_img}...")
            
            img_req = requests.get(img_url, stream=True)
            
            # Algunos servidores antiguos prefieren la orden 'full' en lugar de 'max'
            if img_req.status_code == 400:
                img_url = f"{base_img_url}/full/full/0/default.jpg"
                img_req = requests.get(img_url, stream=True)
                
            img_req.raise_for_status()
            
            # Guardamos la imagen en tu carpeta
            with open(ruta_guardado, 'wb') as f:
                for chunk in img_req.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            # Pausa de 1 segundo por cortesía con el servidor británico para que no nos bloquee
            time.sleep(1) 
            
        except Exception as e:
            logging.error(f"❌ Error al descargar {nombre_img}: {e}")
            time.sleep(2)

    logging.info("\n✅ DESCARGA COMPLETADA. Ya puedes lanzar el Script 1 (El Archivero).")

if __name__ == "__main__":
    descargar_coleccion()