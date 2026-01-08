# NotebookLM, Bard & Gemini Watermark Remover

Una herramienta web premium para eliminar las marcas de agua de tus documentos (NotebookLM) y fotos generadas por IA (Bard, Gemini) de forma automática y fluida.

He hecho una versión gratuita para que todo el mundo pueda usarla, pero si quieres que todo el mundo pueda usarla, puedes desplegarla en la nube (GitHub + Render).

Modifica jacobo

## Características

- **Eliminación inteligente en PDFs**: Detecta y oculta el texto "NotebookLM" en cualquier fondo.
- **Limpieza de Fotos IA (Gemini)**: Elimina el logo de destello (sparkle) mediante **Template Matching**, detectando la forma exacta sin importar el fondo.
- **Calidad Original Garantizada**: La herramienta mantiene la resolución y nitidez original, evitando artefactos de reescalado artificial o filtros que degraden los textos.
- **Inpainting Profesional**: Reconstruye la zona eliminada usando el algoritmo Navier-Stokes para una transición invisible.
- **Interfaz moderna**: Sistema de arrastrar y soltar compatible con PDFs e Imágenes (.jpg, .png).

## Instalación Local (Para uso personal)

1. **Clonar/Descargar** este repositorio.
2. **Instalar dependencias**:

   ```bash
   python3 -m pip install -r requirements.txt
   ```

3. **Lanzar el servidor**:

   ```bash
   python3 execution/web_app_server.py
   ```

4. **Abrir en el navegador**:

   [http://localhost:5001](http://localhost:5001)

## Estructura del Proyecto (Arquitectura de 3 Capas)

- `directives/`: Instrucciones de alto nivel sobre el funcionamiento de la app.
- `execution/`: Scripts de procesamiento (Python) y servidor Flask.
- `web/`: Archivos frontend (HTML, CSS, JS).
- `.tmp/`: Directorio temporal para archivos subidos y procesados.

## Cómo desplegar en la nube (GitHub + Render)

Si quieres que **todo el mundo pueda usarlo gratis**, sigue la guía adjunta o los pasos rápidos en este README:

1. **GitHub**: Sube estos archivos a un repositorio público.
2. **Render**:
   - Crea un "Web Service".
   - Conecta tu repo de GitHub.
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python execution/web_app_server.py`
