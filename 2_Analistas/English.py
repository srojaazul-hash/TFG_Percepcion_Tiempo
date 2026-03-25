import os
import csv
import time
import logging
import re
from google import genai
from google.genai import types
from docx import Document
from docx.enum.text import WD_COLOR_INDEX
from dotenv import load_dotenv, find_dotenv

# ==========================================
# 0. CONFIGURACIÓN MULTICLAVE SEGURA
# ==========================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# El "perro rastreador" buscará el .env aunque el script esté en una subcarpeta
load_dotenv(find_dotenv())

lista_claves = [
    os.getenv("CLAVE_GEMINI_1"),
    os.getenv("CLAVE_GEMINI_2"),
    os.getenv("CLAVE_GEMINI_3"),
    os.getenv("CLAVE_GEMINI_4")
]

lista_claves = [clave for clave in lista_claves if clave is not None and clave.strip() != ""]

if not lista_claves:
    logging.error("❌ ERROR CRÍTICO: No se ha encontrado ninguna clave válida en el archivo .env.")
    exit() 

indice_clave = 0
cliente = genai.Client(api_key=lista_claves[indice_clave])

carpeta_maestros = r'C:\Users\Usuario\Desktop\TFG\Documentos_para_percepción_tiempo\Transcripciones_Maestras'
carpeta_resultados = r'C:\Users\Usuario\Desktop\TFG\Documentos_para_percepción_tiempo\Transcripciones_Analizadas'
archivo_csv = r'C:\Users\Usuario\Desktop\TFG\Documentos_para_percepción_tiempo\Documento_CVS\Base_de_datos_percepcion_tiempo.csv'

os.makedirs(carpeta_resultados, exist_ok=True)
os.makedirs(os.path.dirname(archivo_csv), exist_ok=True)

config_estricta = types.GenerateContentConfig(temperature=0.0, seed=42)

# ==========================================
# LOS 2 AGENTES DE ANÁLISIS
# ==========================================
prompt_fase_3 = """
Misión: Marcado Visual y Semántico de Textos Históricos Secuenciales.

Vas a recibir la transcripción de una página de archivo que puede contener UNA O VARIAS comunicaciones estructuradas en bloques.

REGLA DE ORO: Ignora por completo el texto bajo los bloques [MEMBRETE Y FECHAS ADMINISTRATIVAS] y [FIRMAS Y DESPEDIDA]. Analiza ÚNICAMENTE el texto que se encuentre dentro de TODOS los bloques [CUERPO NARRATIVO] que aparezcan en el documento.

1. Encuentra conceptos de Tiempo Sasa (ciclos, cosechas, clima, eventos naturales, antepasados, referencias relativas al presente) y envuélvelos así: <sasa>concepto</sasa>
2. Encuentra conceptos de Tiempo Lineal (horas, fechas exactas del calendario, plazos matemáticos, retrasos cuantificados) y envuélvelos así: <lineal>concepto</lineal>

Devuelve TODO el documento íntegro, manteniendo exactamente su estructura y saltos de línea originales, pero con las etiquetas inyectadas donde corresponda dentro de los cuerpos narrativos. Prohibido añadir preámbulos o traducciones.
"""

prompt_fase_4 = """
Misión: Auditoría y Cálculo Matemático.
Vas a recibir un texto marcado con etiquetas.
1. Extrae el AÑO y el LUGAR basándote en el PRIMER membrete del texto (si hay varios, coge el principal).
2. Cuenta cuántas veces aparece exactamente la etiqueta <sasa> (S) en TODO el documento.
3. Cuenta cuántas veces aparece exactamente la etiqueta <lineal> (L) en TODO el documento.
4. Calcula el Índice de Linealidad: L / (S + L) redondeado a 2 decimales. (Si S+L=0, pon "N/A").

FORMATO ESTRICTO DE SALIDA (Solo 1 línea con 5 valores separados por |):
[Año] | [Lugar] | [S] | [L] | [Índice]
"""

def crear_documento_word(ruta_guardado, nombre_base, anio, lugar, sasa, lineal, indice, texto_marcado):
    doc = Document()
    doc.add_heading(f'Análisis de Carta: {nombre_base}', 0)
    
    p_meta = doc.add_paragraph()
    p_meta.add_run(f"Año: ").bold = True
    p_meta.add_run(f"{anio} | ")
    p_meta.add_run(f"Lugar: ").bold = True
    p_meta.add_run(f"{lugar}\n")
    p_meta.add_run(f"Sasa: ").bold = True
    p_meta.add_run(f"{sasa} | ")
    p_meta.add_run(f"Lineal: ").bold = True
    p_meta.add_run(f"{lineal} | ")
    p_meta.add_run(f"Índice L/(S+L): ").bold = True
    p_meta.add_run(f"{indice}")
    
    doc.add_paragraph("_" * 50)
    
    p_texto = doc.add_paragraph()
    partes = re.split(r'(<sasa>.*?</sasa>|<lineal>.*?</lineal>)', texto_marcado, flags=re.DOTALL)
    
    for parte in partes:
        if parte.startswith('<sasa>'):
            texto_limpio = parte[6:-7]
            run = p_texto.add_run(texto_limpio)
            run.font.highlight_color = WD_COLOR_INDEX.BRIGHT_GREEN
        elif parte.startswith('<lineal>'):
            texto_limpio = parte[8:-9]
            run = p_texto.add_run(texto_limpio)
            run.font.highlight_color = WD_COLOR_INDEX.TURQUOISE
        else:
            p_texto.add_run(parte)
            
    doc.save(ruta_guardado)

def ejecutar_analista():
    global cliente, indice_clave
    
    archivos_txt = [f for f in os.listdir(carpeta_maestros) if f.endswith('.txt')]
    if not archivos_txt:
        return logging.warning("No hay archivos .txt maestros para analizar.")

    if not os.path.exists(archivo_csv):
        with open(archivo_csv, mode='w', newline='', encoding='utf-8') as f_csv:
            escritor = csv.writer(f_csv, delimiter=';')
            escritor.writerow(['Archivo', 'Anio', 'Lugar', 'Marcadores_Sasa', 'Marcadores_Lineales', 'Indice_Linealidad'])

    for archivo in archivos_txt:
        ruta_txt = os.path.join(carpeta_maestros, archivo)
        nombre_base = archivo.replace('_MAESTRO.txt', '')
        ruta_docx = os.path.join(carpeta_resultados, f"{nombre_base}_Analizado.docx")

        if os.path.exists(ruta_docx):
            logging.info(f"Saltando {nombre_base}, ya está analizado.")
            continue
        
        intentos = 0
        exito = False
        
        while intentos < len(lista_claves) and not exito:
            try:
                logging.info(f"\n--- Analizando: {archivo} (Usando Clave {indice_clave + 1}) ---")
                with open(ruta_txt, 'r', encoding='utf-8') as f:
                    texto_maestro = f.read()

                logging.info("   [Agente 3] Evaluando semántica Sasa/Lineal...")
                txt_marcado = cliente.models.generate_content(
                    model='gemini-2.5-flash', contents=[prompt_fase_3, texto_maestro], config=config_estricta
                ).text.strip()
                
                time.sleep(3)

                logging.info("   [Agente 4] Calculando métricas y guardando...")
                respuesta_calculo = cliente.models.generate_content(
                    model='gemini-2.5-flash', contents=[prompt_fase_4, txt_marcado], config=config_estricta
                )
                
                datos = respuesta_calculo.text.strip().split('|')

                if len(datos) == 5:
                    anio, lugar, sasa, lineal, indice = [d.strip() for d in datos]
                    
                    with open(archivo_csv, mode='a', newline='', encoding='utf-8') as f_csv_append:
                        escritor_append = csv.writer(f_csv_append, delimiter=';')
                        escritor_append.writerow([nombre_base, anio, lugar, sasa, lineal, indice])
                    
                    crear_documento_word(ruta_docx, nombre_base, anio, lugar, sasa, lineal, indice, txt_marcado)
                    logging.info(f"   ✅ ANÁLISIS PERFECTO | S:{sasa} | L:{lineal} | Índice:{indice}")
                    exito = True
                else:
                    logging.error(f"   ❌ Error de formato en los cálculos. Datos: {datos}")
                    time.sleep(5) 
                    break

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
                    logging.error(f"   ❌ ERROR DESCONOCIDO en {archivo}: {error_msg}")
                    time.sleep(5)
                    break 

        if exito:
            time.sleep(15)

    logging.info("\n✅ PROCESO DE ANÁLISIS (2 AGENTES) FINALIZADO.")

if __name__ == "__main__":
    ejecutar_analista()