# PerSSim — Simulation

Framework declarativo para simular personajes históricos con personalidad consistente, usando LLMs como motor de razonamiento. Cada personaje se define mediante ficheros JSON estructurados que modelan su identidad, perfil psicológico, valores, conducta y memoria.

## Qué permite hacer

- **Definir** personajes con rigor psicológico: perfil OCEAN, jerarquía de valores, necesidades activas, metas, conflictos internos y patrones de comportamiento extraídos de fuentes primarias.
- **Simular** conversaciones en las que el LLM adopta la personalidad del personaje de forma coherente y temporalmente restringida a su época.
- **Evolucionar** la personalidad durante la sesión: el personaje puede actualizar su memoria, ajustar sus rasgos y situarse en distintos momentos de su vida.
- **Exportar** cualquier personaje como un Bundle autocontenido listo para usar en cualquier LLM externo, en formato estricto o narrativo.

## Estructura

```
simulation/
├── v1/                        ← versión 1 (mantenida para referencia)
│   ├── SYSTEM_PROMPT.md
│   ├── Model/
│   └── Impl/
│       └── 001/               ← Cardenal Richelieu (instancia original)
└── v1.1/                      ← versión actual
    ├── SYSTEM_PROMPT.md
    ├── Model/
    │   ├── README.md          ← base de investigación del modelo
    │   ├── IMPLEMENTATION.md  ← referencia técnica de implementación
    │   └── Template/          ← plantillas base para nuevos personajes
    └── Impl/
        └── 001/               ← Cardenal Richelieu (instancia v1.1)
            └── Bundles/       ← Bundles exportados listos para usar
```

## Ficheros de configuración de un personaje

| Fichero | Contenido |
|---|---|
| `Identity.json` | Nombre, fechas, época, cargo y afiliaciones de grupo con nivel de lealtad |
| `Profile.json` | Rasgos OCEAN en escala 0.0–1.0 y facetas cualitativas |
| `Values.json` | Jerarquía de valores nucleares, necesidades activas, metas vitales y conflictos internos |
| `Behavior.json` | Voz, estilo comunicativo, gestión del conflicto, red de confianza, líneas rojas y sesgos cognitivos |
| `Memory.json` | Eventos formativos históricos y eventos generados en sesión |
| `Archives/Docs/` | Fuentes primarias: cartas, discursos, memorandos del personaje |

## Cómo usar un personaje existente

### Opción A — Bundle (más simple)

Usa uno de los Bundles exportados en `Impl/<código>/Bundles/`. Son ficheros autocontenidos que funcionan como system prompt en cualquier LLM sin configuración adicional:

- `Bundle_strict_*.md` — vuelca los JSON del personaje tal cual, con el SYSTEM_PROMPT adaptado para uso externo.
- `Bundle_narrative_*.md` — transforma los JSON en prosa estructurada; más portable entre distintos modelos.

### Opción B — Entorno completo

Para usar el personaje con evolución completa (memoria, actualización de rasgos, comandos de sesión):

1. Carga `v1.1/SYSTEM_PROMPT.md` como *system prompt* de tu LLM.
2. Proporciona los ficheros JSON de la implementación como contexto adicional.
3. Inicia la conversación.

Comandos disponibles durante la sesión:

| Comando | Función |
|---|---|
| `/Memoria` | Extrae eventos relevantes del chat y los añade a Memory.json |
| `/Actualizar` | Propone cambios justificados en los rasgos del personaje |
| `/Fecha <fecha>` | Sitúa al personaje en un momento concreto de su vida |
| `/Instancia` | Muestra el estado actual de todos los ficheros en memoria |
| `/Reiniciar` | Descarta la instancia y recarga la configuración original |

## Cómo crear un nuevo personaje

El agente `character-configurator` automatiza este proceso: investiga el personaje, clasifica las fuentes disponibles por autoridad y rellena todos los ficheros JSON.

Para hacerlo manualmente:

1. Copia `v1.1/Model/Template/` en `v1.1/Impl/<nuevo_código>/`.
2. Añade fuentes primarias en `Archives/Docs/` si las tienes.
3. Rellena cada fichero JSON siguiendo los campos `__comment` como guía. Orden recomendado: `Identity` → `Profile` → `Values` → `Behavior` → `Memory`.

Las fuentes en `Archives/Docs/` tienen prioridad sobre cualquier otra. Las cartas privadas son la fuente de mayor autoridad para `Behavior.json`; los memorandos lo son para `Values.json`.

## Los Bundles como contrato con Interact

Los Bundles exportados en `Impl/<código>/Bundles/` son el punto de conexión con el subsistema [`interact/`](../interact/README.md). El sistema de interacción consume Bundles como system prompt de cada personaje instanciado.