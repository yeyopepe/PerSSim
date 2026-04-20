# PerSSim — Interact

Sistema multi-agente que instancia varios personajes PerSSim y los hace dialogar de forma autónoma o dirigida. Cada personaje corre como un servidor HTTP independiente coordinado por un orquestador central. Usa modelos locales vía Ollama.

## Cómo funciona

Cada personaje se carga con su Bundle como system prompt y toma decisiones autónomas sobre cuándo intervenir. El orquestador distribuye las intervenciones, lleva el registro de la conversación y sirve de interfaz al usuario. El usuario puede introducir mensajes como narrador o congelar/reanudar el diálogo en cualquier momento.

## Estructura

```
interact/
├── README.md                  ← este fichero
└── docs/
    ├── design.md              ← arquitectura, endpoints, modelos de datos, plan de implementación
    ├── install.md             ← requisitos, instalación, configuración
    └── usage.md               ← comandos, interfaz de terminal, ejemplos
```

El código fuente (paquete Python `persim-interact`) se añadirá en esta carpeta en fases posteriores.

## Documentación

| Documento | Contenido |
|---|---|
| [`docs/design.md`](docs/design.md) | Arquitectura completa, API de endpoints, ficheros de configuración y plan de implementación por fases |
| [`docs/install.md`](docs/install.md) | Requisitos previos, instalación del paquete y configuración de una sesión |
| [`docs/usage.md`](docs/usage.md) | Comandos del sistema, intervención del narrador, ejemplos de sesión y resolución de problemas |

## Requisitos

- Python 3.11+
- [Ollama](https://ollama.com) corriendo localmente con al menos un modelo descargado
- Bundles de personajes exportados desde [`simulation/`](../simulation/README.md)

## Inicio rápido

```bash
pip install persim-interact

persim-launch --session ./session.config.json
```

Ver [`docs/install.md`](docs/install.md) para la configuración completa.

## Relación con Simulation

Interact consume los Bundles exportados por el subsistema [`simulation/`](../simulation/README.md). Cada personaje en la sesión apunta a su Bundle en `char.config.json`:

```json
{
  "bundle_path": "../simulation/v1.1/Impl/001/Bundles/Bundle_narrative_Richelieu.md"
}
```