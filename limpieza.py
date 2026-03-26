import os
import re

# RUTAS
dir_kikamba_raw = r"C:\Users\Usuario\Desktop\TFG\Documentos_para_percepción_tiempo\Lindblom\VOL_1\Textos_Kikamba"
dir_ingles_raw = r"C:\Users\Usuario\Desktop\TFG\Documentos_para_percepción_tiempo\Lindblom\VOL_1\Textos_ingles"
dir_salida = r"C:\Users\Usuario\Desktop\TFG\Documentos_para_percepción_tiempo\Lindblom\VOL_1\texto_depurado"

# Creamos subcarpetas para no mezclar los idiomas depurados
dir_salida_k = os.path.join(dir_salida, "Kikamba")
dir_salida_i = os.path.join(dir_salida, "Ingles")
os.makedirs(dir_salida_k, exist_ok=True)
os.makedirs(dir_salida_i, exist_ok=True)

# ==========================================
# DICCIONARIO DE LIMPIEZA AUTOMÁTICA
# ==========================================
# Aquí ponemos lo que la IA suele escribir MAL a la izquierda, 
# y a la derecha lo que DEBERÍA haber escrito.
correcciones_kikamba = {
    r"í": "ĩ",    # La IA pone acentos españoles en lugar de tildes
    r"ú": "ũ",
    r"ı": "ĩ",    # La IA a veces confunde la tilde con la i sin punto en ciertas fuentes
    r"ayyĩ": "aŋgĩ", # Fallo específico de la página 20
    r"mapi": "maꝑi", # Fallo específico de la página 20
}

def depurar_textos():
    print("--- Iniciando Depuración Automática ---")
    
    # 1. Limpiar Kikamba
    archivos_k = [f for f in os.listdir(dir_kikamba_raw) if f.endswith(".txt")]
    for archivo in archivos_k:
        ruta_in = os.path.join(dir_kikamba_raw, archivo)
        ruta_out = os.path.join(dir_salida_k, archivo.replace(".txt", "_depurado.txt"))
        
        with open(ruta_in, 'r', encoding='utf-8') as f_in, open(ruta_out, 'w', encoding='utf-8') as f_out:
            for linea in f_in:
                linea_limpia = linea
                for error, correccion in correcciones_kikamba.items():
                    # Reemplaza los errores sistemáticos
                    linea_limpia = re.sub(error, correccion, linea_limpia)
                f_out.write(linea_limpia)
        print(f"✅ Depurado: {archivo}")
        
    # 2. Copiar Inglés (El inglés no suele tener símbolos raros, lo pasamos tal cual)
    archivos_i = [f for f in os.listdir(dir_ingles_raw) if f.endswith(".txt")]
    for archivo in archivos_i:
        ruta_in = os.path.join(dir_ingles_raw, archivo)
        ruta_out = os.path.join(dir_salida_i, archivo.replace(".txt", "_depurado.txt"))
        
        with open(ruta_in, 'r', encoding='utf-8') as f_in, open(ruta_out, 'w', encoding='utf-8') as f_out:
            for linea in f_in:
                f_out.write(linea)
        print(f"✅ Trasladado: {archivo}")

if __name__ == "__main__":
    depurar_textos()
    print(f"\nProceso finalizado. Archivos guardados en: {dir_salida}")