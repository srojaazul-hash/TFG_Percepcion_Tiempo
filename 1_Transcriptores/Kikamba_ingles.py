import os
import time
import json
import logging
from PIL import Image
from google import genai
from google.genai import types
from dotenv import load_dotenv, find_dotenv

# ==========================================
# 0. CONFIGURACIÓN MULTICLAVE SEGURA
# ==========================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
load_dotenv(find_dotenv())

lista_claves = [
    os.getenv("CLAVE_GEMINI_1"),
    os.getenv("CLAVE_GEMINI_2"),
    os.getenv("CLAVE_GEMINI_3"),
    os.getenv("CLAVE_GEMINI_4")
]
lista_claves = [clave for clave in lista_claves if clave is not None and clave.strip() != ""]

if not lista_claves:
    logging.error("❌ ERROR CRÍTICO: No se encontró ninguna clave válida en el .env.")
    exit()

indice_clave = 0
cliente = genai.Client(api_key=lista_claves[indice_clave])

# RUTAS EXACTAS
carpeta_imagenes = r"C:\Users\Usuario\Desktop\TFG\Documentos_para_percepción_tiempo\Lindblom\VOL_1\imagenes_paginas"
dir_kikamba = r"C:\Users\Usuario\Desktop\TFG\Documentos_para_percepción_tiempo\Lindblom\VOL_1\Textos_Kikamba"
dir_ingles = r"C:\Users\Usuario\Desktop\TFG\Documentos_para_percepción_tiempo\Lindblom\VOL_1\Textos_ingles"

os.makedirs(dir_kikamba, exist_ok=True)
os.makedirs(dir_ingles, exist_ok=True)

config_estricta = types.GenerateContentConfig(
    temperature=0.0, 
    seed=42,
    response_mime_type="application/json"
)

# ==========================================
# PROMPT DE EXTRACCIÓN (RESTRICCIÓN FILOLÓGICA 1910-1920)
# ==========================================
prompt_extraccion = """
Misión: Transcripción filológica estricta de textos históricos (1910-1920).

Vas a recibir la imagen de una página de un libro. El texto es interlineal: una línea impresa en Kikamba antiguo e inmediatamente debajo su traducción al inglés.

REGLAS DE ORO:
1. EXTRACCIÓN VISUAL (LÍNEA A LÍNEA): Está absolutamente PROHIBIDO agrupar oraciones. Extrae el texto exactamente como está impreso físicamente. Cada línea visual de la imagen debe ser un elemento en tu lista. Si una línea termina a mitad de una palabra, córtala ahí.
2. ORTOGRAFÍA HISTÓRICA INTACTA: Está estrictamente PROHIBIDO normalizar, corregir o modernizar la ortografía. Debes conservar las inconsistencias de los etnógrafos de 1910. 
   ATENCIÓN OBLIGATORIA A ESTOS CARACTERES:
   - Vocales antiguas: 'æ' (no la conviertas en e), 'ı' (i sin punto, no le pongas punto), 'ε', 'ə'.
   - Consonantes y diacríticos: 'ꝑ' (p con raya), 'ŋ' (letra eng, no pongas ng), 'ñ', 'ṣ', 'ṭ', 'ḍ', 'ḷ', 'ṃ', 'ṇ', 'y', 'yy'.
   - Variantes dialectales: Mantén el uso de las letras 'c' y 'r' exactamente donde aparezcan, no las elimines.
   - Vocales múltiples: Respeta las secuencias largas de vocales juntas (ej. uua, uaa) sin intentar arreglarlas.
3. FORMATO DE SALIDA: Extrae todas las líneas físicas de Kikamba por un lado, y todas las líneas físicas de Inglés por otro, manteniendo el orden cronológico de arriba a abajo.

Devuelve ESTRICTAMENTE este JSON:
{
  "kikamba": ["línea visual 1 kikamba", "línea visual 2 kikamba", ...],
  "ingles": ["línea visual 1 inglés", "línea visual 2 inglés", ...]
}
Si no hay texto de un idioma, devuelve [].
"""

def extraer_textos():
    global cliente, indice_clave
    
    imagenes = sorted([f for f in os.listdir(carpeta_imagenes) if f.endswith('.png')], 
                      key=lambda x: int(x.split('_')[1].split('.')[0]))
    
    if not imagenes: 
        return logging.warning("No hay imágenes en la carpeta para procesar.")

    kikamba_total = []
    ingles_total = []

    for nombre_img in imagenes:
        ruta_img = os.path.join(carpeta_imagenes, nombre_img)
        intentos = 0
        exito = False
        
        while intentos < len(lista_claves) and not exito:
            try:
                logging.info(f"Procesando: {nombre_img} (Clave {indice_clave + 1})")
                img = Image.open(ruta_img)

                respuesta = cliente.models.generate_content(
                    model='gemini-2.5-flash', 
                    contents=[prompt_extraccion, img], 
                    config=config_estricta
                )

                contenido_json = json.loads(respuesta.text)
                k_pagina = contenido_json.get("kikamba", [])
                i_pagina = contenido_json.get("ingles", [])
                
                kikamba_total.extend(k_pagina)
                ingles_total.extend(i_pagina)
                
                logging.info(f"   ✅ Extraídas {len(k_pagina)} líneas físicas en Kikamba y {len(i_pagina)} en Inglés.")
                exito = True 

            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    logging.warning(f"   ⚠️ Cuota agotada en la Clave {indice_clave + 1}.")
                    indice_clave += 1
                    
                    if indice_clave < len(lista_claves):
                        logging.info(f"   🔄 Rotando a la Clave {indice_clave + 1}...")
                        cliente = genai.Client(api_key=lista_claves[indice_clave])
                        intentos += 1
                        time.sleep(2)
                    else:
                        logging.error("\n❌ SE HAN AGOTADO TODAS LAS CLAVES. Guardando progreso parcial...")
                        guardar_archivos(kikamba_total, ingles_total)
                        return 
                else:
                    logging.error(f"   ❌ ERROR en {nombre_img}: {error_msg}")
                    time.sleep(5)
                    break 

        if exito:
            time.sleep(4)

    guardar_archivos(kikamba_total, ingles_total)

def guardar_archivos(kikamba_total, ingles_total):
    total_k = len(kikamba_total)
    total_i = len(ingles_total)
    
    logging.info(f"\n--- Resumen Final: {total_k} líneas en Kikamba | {total_i} líneas en Inglés ---")
    
    if total_k == 0 and total_i == 0:
        return logging.warning("No se extrajo texto válido.")

    tamano_chunk = 500
    max_lineas = max(total_k, total_i)

    for chunk_idx in range(0, max_lineas, tamano_chunk):
        num_archivo = (chunk_idx // tamano_chunk) + 1
        ruta_k = os.path.join(dir_kikamba, f"Kikamba_part_{num_archivo}.txt")
        ruta_i = os.path.join(dir_ingles, f"Ingles_part_{num_archivo}.txt")
        
        with open(ruta_k, 'w', encoding='utf-8') as f_k, open(ruta_i, 'w', encoding='utf-8') as f_i:
            for i in range(chunk_idx, min(chunk_idx + tamano_chunk, max_lineas)):
                linea_k = kikamba_total[i] if i < total_k else ""
                linea_i = ingles_total[i] if i < total_i else ""
                
                f_k.write(linea_k + '\n')
                f_i.write(linea_i + '\n')

    logging.info("✅ PROCESO FINALIZADO. Archivos guardados y sincronizados.")

if __name__ == "__main__":
    extraer_textos()