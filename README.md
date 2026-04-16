# PerSSim — Personality Simulation Framework

PerSSim es un framework declarativo para simular personajes históricos con personalidad consistente, usando grandes modelos de lenguaje (LLMs) como motor de razonamiento. Cada personaje se define mediante un conjunto de ficheros JSON estructurados que modelan su identidad, perfil psicológico, valores, conducta y memoria, junto con un *system prompt* que orquesta la simulación.

## Propósito general

El objetivo de PerSSim es dotar a un LLM de una personalidad coherente, estable y evolutiva, de modo que sus respuestas sean auténticas al personaje: respetando su sistema de valores, sus sesgos cognitivos, su vocabulario y su conocimiento histórico limitado a su época.

El framework permite:

- **Definir** personajes con rigor psicológico (modelo OCEAN, valores, necesidades, metas, conflictos internos).
- **Simular** conversaciones en las que el LLM permanece en el personaje de forma consistente.
- **Evolucionar** la personalidad del personaje durante la sesión a través de comandos (`/Memoria`, `/Actualizar`, `/Fecha`).
- **Reutilizar** la plantilla base para construir cualquier nuevo personaje.

## Estructura de ficheros

```
PerSSim/
├── README.md                          # Este fichero
└── v1/                                # Versión 1 del framework
    ├── SYSTEM_PROMPT.md               # Prompt de orquestación principal (instrucciones, razonamiento y comandos)
    ├── Template/                      # Plantilla base para crear nuevos personajes
    │   ├── SYSTEM_PROMPT.md           # Versión comentada del prompt, con instrucciones de uso
    │   ├── Identity.json              # Quién es el personaje: nombre, fechas, contexto histórico, afiliaciones
    │   ├── Profile.json               # Perfil psicológico OCEAN (0.0–1.0) y facetas cualitativas
    │   ├── Values.json                # Valores nucleares, necesidades activas, metas vitales y conflictos internos
    │   ├── Behavior.json              # Estilo comunicativo, gestión del conflicto, líneas rojas y sesgos cognitivos
    │   ├── Memory.json                # Registro de eventos fundamentales que han moldeado al personaje
    │   └── Archives/
    │       └── Docs/                  # Fuentes históricas primarias (cartas, papeles de Estado)
    │       └── PublicLinks.md         # Lista de recursos públicos adicionales sobre el personaje
    └── Impl/                          # Implementaciones concretas de personajes
        └── 001/                       # Personaje: Cardenal Richelieu (1585–1642)
```

### Descripción de los ficheros de configuración de un personaje

| Fichero | Rol |
|---|---|
| `Identity.json` | Datos biográficos, contexto histórico y grupo de afiliaciones con nivel de lealtad |
| `Profile.json` | Cinco rasgos OCEAN en escala continua 0.0–1.0 más facetas cualitativas |
| `Values.json` | Jerarquía de valores nucleares, necesidades activas (0.0–1.0), metas vitales y conflictos internos |
| `Behavior.json` | Expresión situacional: tono comunicativo, gestión del conflicto, confianza, líneas rojas y sesgos |
| `Memory.json` | Línea temporal de eventos clave; se puede ampliar durante la sesión con `/Memoria` |
| `Archives/` | Fuentes externas (documentos, enlaces) que enriquecen el conocimiento del personaje |

## Cómo usar un personaje existente

1. Carga `v1/SYSTEM_PROMPT.md` como *system prompt* de tu LLM.
2. Proporciona los ficheros JSON del personaje (p. ej. `v1/Impl/001/`) como contexto adicional.
3. Inicia la conversación: el modelo adoptará la personalidad del personaje.
4. Usa los comandos del sistema para gestionar la sesión:
   - `/Memoria` — extrae y almacena en instancia los eventos del chat.
   - `/Actualizar` — propone cambios en los rasgos del personaje basándose en la sesión.
   - `/Fecha <fecha>` — restringe el conocimiento del personaje a una fecha concreta.
   - `/Instancia` — muestra el estado actual de todos los ficheros de la instancia.
   - `/Reiniciar` — reinicia la sesión releyendo la configuración original.

## Cómo crear un nuevo personaje

1. Copia la carpeta `v1/Template/` en `v1/Impl/<nuevo_id>/`.
2. Rellena cada fichero JSON siguiendo los comentarios `__comment` incluidos como guía.
3. (Opcional) Añade fuentes documentales en `Archives/Docs/` y enlaces en `Archives/PublicLinks.md`.
