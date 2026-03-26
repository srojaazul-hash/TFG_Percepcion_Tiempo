import os
import re
import csv

# ==========================================
# RUTAS EXACTAS
# ==========================================
dir_kikamba_depurado = r"C:\Users\Usuario\Desktop\TFG\Documentos_para_percepción_tiempo\Lindblom\VOL_1\texto_depurado\Kikamba"
archivo_csv_salida = r"C:\Users\Usuario\Desktop\TFG\Documentos_para_percepción_tiempo\Lindblom\VOL_1\resultados_analisis.csv"

# ==========================================
# DICCIONARIOS DE EXPRESIONES REGULARES (RegEx)
# ==========================================
marcadores_evento = {
    "Tene": r"\btene\b",
    "Zamani": r"\bzamani\b",
    "Kwakya": r"\bkwakya\b",
    "Mwaya_wa_kwithiwa": r"\bmwaya wa kwithiwa\b",
    "Infijo_a": r"\b[a-zĩũꝑŋṣṭḍḷṃṇñy]+a[a-zĩũꝑŋṣṭḍḷṃṇñy]+a\b" 
}

marcadores_lineales = {
    "Prefijo_ni_ka": r"\bn[ĩi]-?ka-[a-zĩũꝑŋṣṭḍḷṃṇñy]+\b|\bn[ĩi]ka[a-zĩũꝑŋṣṭḍḷṃṇñy]+\b", 
    "Saa": r"\bsaa\b",
    "Mwaka": r"\bmwaka\b",
    "Umunthi": r"\b[uũ]m[uũ]nth[iĩ]\b",
    "Iyoo": r"\biyoo\b"
}

def analizar_percepcion_tiempo_csv():
    print("--- INICIANDO EXTRACCIÓN DE DATOS A CSV ---")
    
    if not os.path.exists(dir_kikamba_depurado):
        print(f"❌ ERROR: No se encuentra la ruta: {dir_kikamba_depurado}")
        return
        
    archivos = sorted([f for f in os.listdir(dir_kikamba_depurado) if f.endswith(".txt")])
    if not archivos:
        print("❌ No se encontraron archivos .txt en la carpeta de texto depurado.")
        return

    # Definir las cabeceras del CSV
    cabeceras = ["Archivo"] + list(marcadores_evento.keys()) + list(marcadores_lineales.keys()) + ["IL_Pagina"]
    datos_csv = []

    for archivo in archivos:
        ruta = os.path.join(dir_kikamba_depurado, archivo)
        
        with open(ruta, 'r', encoding='utf-8') as f:
            texto_completo = f.read().lower() 
            
            fila_actual = {"Archivo": archivo}
            conteo_evento = 0
            conteo_lineal = 0

            # Rastreo de Tiempo de Evento
            for nombre, patron in marcadores_evento.items():
                coincidencias = len(re.findall(patron, texto_completo))
                fila_actual[nombre] = coincidencias
                if "Infijo_a" not in nombre:
                    conteo_evento += coincidencias

            # Rastreo de Tiempo Lineal
            for nombre, patron in marcadores_lineales.items():
                coincidencias = len(re.findall(patron, texto_completo))
                fila_actual[nombre] = coincidencias
                conteo_lineal += coincidencias

            # Cálculo del Índice de Linealidad local
            if conteo_evento > 0:
                fila_actual["IL_Pagina"] = round(conteo_lineal / conteo_evento, 2)
            else:
                fila_actual["IL_Pagina"] = "N/A"

            datos_csv.append(fila_actual)

    # Escritura del archivo CSV
    try:
        with open(archivo_csv_salida, mode='w', newline='', encoding='utf-8') as f_csv:
            escritor = csv.DictWriter(f_csv, fieldnames=cabeceras)
            escritor.writeheader()
            escritor.writerows(datos_csv)
        print(f"✅ Extracción completada. Archivo guardado en:\n{archivo_csv_salida}")
    except PermissionError:
        print(f"❌ ERROR: No se puede escribir el archivo. Cierra {archivo_csv_salida} si lo tienes abierto en Excel.")

if __name__ == "__main__":
    analizar_percepcion_tiempo_csv()