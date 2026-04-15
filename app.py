import pandas as pd
from google import genai
import json
import PIL.Image
import os
import shutil
from datetime import datetime
import docx
import time
from dotenv import load_dotenv
import os

load_dotenv()

# 1. CONFIGURACIÓN DE LA IA
api_key_secreta = os.getenv("GEMINI_API_KEY")
cliente = genai.Client(api_key=api_key_secreta)

# 2. CONFIGURACIÓN DE CARPETAS
CARPETA_ENTRADA = "facturas_nuevas"
CARPETA_SALIDA = "facturas_procesadas"
BASE_DATOS_EXCEL = "base_historica_facturas.xlsx"

os.makedirs(CARPETA_ENTRADA, exist_ok=True)
os.makedirs(CARPETA_SALIDA, exist_ok=True)

def extraer_datos_multiformato(ruta_archivo):
    print(f"🤖 Analizando archivo: {os.path.basename(ruta_archivo)}...")
    ext = os.path.splitext(ruta_archivo)[1].lower()
    
    # Instrucción maestra para la IA
    instruccion = """
    Eres un experto en auditoría de facturas chilenas. Extrae la siguiente información:
    1. Nombre de la empresa (Emisor).
    2. Número de factura (Folio).
    3. Para cada ítem: Descripción, Precio_Unitario, Cantidad, Precio_Total.

    IMPORTANTE: 
    - Si un dato no existe, usa null.
    - El resultado debe ser ÚNICAMENTE un objeto JSON con este formato:
    {
      "Empresa": "Nombre",
      "Numero_Factura": "123",
      "Items": [
        {"Descripcion": "Producto X", "Precio_Unitario": 1000, "Cantidad": 2, "Precio_Total": 2000}
      ]
    }
    """

    # Lógica según el tipo de archivo
    if ext in ['.jpg', '.jpeg', '.png']:
        contenido = [PIL.Image.open(ruta_archivo), instruccion]
    elif ext == '.pdf':
        with open(ruta_archivo, "rb") as f:
            pdf_bytes = f.read()
        # Enviamos el PDF como bytes especificando el tipo mime
        contenido = [
            {"mime_type": "application/pdf", "data": pdf_bytes},
            instruccion
        ]
    elif ext == '.docx':
        doc = docx.Document(ruta_archivo)
        texto_completo = "\n".join([p.text for p in doc.paragraphs])
        contenido = [f"Texto extraído del documento Word:\n{texto_completo}", instruccion]
    else:
        raise ValueError(f"Formato {ext} no soportado.")

    respuesta = cliente.models.generate_content(
        model='gemini-2.5-flash',
        contents=contenido
    )
    
    texto_json = respuesta.text.replace('```json', '').replace('```', '').strip()
    return json.loads(texto_json)

def auditar_y_guardar(datos, nombre_archivo):
    if os.path.exists(BASE_DATOS_EXCEL):
        df_historico = pd.read_excel(BASE_DATOS_EXCEL)
    else:
        columnas = ['Fecha', 'Empresa', 'Factura', 'Producto', 'Precio_Unitario', 'Cantidad', 'Precio_Total']
        df_historico = pd.DataFrame(columns=columnas)
    
    nuevos_registros = []
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"\n--- AUDITORÍA: {datos['Empresa']} (Factura: {datos['Numero_Factura']}) ---")
    
    for item in datos['Items']:
        desc = item['Descripcion']
        # Manejo de nulos para cálculos
        p_unit = round(float(item['Precio_Unitario']), 2) if item['Precio_Unitario'] else 0
        cant = item['Cantidad'] if item['Cantidad'] else 0
        p_total = item['Precio_Total'] if item['Precio_Total'] else 0
        
        # Comparación contra historial
        historial = df_historico[df_historico['Producto'].str.contains(desc, case=False, na=False, regex=False)]
        
        if not historial.empty:
            ultimo_p = float(historial.iloc[-1]['Precio_Unitario'])
            if p_unit > ultimo_p:
                print(f"⚠️ ALZA: {desc} (${ultimo_p} -> ${p_unit})")
            elif p_unit < ultimo_p:
                print(f"📉 BAJA: {desc} (${ultimo_p} -> ${p_unit})")
            else:
                print(f"✅ IGUAL: {desc} (${p_unit})")
        else:
            print(f"🆕 NUEVO: {desc} (${p_unit})")
            
        nuevos_registros.append({
            'Fecha': fecha_actual,
            'Empresa': datos['Empresa'],
            'Factura': datos['Numero_Factura'],
            'Producto': desc,
            'Precio_Unitario': p_unit,
            'Cantidad': cant,
            'Precio_Total': p_total
        })
    
    if nuevos_registros:
        df_final = pd.concat([df_historico, pd.DataFrame(nuevos_registros)], ignore_index=True)
        df_final.to_excel(BASE_DATOS_EXCEL, index=False)

if __name__ == "__main__":
    formatos_validos = ('.png', '.jpg', '.jpeg', '.pdf', '.docx')
    archivos = [f for f in os.listdir(CARPETA_ENTRADA) if f.lower().endswith(formatos_validos)]
    
    if not archivos:
        print("📂 Sin archivos nuevos.")
    else:
        for archivo in archivos:
            ruta_in = os.path.join(CARPETA_ENTRADA, archivo)
            ruta_out = os.path.join(CARPETA_SALIDA, archivo)
            
            exito = False
            intentos = 0
            
            # Intentará procesar la factura hasta 3 veces si el servidor está lleno
            while not exito and intentos < 3:
                try:
                    datos = extraer_datos_multiformato(ruta_in)
                    auditar_y_guardar(datos, archivo)
                    shutil.move(ruta_in, ruta_out)
                    print(f"✅ Procesado: {archivo}\n" + "-"*30)
                    exito = True
                    time.sleep(5) # Pausa de 5 segundos antes de leer la siguiente factura
                    
                except Exception as e:
                    mensaje_error = str(e)
                    if "503" in mensaje_error:
                        intentos += 1
                        print(f"⏳ Servidor saturado (Intento {intentos}/3). Esperando 15 segundos para reintentar con {archivo}...")
                        time.sleep(15)
                    else:
                        print(f"❌ Error inesperado en {archivo}: {e}")
                        break # Si es un error distinto al 503, se detiene
            
            if not exito:
                print(f"⚠️ No se pudo procesar {archivo} después de 3 intentos. Se intentará en la próxima ejecución.\n" + "-"*30)
