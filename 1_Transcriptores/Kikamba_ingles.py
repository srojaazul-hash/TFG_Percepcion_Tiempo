import os
import time
import json
import logging
from PIL import Image
from google import genai
from google.genai import types

# ==========================================
# CONFIGURACIÓN DE RUTAS Y CLAVES
# ==========================================
lista_claves = ['TU_CLAVE_1', 'TU_CLAVE_2', 'TU_CLAVE_3', 'TU_CLAVE_4']
indice_clave = 0

carpeta_imagenes = r"C:\Users\Usuario\Desktop\TFG\Documentos_para_percepción_tiempo\Lindblom\VOL_1\imagenes_paginas"
ruta_kikamba_txt = r"C:\Users\Usuario\Desktop\TFG\Documentos_para_percepción_tiempo\Lindblom\VOL_1\Textos_Kikamba\Kikamba_part_1.txt"
ruta_ingles_txt = r"C:\Users\Usuario\Desktop\TFG\Documentos_para_percepción_tiempo\Lindblom\VOL_1\Textos_ingles\Ingles_part_1.txt"

# Configuración de Logging para ver el progreso en tiempo real
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Cliente inicial
cliente = genai.Client(api_key=lista_claves[indice_clave])

# ==========================================
# PROMPT Y CONFIGURACIÓN IA
# ==========================================
prompt_extraccion = """
Eres un experto en transcripción paleográfica. Tu tarea es extraer el texto de esta página 
siguiendo un formato JSON estricto. La página contiene texto interlineal (Kikamba arriba, Inglés abajo).
Debes devolver una lista de strings para cada idioma, manteniendo el orden exacto.
IMPORTANTE: Respeta los caracteres especiales (como p con raya, s con punto debajo, etc.).
Formato de salida: {"kikamba": ["linea1", "linea2"], "ingles": ["linea1", "linea2"]}
"""

config_estricta = types.GenerateContentConfig(
    response_mime_type='application/json',
    temperature=0.1
)

def extraer_textos_blindado():
    global cliente, indice_clave
    
    # Obtener y ordenar imágenes
    try:
        imagenes = sorted([f for f in os.listdir(carpeta_imagenes) if f.endswith('.png')], 
                          key=lambda x: int(x.split('_')[1].split('.')[0]))
    except Exception as e:
        logging.error(f"Error al leer la carpeta de imágenes: {e}")
        return

    if not imagenes: 
        logging.warning("No hay imágenes en la carpeta.")
        return

    logging.info(f"--- Iniciando extracción de {len(imagenes)} páginas ---")

    for nombre_img in imagenes:
        ruta_img = os.path.join(carpeta_imagenes, nombre_img)
        exito_pagina = False
        intentos_claves = 0
        
        # Intentar procesar la página actual rotando claves si es necesario
        while intentos_claves < len(lista_claves) and not exito_pagina:
            try:
                logging.info(f"Analizando: {nombre_img} (Clave {indice_clave + 1})")
                img = Image.open(ruta_img)

                respuesta = cliente.models.generate_content(
                    model='gemini-2.0-flash', # O la versión que estés usando
                    contents=[prompt_extraccion, img], 
                    config=config_estricta
                )

                # Parsear JSON
                datos = json.loads(respuesta.text)
                k_lineas = datos.get("kikamba", [])
                i_lineas = datos.get("ingles", [])
                
                # --- GUARDADO INMEDIATO (MODO APPEND 'a') ---
                with open(ruta_kikamba_txt, 'a', encoding='utf-8') as f_k:
                    for l in k_lineas: f_k.write(l + "\n")
                
                with open(ruta_ingles_txt, 'a', encoding='utf-8') as f_i:
                    for l in i_lineas: f_i.write(l + "\n")
                
                logging.info(f"   ✅ {nombre_img} GUARDADA en disco.")
                exito_pagina = True 
                time.sleep(4) # Pausa de seguridad para no saturar RPM

            except Exception as e:
                error_str = str(e).upper()
                if "429" in error_str or "QUOTA" in error_str or "EXHAUSTED" in error_str:
                    logging.warning(f"   ⚠️ Clave {indice_clave + 1} agotada.")
                    indice_clave += 1
                    intentos_claves += 1
                    
                    if indice_clave < len(lista_claves):
                        logging.info(f"   🔄 Saltando a Clave {indice_clave + 1}...")
                        cliente = genai.Client(api_key=lista_claves[indice_clave])
                        time.sleep(2)
                    else:
                        logging.error("❌ TODAS LAS CLAVES AGOTADAS PARA HOY.")
                        return # Detiene el script por completo
                else:
                    logging.error(f"   ❌ Error inesperado en {nombre_img}: {e}")
                    time.sleep(5)
                    break # Salta a la siguiente imagen si el error no es de cuota

    logging.info("--- PROCESO FINALIZADO ---")

if __name__ == "__main__":
    extraer_textos_blindado()