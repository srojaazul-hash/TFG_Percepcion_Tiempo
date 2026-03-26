import unicodedata

# Ruta exacta de tu archivo con los errores
ruta_archivo = r"C:\Users\Usuario\Desktop\TFG\Documentos_para_percepción_tiempo\Lindblom\VOL_1\Textos_Kikamba\Kikamba_part_1.txt"

try:
    with open(ruta_archivo, 'r', encoding='utf-8') as f:
        # Leemos solo la primera línea
        primera_linea = f.readline().strip()
        
    print(f"--- ANALIZANDO LA LÍNEA: ---\n{primera_linea}\n")
    print("--- RADIOGRAFÍA UNICODE (Primeros 30 caracteres) ---")
    
    # Analizamos letra por letra
    for letra in primera_linea[:30]:
        nombre = unicodedata.name(letra, 'NOMBRE_DESCONOCIDO')
        codigo = f"U+{ord(letra):04X}"
        print(f"Símbolo: [{letra}]  ->  Código: {codigo}  ->  Nombre: {nombre}")

except FileNotFoundError:
    print("❌ No se ha encontrado el archivo. Comprueba que la ruta es correcta.")