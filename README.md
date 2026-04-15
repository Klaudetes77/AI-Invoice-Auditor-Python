# AI Invoice Auditor & Tracker (Python + Google Gemini)

Este sistema automatizado extrae, audita y estructura datos de facturas físicas y digitales (Imágenes, PDF, Word) utilizando Inteligencia Artificial multimodal, cruzando los datos en tiempo real con una base histórica para detectar variaciones de costos.

## El Problema que Resuelve
Las empresas pierden cientos de horas mensuales digitando facturas manualmente y rara vez detectan a tiempo cuando un proveedor les sube el precio de un insumo de forma silenciosa ("cost creep").

## La Solución
Un pipeline de datos en Python que procesa facturas por lotes de forma desatendida.

**Características Principales:**
**Extracción Inteligente:** Lee JPG, PNG, PDF y DOCX. Entiende el contexto, extrae el Emisor, Folio, Ítems, Cantidades y Precios, ignorando manchas o formatos irregulares.
**Auditoría de Precios Automática:** Cruza cada ítem leído con la base de datos histórica (`.xlsx`). Detecta de inmediato si el producto es Nuevo, si mantuvo su precio, si tuvo una Baja, o lanza una alerta si presenta un Alza de costo.
**Tolerancia a Fallos (Resiliencia):** Incluye un manejador de reintentos (Retry Handler) que gestiona automáticamente los picos de saturación de la API, garantizando que ninguna factura quede sin procesar.
**Organización Autónoma:** Mueve automáticamente los archivos ya leídos a una carpeta de procesados para evitar duplicidades.

## Tecnologías Utilizadas
**Lenguaje:** Python 3
**Procesamiento de Datos:** Pandas, OpenPyXL
**Inteligencia Artificial:** Google GenAI (Gemini 2.5 Flash / 1.5 Flash)
**Manejo de Archivos:** OS, Shutil, Python-docx, Pillow

## Ejemplo de Salida (Consola)
```text
Analizando archivo: factura_proveedor_01.jpg...
--- AUDITORÍA: Distribuidora Central (Factura: 45092) ---
IGUAL: Harina de Trigo 25kg ($25000.0)
ALZA: Aceite Maravilla 5L ($8500.0 -> $9200.0)
NUEVO: Levadura Fresca 1kg ($1200.0)
Base de datos histórica actualizada con éxito.
Archivo movido a carpeta de procesadas.