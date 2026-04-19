# PerSSim — Personality Simulation Framework

PerSSim es un framework para simular personajes históricos con personalidad consistente, usando LLMs como motor de razonamiento. El repositorio tiene dos subsistemas independientes:

| Subsistema | Carpeta | Para qué |
|---|---|---|
| **Simulation** | `simulation/` | Definir, simular y evolucionar personajes históricos |
| **Interact** | `interact/` | Orquestar diálogos autónomos entre varios personajes |

---

## Simulation

Framework declarativo para definir personajes con rigor psicológico (perfil OCEAN, valores, conducta, memoria) y simularlos en conversación con un LLM. Cada personaje se exporta como un Bundle autocontenido que funciona en cualquier LLM externo.

→ Ver [`simulation/README.md`](simulation/README.md)

## Interact

Sistema multi-agente que instancia varios personajes y los hace dialogar de forma autónoma o dirigida. Cada personaje corre como un proceso HTTP independiente coordinado por un orquestador. Usa modelos locales vía Ollama.

→ Ver [`interact/README.md`](interact/README.md)

---

## Agentes disponibles

Los agentes se invocan desde el entorno de desarrollo (GitHub Copilot o equivalente).

| Agente | Función |
|---|---|
| `character-configurator` | Investiga un personaje y genera sus ficheros JSON |
| `character-v1` | Adopta la personalidad de un personaje y lo simula en conversación |
| `character-compiler-strict` | Exporta el personaje como `Bundle_strict_<nombre>.md` |
| `character-compiler-narrative` | Exporta el personaje como `Bundle_narrative_<nombre>.md` |

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
└── .github/
    └── agents/
```