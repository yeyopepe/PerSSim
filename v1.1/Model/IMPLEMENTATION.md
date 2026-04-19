# PerSSim v1.1 — Documentación de implementación

## Propósito de este documento

Este documento describe la implementación técnica de la versión 1.1 del framework PerSSim: qué ficheros componen un personaje, qué contiene cada uno, cómo se relacionan entre sí, y cómo usarlos. Es el documento de referencia para crear nuevos personajes, entender el modelo de datos y operar los agentes disponibles.

Para la base teórica del modelo (marcos psicológicos, jerarquía de decisiones, referencias académicas), consulta `README.md`.

---

## Estructura de ficheros de una implementación

Cada personaje es una carpeta dentro de `v1.1/Impl/<código>/` con la siguiente estructura:

```
v1.1/Impl/001/
├── SYSTEM_PROMPT.md          # Referencia al system prompt de la versión
├── Identity.json             # Identidad y contexto histórico
├── Profile.json              # Perfil psicológico OCEAN
├── Values.json               # Valores, necesidades, metas y conflictos
├── Behavior.json             # Comportamiento y expresión situacional
├── Memory.json               # Eventos formativos y de sesión
├── Bundle.md                 # Exportación autocontenida (generada por el agente bundler)
└── Archives/
    ├── PublicLinks.md        # Recursos externos de referencia
    └── Docs/                 # Fuentes primarias: cartas, documentos, discursos
```

El fichero `SYSTEM_PROMPT.md` de cada implementación no contiene el prompt directamente — apunta al prompt compartido de la versión en `v1.1/SYSTEM_PROMPT.md`. Esto garantiza que todas las implementaciones usan siempre la misma versión del prompt sin duplicación.

---

## Descripción de cada fichero

### Identity.json

Define quién es el personaje: datos biográficos objetivos, su posición en el momento de la instancia y sus afiliaciones de grupo con nivel de lealtad.

El campo `id` incluye el año de la instancia, no necesariamente el de nacimiento. Este año indica el momento vital en que se sitúa la simulación por defecto, y debe ser coherente con el estado de los demás ficheros — especialmente `Memory.json` y `necesidades_activas` en `Values.json`.

Las `identidades_de_grupo` modelan la Teoría de la Identidad Social: cada grupo tiene un `rol` y un nivel de `lealtad` de 0.0 a 1.0. La lealtad no es declarada sino inferida del comportamiento: cuando dos grupos entraron en conflicto, ¿cuál prevaleció? Es el único campo de `Identity.json` que puede actualizarse durante una sesión mediante el comando `/Actualizar`.

### Profile.json

Contiene el perfil psicológico del personaje según el modelo OCEAN (Big Five). Cada rasgo es un valor continuo de 0.0 a 1.0:

| Rasgo | 0.0 | 1.0 |
|---|---|---|
| `apertura` | Convencional, pragmático | Curioso, creativo, abierto |
| `responsabilidad` | Impulsivo, desorganizado | Metódico, disciplinado |
| `extraversion` | Reservado, introvertido | Sociable, asertivo |
| `amabilidad` | Competitivo, escéptico | Empático, cooperativo |
| `neuroticismo` | Calmado, resistente | Ansioso, reactivo |

Las `facetas_notables` son rasgos cualitativos que matizan o contradicen lo que los valores numéricos podrían sugerir. Se usan para capturar paradojas documentadas o patrones que no encajan en un solo eje OCEAN.

Los valores de Profile.json son los más estables del modelo — cambian muy lentamente en adultos y solo deberían actualizarse ante evidencia muy sostenida en sesión.

### Values.json

Es el núcleo del sistema de decisiones. Contiene cuatro elementos:

**`valores_nucleares`** — jerarquía ordenada de principios motivacionales del personaje. Cada valor tiene una `prioridad` (1 = máxima) y `notas` que explican cómo lo interpreta el personaje. El orden importa: cuando dos valores entran en conflicto, el de mayor prioridad prevalece. Los valores nucleares corresponden a la Capa 1 de la jerarquía de decisiones y son los más resistentes al cambio.

**`necesidades_activas`** — estado de satisfacción de necesidades psicológicas en el momento de la instancia, en escala de 0.0 a 1.0. No representan importancia abstracta sino urgencia actual: una necesidad cubierta tiene valor bajo aunque sea fundamental para el personaje. Corresponde a la Capa 2 de la jerarquía y puede cambiar con más frecuencia que los valores nucleares.

**`metas_vitales`** — objetivos concretos que el personaje persigue activamente en su horizonte temporal. Corresponde a la Capa 3. Las metas ya alcanzadas en la fecha de la instancia deben aparecer en `Memory.json`, no aquí.

**`conflictos_internos`** — tensiones documentadas entre valores o metas. Solo se incluyen conflictos con evidencia de tensión real — momentos en que el personaje dudó, actuó contra un valor declarado, o tuvo que elegir entre dos cosas que valoraba.

### Behavior.json

Define la expresión situacional de la personalidad: cómo se comporta el personaje en la práctica. Es la capa más observable — lo que un contemporáneo habría podido describir. Contiene:

**`voz`** — subcampo exclusivo para información extraída de cartas y textos de producción directa del personaje. Si no hay material primario disponible, este campo se deja vacío. Incluye:
- `registro`: nivel de formalidad y variaciones según el destinatario.
- `recursos_retóricos`: patrones de argumentación y expresión recurrentes, con ejemplos extraídos de los textos.
- `reaccion_ante_desacuerdo`: comportamiento cuando alguien le contradice, según se observa en su correspondencia.
- `frases_o_expresiones_características`: fragmentos literales o paráfrasis muy cercanas extraídas de los textos originales.

**`estilo_comunicativo`** — síntesis del tono y forma habitual, integrando `voz` con lo inferido de otras fuentes.

**`manejo_del_conflicto`** — reacción ante tensión o confrontación, distinguiendo posición de fuerza de posición vulnerable.

**`relaciones_interpersonales`** — red de confianza (con personas concretas cuando es posible) y actitud hacia subordinados.

**`lineas_rojas`** — límites que el personaje nunca cruzó aunque tuvo oportunidad. Cada uno debería poder respaldarse con un momento documentado.

**`sesgos_cognitivos`** — patrones sistemáticos de error o distorsión en la interpretación de la realidad. Deben ser específicos del personaje, no genéricos.

### Memory.json

Registro de eventos que han moldeado al personaje. Tiene dos tipos de eventos, distinguidos por el campo `type`:

- `historical` — eventos anteriores al inicio de la simulación, que forman la memoria base del personaje. Se configuran al crear el personaje.
- `user` — eventos generados durante una sesión con el comando `/Memoria`. Registran decisiones, interacciones o cambios relevantes ocurridos en el chat.

Formato de cada evento:
```json
{
  "type": "historical" | "user",
  "date": "YYYY-MM-DD",
  "event": "descripción en primera persona, desde la perspectiva del personaje"
}
```

La selección de eventos históricos sigue el criterio de 2 de 3: cada evento debe cumplir al menos dos de estas condiciones: (1) el personaje tomó una decisión activa; (2) el evento tuvo consecuencias directas en su trayectoria; (3) revela o confirma algo de su perfil, valores o comportamiento.

### SYSTEM_PROMPT.md (de la versión)

El prompt operativo que gobierna el comportamiento del agente. Contiene:

- **Misión**: instrucción de rol y referencia a cada fichero de configuración.
- **Razonamiento**: cadena de 5 pasos que el agente ejecuta internamente antes de cada respuesta, sin mostrarla.
- **Reglas de oro**: restricciones de comportamiento permanentes, incluyendo la gestión de la fecha activa y el tratamiento del anacronismo.
- **Comandos**: acciones que rompen temporalmente el personaje para ejecutar una operación estructurada.

La cadena de razonamiento mapea directamente sobre la jerarquía de decisiones del modelo:

| Paso | Capa del modelo |
|---|---|
| 1. ¿Conflicto con valores nucleares? | Capa 1 — Valores |
| 2. ¿Qué necesidades están en juego? | Capa 2 — Necesidades |
| 3. ¿Cómo afecta a mis metas? | Capa 3 — Metas |
| 4. ¿Cómo reaccionaría con mi personalidad? | Capa 4 — Disposiciones |
| 5. ¿Cuál es mi respuesta más auténtica? | Capa 5 — Respuesta contextual |

---

## Comandos disponibles en sesión

| Comando | Función |
|---|---|
| `/Memoria` | Extrae eventos relevantes del chat y los añade a la instancia de Memory.json como eventos de tipo `user`. |
| `/Actualizar` | Propone cambios justificados en Profile, Behavior, Values o Identity (solo identidades_de_grupo), con evidencia de sesión explícita por cada cambio. |
| `/Fecha <fecha>` | Establece la fecha activa del personaje. Solo considera eventos de Memory.json anteriores a esa fecha y ejecuta `/Actualizar` automáticamente. |
| `/Instancia` | Muestra el estado actual de todos los ficheros de la instancia en memoria. |
| `/Reiniciar` | Descarta la instancia en memoria y recarga los ficheros originales. |

**Resistencia al cambio por capa.** No todos los campos evolucionan igual ante la evidencia de sesión. Los valores nucleares (Capa 1) requieren evidencia muy sólida y sostenida para cambiar. Las necesidades activas (Capa 2) pueden ajustarse con mayor facilidad. El perfil OCEAN cambia muy lentamente y solo ante patrones consistentes a lo largo de múltiples sesiones.

---

## Agentes disponibles

| Agente | Fichero | Función |
|---|---|---|
| `character-configurator` | `.github/agents/character-configurator.agent.md` | Investiga un personaje y genera todos sus ficheros JSON a partir de fuentes en Archives y fuentes externas contrastadas. |
| `character-v1` | `.github/agents/character-v1.agent.md` | Adopta la personalidad de un personaje definido en v1.1 y lo simula en conversación. |
| `character-bundler` | `.github/agents/character-bundler.agent.md` | Genera un `Bundle.md` autocontenido para exportar el personaje a cualquier LLM externo (exportación de solo lectura). |

### Flujo de trabajo típico

```
1. character-configurator  →  genera los ficheros JSON del personaje
2. character-v1            →  simula el personaje en sesión
3. /Memoria, /Actualizar   →  evoluciona la instancia durante la sesión
4. character-bundler       →  exporta el personaje para uso en otros LLMs
```

---

## Fuentes y jerarquía de autoridad

Al configurar un personaje, las fuentes en `Archives/Docs/` tienen prioridad sobre cualquier otra. Dentro de esas fuentes, la jerarquía de autoridad es:

1. **Cartas privadas y correspondencia personal** — mayor valor. Fuente principal para `Behavior.json` (especialmente `voz`) y facetas cualitativas de `Profile.json`.
2. **Instrucciones, memorandos y documentos de trabajo propios** — alta autoridad. Fuente principal para `Values.json`.
3. **Discursos y textos públicos firmados** — autoridad media-alta. Útiles para valores declarados; filtrar diferencia entre lo público y lo actuado.
4. **Testimonios de contemporáneos** — autoridad media. Considerar la relación del testigo con el personaje.
5. **Biografías y crónicas** — autoridad de contraste. Para contextualizar y verificar, no como fuente primaria de rasgos.

---

## Notas sobre el Bundle.md

El `Bundle.md` es una exportación de solo lectura generada por el agente `character-bundler`. Contiene el SYSTEM_PROMPT adaptado para uso sin ficheros externos, y todos los JSON del personaje limpios de campos `__comment`. Es el formato recomendado para usar el personaje en ChatGPT, Gemini u otros LLMs.

**Limitaciones del Bundle:** el personaje no evolucionará durante la sesión en el LLM de destino. Los comandos `/Memoria`, `/Actualizar` y `/Fecha` no están disponibles. Para sesiones con evolución, usar el entorno PerSSim original con el agente `character-v1`.