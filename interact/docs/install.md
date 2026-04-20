# Guía de instalación

## Requisitos previos

### Python

Se requiere Python 3.11 o superior.

```bash
python --version
```

Si necesitas instalar Python: https://www.python.org/downloads/

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
ollama pull mistral
ollama pull qwen2.5
```

> Para personajes históricos con mucho contexto, modelos con ventana de contexto grande (>8K tokens) producen resultados más coherentes. Se recomienda `llama3` o `qwen2.5` como punto de partida.

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

### Desde PyPI (cuando esté publicado)

```bash
pip install persim-interact
```

### Verificar la instalación

```bash
persim-launch --help
```

Deberías ver el mensaje de ayuda con las opciones disponibles.

---

## Estructura de directorios de trabajo

Una vez instalado, crea una carpeta de trabajo para tu sesión:

```
mi-sesion/
├── session.config.json            # Configuración de la sesión
├── bundles/                # Ficheros Bundle de los personajes
│   ├── Bundle_Richelieu.md
│   └── Bundle_Mazarin.md
├── chars/                  # Configuración de cada personaje
│   ├── richelieu.config.json
│   └── mazarin.config.json
└── logs/                   # Generado automáticamente
```

> Puedes generar esta estructura con ficheros de ejemplo con: `persim-launch --init mi-sesion`

---

## Configuración de una sesión

### `session.config.json`

Fichero principal. Define los personajes que participan, la ruta del log y la situación inicial.

```json
{
  "session_id": "sesion_001",
  "log_path":   "./logs/sesion_001.jsonl",
  "initial_situation": "París, 1635. El cardenal Richelieu y Giulio Mazarino se reúnen para debatir la estrategia de Francia frente a los Habsburgo.",
  "characters": [
    { "id": "richelieu", "host": "localhost", "port": 5001, "config": "./chars/richelieu.config.json" },
    { "id": "mazarin",   "host": "localhost", "port": 5002, "config": "./chars/mazarin.config.json" }
  ]
}
```

### `chars/richelieu.config.json`

Fichero de configuración individual de cada personaje.

```json
{
  "character_id":      "richelieu",
  "bundle_path":       "./bundles/Bundle_Richelieu.md",
  "ollama_model":      "llama3",
  "ollama_host":       "http://localhost:11434",
  "orchestrator_host": "http://localhost:5000",
  "port":              5001,
  "wait_min_seconds":  30,
  "wait_max_seconds":  120
}
```

> `wait_min_seconds` y `wait_max_seconds` controlan el rango de tiempo aleatorio que el personaje espera antes de decidir si interviene espontáneamente.

### Preparar los Bundles

Cada personaje necesita un fichero Bundle exportado desde PerSSim, disponible en `Impl/<código>/Bundles/`:

- `Bundle_strict_<nombre>.md` — formato JSON estructurado, más preciso.
- `Bundle_narrative_<nombre>.md` — formato narrativo en prosa, más portable entre modelos.

> Si cambias de modelo Ollama, el formato `Bundle_narrative` es generalmente más robusto entre distintos modelos que el `Bundle_strict`.

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

> Si la respuesta tarda más de 30 segundos en el test rápido, considera aumentar `wait_min_seconds` en la configuración del personaje para evitar timeouts.
