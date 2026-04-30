# PerSSim — Personality Simulation Framework

PerSSim es un framework para simular personajes históricos con personalidad consistente, usando LLMs como motor de razonamiento. El repositorio tiene tres subsistemas independientes:

| Subsistema | Carpeta | Para qué |
|---|---|---|
| **Simulation** | `simulation/` | Definir, simular y evolucionar personajes históricos |
| **Interact** | `interact/` | Orquestar diálogos autónomos entre varios personajes |
| **Correspondence** | `correspondence/` | Perfiles autocontenidos de personajes para uso en modo epistolar |

---

## Simulation

Framework declarativo para definir personajes con rigor psicológico (perfil OCEAN, valores, conducta, memoria) y simularlos en conversación con un LLM. Cada personaje se exporta como un Bundle autocontenido que funciona en cualquier LLM externo.

→ Ver [`simulation/README.md`](simulation/README.md)

## Interact

Sistema multi-agente que instancia varios personajes y los hace dialogar de forma autónoma o dirigida. Cada personaje corre como un proceso HTTP independiente coordinado por un orquestador. Usa modelos locales vía Ollama.

→ Ver [`interact/README.md`](interact/README.md)

## Correspondence

Perfiles autocontenidos de personajes diseñados para el agente `pen-pal`. Cada perfil incluye toda la información necesaria para que el personaje mantenga correspondencia con el usuario sin depender de ficheros externos.

→ Ver [`correspondence/`](correspondence/)

---

## Agentes disponibles

Los agentes se invocan desde el entorno de desarrollo (GitHub Copilot o equivalente).

| Agente | Función |
|---|---|
| `character-configurator` | Investiga un personaje y genera sus ficheros JSON |
| `character-v1` | Adopta la personalidad de un personaje y lo simula en conversación |
| `character-compiler-strict` | Exporta el personaje como `Bundle_strict_<nombre>.md` |
| `character-compiler-narrative` | Exporta el personaje como `Bundle_narrative_<nombre>.md` |
| `pen-pal` | Mantiene correspondencia epistolar con el usuario adoptando la personalidad de un personaje |

## Skills disponibles

Las skills extienden las capacidades de los agentes que las invocan.

| Skill | Agente | Función |
|---|---|---|
| `human-dialog` | `pen-pal` | Adapta el estilo de respuesta del personaje al tono y registro del interlocutor humano |

## Estructura del repositorio

```
PerSSim/
├── AGENT.md
├── README.md                  ← este fichero
├── simulation/                ← framework de simulación de personalidades
│   ├── README.md
│   ├── v1/                    ← versión 1 (referencia)
│   └── v1.1/                  ← versión actual
├── interact/                  ← sistema de interacción multi-agente
│   ├── README.md
│   └── docs/
│       ├── design.md
│       ├── install.md
│       └── usage.md
├── correspondence/            ← perfiles para modo epistolar (pen-pal)
│   └── <personaje>/
│       ├── instructions.md
│       └── profile.md
└── .github/
    └── agents/
        ├── character-v1.agent.md
        ├── character/
        │   └── generator/
        │       ├── character-configurator.agent.md
        │       ├── character-compiler-strict.agent.md
        │       └── character-compiler-narrative.agent.md
        └── pen-pal/
            ├── pen-pal.agent.md
            └── skills/
                └── human-dialog/
                    └── SKILL.md
```