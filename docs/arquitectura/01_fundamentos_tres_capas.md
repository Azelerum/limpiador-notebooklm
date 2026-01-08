# Fundamentos de la Arquitectura de 3 Capas

## Introducción: El Problema de la Probabilidad vs. Determinismo

El desarrollo de software con Grandes Modelos de Lenguaje (LLMs) presenta un desafío fundamental: **los LLMs son probabilísticos, mientras que la lógica de negocio requiere consistencia determinista**.

Si le pides a un LLM que realice 5 pasos secuenciales manualmente, y cada paso tiene un 90% de precisión, la probabilidad de éxito total es solo del 59% ($0.9^5$). Los errores se componen.

Esta arquitectura resuelve ese problema desacoplando la **toma de decisiones** de la **ejecución**.

---

## Las Tres Capas

### Capa 1: Directiva (El "Qué")
**Naturaleza**: Estática, Humana/Documental.
**Ubicación**: Carpeta `directives/` (archivos Markdown).

Son los Procedimientos Operativos Estándar (SOPs). No contienen código, sino instrucciones en lenguaje natural estructurado. Definen:
- **Objetivo**: Qué queremos lograr.
- **Inputs**: Qué información se necesita.
- **Herramientas**: Qué scripts específicos se deben usar.
- **Outputs**: Qué se espera obtener.
- **Casos Borde**: Qué hacer si algo falla.

Es como el manual de instrucciones que le darías a un empleado inteligente.

### Capa 2: Orquestación (El "Cerebro")
**Naturaleza**: Probabilística, IA Agente.
**Ubicación**: El modelo (Tú/Antigravity).

Es el agente inteligente que lee la directiva. Su trabajo NO es "hacer" el trabajo manual, sino **enrutar**.
- Lee la directiva `directives/remove_watermark.md`.
- Entiende que para un PDF debe llamar a la herramienta A y para una imagen a la herramienta B.
- Interpreta errores y decide si reintentar o preguntar al usuario.
- **Función Clave**: Convierte la intención humana (texto) en parámetros precisos para la máquina.

### Capa 3: Ejecución (El "Cómo")
**Naturaleza**: Determinista, Código Puro.
**Ubicación**: Carpeta `execution/` (Scripts Python/Bash).

Son scripts atómicos, fiables y testeables.
- **No piensan**: Solo ejecutan una tarea muy bien definida.
- **Cero Alucinaciones**: Si el código dice `rm -rf`, borra archivos. No "cree" que los borra.
- **Aislamiento**: Cada script se encarga de una sola cosa.

---

## El Principio de Aislamiento: El Caso Práctico

Me preguntabas por qué modificar la eliminación de marcas de agua en Gemini no afecta a NotebookLM. La respuesta está en la **Capa 3**.

### Escenario
Tienes dos flujos de trabajo en tu aplicación:
1.  **Limpiar PDF**: Usa `execution/process_pdf_watermark.py`
2.  **Limpiar Imagen**: Usa `execution/process_image_watermark.py`

### Por qué es robusto
Cuando me pediste mejorar la limpieza de imágenes de Gemini, yo (Capa 2) modifiqué **exclusivamente** el archivo `execution/process_image_watermark.py` (Capa 3).

El script `process_pdf_watermark.py` ni siquiera fue abierto. No comparten memoria, no comparten variables globales, no comparten lógica. Son procesos estancos.

- **Antes**: La lógica de Gemini usaba umbrales de brillo.
- **Ahora**: Usa "Template Matching" (reconocimiento de formas).

Este cambio radical en la lógica interna del script de imagen es invisible para el resto del sistema. La Capa 1 (la directiva) sigue diciendo simplemente: *"Si es imagen -> ejecutar script de imagen"*.

### Beneficio
Esto permite "recocer" (self-anneal) partes del sistema sin riesgo de regresiones en otras. Si rompes el script de imágenes, el de PDFs sigue funcionando al 100% porque son tuberías de ejecución paralelas que nunca se cruzan.
