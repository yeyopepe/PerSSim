# PerSSim — Personality Simulation Framework

PerSSim es un framework declarativo para simular personajes históricos con personalidad consistente, usando grandes modelos de lenguaje (LLMs) como motor de razonamiento. Cada personaje se define mediante un conjunto de ficheros JSON estructurados que modelan su identidad, perfil psicológico, valores, conducta y memoria, junto con un *system prompt* que orquesta la simulación.

## Qué permite hacer PerSSim

- **Definir** personajes con rigor psicológico: perfil OCEAN, jerarquía de valores, necesidades activas, metas, conflictos internos y patrones de comportamiento extraídos de fuentes primarias.
- **Simular** conversaciones en las que el LLM adopta la personalidad del personaje de forma coherente y temporalmente restringida a su época.
- **Evolucionar** la personalidad durante la sesión mediante comandos: el personaje puede actualizar su memoria, ajustar sus rasgos y situarse en distintos momentos de su vida.
- **Exportar** cualquier personaje como un fichero autocontenido listo para usar en cualquier LLM externo, en formato estricto o narrativo.

## Estructura del repositorio

```
PerSSim/
├── README.md                         # Este fichero
├── .github/
│   └── agents/                       # Agentes de IA para automatizar el flujo de trabajo
│       ├── character-configurator.agent.md
│       ├── character-v1.agent.md
│       ├── character-compiler-strict.agent.md
│       └── character-compiler-narrative.agent.md
├── v1/                               # Versión 1 (mantenida para referencia)
│   ├── SYSTEM_PROMPT.md
│   ├── Model/
│   └── Impl/
│       └── 001/                      # Cardenal Richelieu (instancia original)
└── v1.1/                             # Versión actual
    ├── SYSTEM_PROMPT.md
    ├── Model/
    │   ├── README.md                 # Base de investigación del modelo
    │   ├── IMPLEMENTATION.md         # Referencia técnica de implementación
    │   └── Template/                 # Plantillas base para nuevos personajes
    │       ├── Identity.json
    │       ├── Profile.json
    │       ├── Values.json
    │       ├── Behavior.json
    │       ├── Memory.json
    │       └── Archives/
    └── Impl/
        └── 001/                      # Cardenal Richelieu (instancia v1.1)
            

## Ficheros de configuración de un personaje

| Fichero | Contenido |
|---|---|
| `Identity.json` | Nombre, fechas, época, cargo y afiliaciones de grupo con nivel de lealtad |
| `Profile.json` | Rasgos OCEAN en escala 0.0–1.0 y facetas cualitativas |
| `Values.json` | Jerarquía de valores nucleares, necesidades activas, metas vitales y conflictos internos |
| `Behavior.json` | Voz (extraída de cartas), estilo comunicativo, gestión del conflicto, red de confianza, líneas rojas y sesgos cognitivos |
| `Memory.json` | Eventos formativos históricos y eventos generados en sesión |
| `Archives/Docs/` | Fuentes primarias: cartas, discursos, memorandos del personaje |

## Cómo usar un personaje existente

La forma más directa es usar uno de los Bundles exportados en `Impl/<código>/Bundles/`. Son ficheros autocontenidos que funcionan como system prompt en cualquier LLM sin configuración adicional:

- `Bundle_strict_*.md` — vuelca los JSON del personaje tal cual, con el SYSTEM_PROMPT adaptado para uso externo.
- `Bundle_narrative_*.md` — transforma los JSON en prosa estructurada; más portable entre distintos modelos.

Para usar el personaje en el entorno PerSSim con evolución completa:

1. Carga `v1.1/SYSTEM_PROMPT.md` como *system prompt* de tu LLM.
2. Proporciona los ficheros JSON de la implementación como contexto adicional.
3. Inicia la conversación: el modelo adoptará la personalidad del personaje.
4. Usa los comandos para gestionar la sesión:

| Comando | Función |
|---|---|
| `/Memoria` | Extrae eventos relevantes del chat y los añade a la instancia de Memory.json |
| `/Actualizar` | Propone cambios justificados en los rasgos del personaje basándose en la sesión |
| `/Fecha <fecha>` | Sitúa al personaje en un momento concreto de su vida |
| `/Instancia` | Muestra el estado actual de todos los ficheros en memoria |
| `/Reiniciar` | Descarta la instancia y recarga la configuración original |

## Cómo crear un nuevo personaje

El agente `character-configurator` automatiza este proceso: investiga el personaje, clasifica las fuentes disponibles por autoridad y rellena todos los ficheros JSON siguiendo las instrucciones embebidas en las plantillas.

Para hacerlo manualmente:

1. Copia la carpeta `v1.1/Model/Template/` en `v1.1/Impl/<nuevo_código>/`.
2. Añade fuentes primarias en `Archives/Docs/` si las tienes (cartas, discursos propios).
3. Rellena cada fichero JSON siguiendo los campos `__comment` como guía. El orden recomendado es: `Identity` → `Profile` → `Values` → `Behavior` → `Memory`.

Las fuentes en `Archives/Docs/` tienen prioridad sobre cualquier otra. Dentro de ellas, las cartas privadas son la fuente de mayor autoridad para `Behavior.json`; los memorandos e instrucciones lo son para `Values.json`.

## Agentes disponibles

Los agentes se invocan desde el entorno de desarrollo (GitHub Copilot o equivalente).

| Agente | Función |
|---|---|
| `character-configurator` | Investiga un personaje y genera sus ficheros JSON a partir de las fuentes en `Archives/` y fuentes externas contrastadas |
| `character-v1` | Adopta la personalidad de un personaje definido en v1.1 y lo simula en conversación |
| `character-compiler-strict` | Exporta el personaje como `Bundle_strict_<nombre>.md`: SYSTEM_PROMPT adaptado + JSON limpios |
| `character-compiler-narrative` | Exporta el personaje como `Bundle_narrative_<nombre>.md`: SYSTEM_PROMPT adaptado + datos en prosa estructurada |

## Documentación del modelo

La documentación técnica y de investigación está en `v1.1/Model/`:

- `README.md` — base de investigación: marcos psicológicos, intentos previos de simulación y decisiones de diseño del framework.
- `IMPLEMENTATION.md` — referencia técnica: descripción de cada fichero, comandos, agentes y jerarquía de fuentes.