# Arquitectura Avanzada: Escalabilidad y Agentes Anidados

## Más allá de tareas simples

En el ejemplo de las marcas de agua, tenemos un flujo lineal simple:
`Input -> Agente decide script -> Ejecución -> Output`

Pero, ¿qué pasa cuando la tarea es "Contratar a un nuevo empleado"? Ningún script de Python puede "contratar a alguien". Es un proceso complejo que requiere múltiples sub-tareas, decisiones humanas y herramientas dispares.

Aquí es donde la arquitectura escala mediante la **Composabilidad** y la **Recursividad**.

---

## Concepto: Meta-Directivas y Agentes Anidados

En sistemas complejos, una Directiva (Capa 1) no llama a un Script (Capa 3), sino que **llama a otras Directivas**.

Imagina una jerarquía:

1.  **Directiva Padre**: `directives/hr/onboarding_empleado.md`
    *   *Paso 1*: Generar contrato -> Llama a `directives/legal/generar_contrato.md`
    *   *Paso 2*: Crear cuentas IT -> Llama a `directives/it/provisionar_cuentas.md`
    *   *Paso 3*: Enviar bienvenida -> Llama a `directives/comms/email_bienvenida.md`

### Cómo funciona el flujo (El Agente llama al Agente)

1.  **Agente Principal (Capa 2 - Nivel A)**:
    - Recibe: "Contratar a Juan Pérez".
    - Lee `onboarding_empleado.md`.
    - Ve que el primer paso es "Generar contrato".
    - **No ejecuta un script directamente**. En su lugar, invoca una sub-instancia de agente (o cambia su propio contexto) para resolver esa sub-tarea.

2.  **Agente Secundario (Capa 2 - Nivel B)**:
    - Recibe: "Generar contrato para Juan Pérez".
    - Lee `generar_contrato.md`.
    - Este SOP sí es terminal: dice "Usa el script `execution/fill_pdf_template.py`".
    - El Agente B ejecuta el script, verifica el PDF y retorna el resultado al Agente A.

3.  **Agente Principal (Capa 2 - Nivel A)**:
    - Recibe "Contrato generado en `/tmp/contrato_juan.pdf`".
    - Marca el paso 1 como hecho.
    - Pasa al paso 2: "Crear cuentas IT".

---

## Ejemplo Práctico: Escenario "Contratar Empleado"

### Estructura de Archivos
```text
directives/
├── hr/
│   └── contratar_empleado.md  <-- META-DIRECTIVA
├── legal/
│   └── generar_contrato_pdf.md <-- DIRECTIVA TERMINAL
└── it/
    └── crear_usuario_slack.md  <-- DIRECTIVA TERMINAL
```

### Flujo de Ejecución

#### 1. Directiva Padre (`hire_employee.md`)
> **Objetivo**: Completar onboarding.
> **Pasos**:
> 1. Ejecutar directiva `legal/generar_contrato_pdf.md` con datos del candidato.
> 2. Si contrato OK, ejecutar directiva `it/crear_usuario_slack.md`.
> 3. Notificar al manager.

#### 2. La Magia de la Abstracción
El Agente que corre la directiva padre **no necesita saber cómo se crea un usuario en Slack**. Solo necesita saber que existe una directiva experta en eso y llamarla.

Si mañana Slack cambia su API:
1.  Falla la directiva `it/crear_usuario_slack.md`.
2.  Un ingeniero (o el agente en modo "fix") actualiza el script `execution/slack_invite.py` y la directiva de IT.
3.  La directiva padre `hire_employee.md` **no necesita cambios**. Sigue llamando a la misma directiva de IT, que ahora internamente funciona diferente.

## Conclusión

Esta arquitectura permite construir sistemas de **Complejidad Infinita** mediante piezas de **Simplicidad Finita**.

- ** scripts (Capa 3)** son las células. Hacen funciones biológicas básicas.
- ** Directivas (Capa 1)** son los órganos. Agrupan células para una función mayor.
- ** Agentes (Capa 2)** son el sistema nervioso. Coordinan los órganos para mantener el cuerpo vivo.

Al igual que en el caso de las marcas de agua, el aislamiento es total. Un fallo en el proceso de creación de email no detiene la generación del contrato, y permite depurar cada pieza por separado.
