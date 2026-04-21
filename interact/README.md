# PerSSim — Interact

Sistema multi-agente que instancia varios personajes PerSSim y los hace dialogar de forma autónoma por turnos. Cada personaje corre como un servidor HTTP independiente coordinado por un orquestador central. Usa modelos locales vía Ollama.

## Cómo funciona

Cada personaje se carga con su Bundle como system prompt y mantiene su propia memoria de conversación (pila de mensajes). El orquestador define el orden de turnos, distribuye los mensajes entre personajes y gestiona los timeouts. El usuario puede introducir narración libre en cualquier momento.

## Estructura

```
interact/
├── README.md
├── perssim/                    ← paquete Python (perssim-interact)
│   ├── char.py                 ← servidor FastAPI del personaje
│   ├── orchestrator.py         ← servidor FastAPI del orquestador
│   ├── launcher.py             ← lanzador de sesión (perssim-launch)
│   ├── ollama_client.py        ← cliente async Ollama (httpx)
│   ├── ollama_debug.py         ← logging de peticiones/respuestas Ollama
│   ├── models.py               ← modelos Pydantic compartidos
│   ├── tui.py                  ← interfaz de terminal (Rich)
│   └── __init__.py
├── config/                     ← plantillas de configuración
│   ├── session.example.config.json
│   └── char.example.config.json
├── tests/                      ← tests automatizados y datos de prueba
│   ├── bundles/
│   ├── session_test/
│   ├── test_char_turns.py
│   └── test_orchestrator_turns.py
└── docs/
    ├── design.md               ← arquitectura, endpoints, configuración
    ├── install.md              ← instalación y configuración de sesión
    └── usage.md                ← comandos, ejemplos, resolución de problemas
```

## Documentación

| Documento | Contenido |
|---|---|
| [`docs/design.md`](docs/design.md) | Arquitectura completa, flujo de turnos, API de endpoints y referencia de configuración |
| [`docs/install.md`](docs/install.md) | Requisitos previos, instalación del paquete y configuración de una sesión |
| [`docs/usage.md`](docs/usage.md) | Comandos del sistema, intervención del narrador y resolución de problemas |

## Requisitos

- Python 3.11+
- [Ollama](https://ollama.com) corriendo localmente con al menos un modelo descargado
- Bundles de personajes exportados desde [`simulation/`](../simulation/README.md)

## Inicio rápido

```bash
cd interact
pip install -e .

perssim-launch --session ./sessions/test-session-001/session.config.json
```

Ver [`docs/install.md`](docs/install.md) para la configuración completa.

## Relación con Simulation

Interact consume los Bundles exportados por el subsistema [`simulation/`](../simulation/README.md). Cada personaje en la sesión apunta a su Bundle en `char.config.json`:

```json
{
  "bundle_path": "../simulation/v1.1/Impl/001/Bundles/Bundle_narrative_Richelieu.md"
}
```
