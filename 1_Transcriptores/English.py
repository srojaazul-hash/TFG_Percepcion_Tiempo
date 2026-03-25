import os
import time
import logging
from PIL import Image
from google import genai
from google.genai import types
from dotenv import load_dotenv, find_dotenv

# ==========================================
# 0. CONFIGURACIÓN MULTICLAVE SEGURA
# ==========================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# El "perro rastreador" buscará el .env aunque el script esté en una subcarpeta
load_dotenv(find_dotenv())

# Creamos la lista llamando a las variables secretas
lista_claves = [
    os.getenv("CLAVE_GEMINI_1"),
    os.getenv("CLAVE_GEMINI_2"),
    os.getenv("CLAVE_GEMINI_3"),
    os.getenv("CLAVE_GEMINI_4")
]

# Filtramos por si acaso alguna clave está en blanco en el .env
lista_claves = [clave for clave in lista_claves if clave is not None and clave.strip() != ""]

# PARACAÍDAS DE SEGURIDAD
if not lista_claves:
    logging.error("❌ ERROR CRÍTICO: No se ha encontrado ninguna clave válida en el archivo .env.")
    logging.info("Verifica que el archivo se llame '.env' y que las claves estén bien escritas.")
    exit() # Detiene el programa de forma segura

indice_clave = 0
cliente = genai.Client(api_key=lista_claves[indice_clave])

carpeta_imagenes = r'C:\Users\Usuario\Desktop\TFG\Documentos_para_percepción_tiempo\Imagenes_crudas'
carpeta_maestros = r'C:\Users\Usuario\Desktop\TFG\Documentos_para_percepción_tiempo\Transcripciones_Maestras'
os.makedirs(carpeta_maestros, exist_ok=True)

config_estricta = types.GenerateContentConfig(temperature=0.0, seed=42)

# ==========================================
# LOS 2 AGENTES DE DIGITALIZACIÓN
# ==========================================
prompt_fase_1 = """
Misión: Transcripción bruta (OCR).
Transcribe el texto de la imagen exactamente como lo ves. No corrijas nada, no formatees. Solo extrae las letras.
"""

# NUEVO PROMPT FASE 2: SECUENCIAL Y POR DOCUMENTO
prompt_fase_2 = """
Misión: Filología y Estructuración Secuencial para Minería de Datos Históricos.

Vas a recibir una transcripción bruta de una página manuscrita. Esta página puede contener MÚLTIPLES comunicaciones distintas (cartas, oficios, notas administrativas) una debajo de la otra.

TU REGLA DE ORO ES LA SECUENCIALIDAD: Analiza el texto de arriba a abajo. MANTÉN agrupados los elementos de cada comunicación individual. PROHIBIDO mezclar o agregar todos los membretes al principio si pertenecen a cartas distintas.

Sigue estos pasos estrictamente:
1. Corrige errores evidentes de lectura y SEPARA LAS PALABRAS que el OCR haya pegado por error.
2. Unifica la ortografía de nombres propios y lugares.
3. Para CADA comunicación individual que detectes en la página (Carta 1, luego Carta 2, etc.), aplica OBLIGATORIAMENTE y SECUENCIALMENTE esta estructura de tres bloques con sus títulos exactos:

[MEMBRETE Y FECHAS ADMINISTRATIVAS]
(Texto administrativo de la carta en cuestión)
[CUERPO NARRATIVO]
(Texto del mensaje principal de la carta en cuestión)
[FIRMAS Y DESPEDIDA]
(Texto del cierre y firma de la carta en cuestión)

Si hay una segunda comunicación más abajo en la página, repite exactamente los mismos bloques con sus datos correspondientes inmediatamente después.

REGLAS ESTRICTAS DE FORMATO:
- Debe haber un salto de línea antes y después de cada título de bloque.
- PROHIBIDO añadir saludos, preámbulos o confirmaciones ("Aquí tienes la transcripción..."). Devuelve SOLO la transcripción.
- MANTÉN INTACTOS los saltos de línea originales del documento dentro de cada bloque.
"""

def ejecutar_archivo_maestro():
    global cliente, indice_clave
    
    imagenes = [f for f in os.listdir(carpeta_imagenes) if f.endswith(('.jpg', '.png', '.jpeg'))]
    if not imagenes: 
        return logging.warning("No hay imágenes en la carpeta.")

    for nombre_img in imagenes:
        ruta_img = os.path.join(carpeta_imagenes, nombre_img)
        nombre_base = os.path.splitext(nombre_img)[0]
        ruta_txt = os.path.join(carpeta_maestros, f"{nombre_base}_MAESTRO.txt")

        if os.path.exists(ruta_txt):
            logging.info(f"Saltando {nombre_img}, el maestro ya existe.")
            continue
        
        intentos = 0
        exito = False
        
        while intentos < len(lista_claves) and not exito:
            try:
                logging.info(f"\n--- Digitalizando Maestro: {nombre_img} (Usando Clave {indice_clave + 1}) ---")
                img = Image.open(ruta_img)

                logging.info("   [Agente 1] Extrayendo texto bruto (OCR)...")
                txt_bruto = cliente.models.generate_content(
                    model='gemini-2.5-flash', contents=[prompt_fase_1, img], config=config_estricta
                ).text.strip()

                time.sleep(3)

                logging.info("   [Agente 2] Estructurando secuencialmente y limpiando ortografía...")
                txt_maestro = cliente.models.generate_content(
                    model='gemini-2.5-flash', contents=[prompt_fase_2, f"TEXTO BRUTO:\n{txt_bruto}"], config=config_estricta
                ).text.strip()

                with open(ruta_txt, 'w', encoding='utf-8') as f:
                    f.write(txt_maestro)
                
                logging.info(f"   ✅ Archivo Maestro Creado de forma secuencial: {nombre_base}_MAESTRO.txt")
                exito = True 

            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    logging.warning(f"   ⚠️ Cuota agotada en la Clave {indice_clave + 1}.")
                    indice_clave += 1
                    
                    if indice_clave < len(lista_claves):
                        logging.info(f"   🔄 Rotando a la Clave {indice_clave + 1} y reintentando...")
                        cliente = genai.Client(api_key=lista_claves[indice_clave])
                        intentos += 1
                        time.sleep(2)
                    else:
                        logging.error("\n❌ SE HAN AGOTADO TODAS LAS CLAVES POR HOY. Terminando proceso.")
                        return 
                else:
                    logging.error(f"   ❌ ERROR DESCONOCIDO en {nombre_img}: {error_msg}")
                    # PARACAÍDAS: Si la imagen está corrupta, esperamos 5 seg para no ametrallar a Google
                    time.sleep(5)
                    break 

        if exito:
            time.sleep(15) 

    logging.info("\n✅ PROCESO DE DIGITALIZACIÓN FINALIZADO.")

if __name__ == "__main__":
    ejecutar_archivo_maestro()