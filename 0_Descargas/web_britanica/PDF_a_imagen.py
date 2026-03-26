import os
from pdf2image import convert_from_path

def pdf_a_imagenes():
    ruta_pdf = r"C:\Users\Usuario\Desktop\TFG\Documentos_para_percepción_tiempo\textos\Kamba_Folklore_vol_1.pdf"
    carpeta_imagenes = r"C:\Users\Usuario\Desktop\TFG\Documentos_para_percepción_tiempo\Lindblom\VOL_1\imagenes_paginas"
    os.makedirs(carpeta_imagenes, exist_ok=True)
    
    print("Iniciando conversión del PDF a imágenes... Esto puede tardar unos minutos.")
    
    # Si te da error de que no encuentra Poppler, quita el '#' de la siguiente línea 
    # y ajusta el nombre exacto de la carpeta si es necesario:
    # imagenes = convert_from_path(ruta_pdf, dpi=300, poppler_path=r"C:\Users\Usuario\Desktop\TFG\Release-24.02.0-0\poppler-24.02.0\Library\bin")
    
    imagenes = convert_from_path(ruta_pdf, dpi=300)
    
    for i, imagen in enumerate(imagenes):
        ruta_imagen = os.path.join(carpeta_imagenes, f"pagina_{i + 1}.png")
        imagen.save(ruta_imagen, "PNG")
        print(f"Guardada: {ruta_imagen}")
        
    print("¡Conversión completada con éxito!")

if __name__ == '__main__':
    pdf_a_imagenes()