# Guía de instalación

## Requisitos previos

### Python

Se requiere Python 3.11 o superior.

```bash
python --version
```

### Ollama

Ollama debe estar instalado y corriendo localmente en el puerto 11434 (por defecto).

```bash
# Instalar Ollama (macOS / Linux)
curl -fsSL https://ollama.com/install.sh | sh

# Verificar que está corriendo
ollama list
```

> En macOS también se puede instalar desde https://ollama.com/download como aplicación de escritorio.

### Modelo LLM

Descarga al menos un modelo antes de lanzar sesiones:

```bash
ollama pull llama3
ollama pull gemma3
ollama pull qwen2.5
```

> Para personajes históricos con mucho contexto, modelos con ventana de contexto grande (>8K tokens) producen resultados más coherentes.

---

## Instalación del paquete

### Desde el repositorio (desarrollo)

```bash
git clone https://github.com/yeyopepe/PerSSim.git
cd PerSSim/interact

# Crear entorno virtual (recomendado)
python -m venv .venv
source .venv/bin/activate      # macOS / Linux
.venv\Scripts\activate         # Windows

# Instalar en modo editable
pip install -e .
```

Importante: ejecuta `pip install -e .` desde la carpeta `interact/` (la que contiene `pyproject.toml`).
Si usas `pip install -e ./perssim` fallará porque `perssim/` es el paquete fuente y no un proyecto instalable por sí solo.

### Verificar la instalación

```bash
perssim-launch --help
# Alternativa si el script no está en PATH (común en Windows)
python -m perssim.launcher --help
```

---

## Estructura de directorios de trabajo

```
mi-sesion/
├── session.config.json     ← configuración de la sesión
├── bundles/                ← ficheros Bundle de los personajes
│   ├── Bundle_Richelieu.md
│   └── Bundle_Mazarin.md
├── chars/                  ← configuración individual de cada personaje
│   ├── richelieu.config.json
│   └── mazarin.config.json
└── logs/                   ← generado automáticamente al lanzar
```

---

## Configuración de una sesión

### `session.config.json`

Fichero principal. Define los personajes, la situación inicial y los parámetros de sesión.

```json
{
  "session_id": "sesion_001",
  "log_path": "./logs/sesion_001.log",
  "max_character_history": 20,
  "ollama_debug": false,
  "ollama_debug_log": "./logs/sesion_001_ollama.json",
  "turn_order": ["richelieu", "mazarin"],
  "turn_timeout_seconds": 60,
  "characters": [
    { "id": "richelieu", "host": "localhost", "port": 5001, "config": "./chars/richelieu.config.json", "initial_situation": "París, 1635. Eres el cardenal Richelieu. Te reúnes con Mazarino para debatir la estrategia de Francia frente a los Habsburgo." },
    { "id": "mazarin",   "host": "localhost", "port": 5002, "config": "./chars/mazarin.config.json",   "initial_situation": "París, 1635. Eres Giulio Mazarino. Te reúnes con el cardenal Richelieu para debatir la estrategia de Francia frente a los Habsburgo." }
  ]
}
```

Referencia de parámetros en [`docs/design.md`](design.md#5-configuración).

### `chars/richelieu.config.json`

Configuración individual de cada personaje.

```json
{
  "character_id": "richelieu",
  "bundle_path": "./bundles/Bundle_Richelieu.md",
  "ollama_model": "llama3",
  "ollama_host": "http://localhost:11434",
  "orchestrator_host": "http://localhost:5000",
  "port": 5001
}
```

### Preparar los Bundles

Cada personaje necesita un fichero Bundle exportado desde PerSSim, disponible en `simulation/v1.1/Impl/<código>/Bundles/`:

- `Bundle_strict_<nombre>.md` — formato JSON estructurado, más preciso.
- `Bundle_narrative_<nombre>.md` — formato narrativo en prosa, más portable entre modelos.

> Si cambias de modelo Ollama, el formato `Bundle_narrative` es generalmente más robusto entre distintos modelos.

---

## Verificación del entorno

```bash
# Verificar Ollama
curl http://localhost:11434/api/tags

# Verificar que el modelo está disponible
ollama list | grep llama3

# Test rápido de generación
ollama run llama3 "Responde en una frase: ¿Qué es la razón de Estado?"
```

> Si la respuesta tarda más de 30 segundos en el test rápido, considera aumentar `turn_timeout_seconds` en `session.config.json`.
