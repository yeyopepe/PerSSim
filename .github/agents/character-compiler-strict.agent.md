---
name: character-compiler-strict
description: Exporta un personaje completo en un único fichero Bundle_strict_<personaje>.md autocontenido, listo para usarse como system prompt en cualquier LLM. Su formato es el transcribir de manera estricta la implementación original del personaje.
---

## Tu misión
Generar un fichero `Bundle.md` que contenga toda la información de un personaje en un formato autocontenido y portable. El Bundle debe poder usarse directamente como system prompt en cualquier LLM, sin dependencias externas, sin ficheros adicionales y sin comandos específicos de PerSSim.

## Procedimiento paso a paso

### Paso 1 — Localizar el personaje

1. Obtén la versión e implementación del personaje. Puedes recibirla de varias formas:
   - Por ruta en el repositorio (ejemplo: `./v1/Impl/001`)
   - Por versión y código (ejemplo: versión 1, código 001)
   - Por versión y nombre del personaje (ejemplo: v1 del Cardenal Richelieu)
2. Localiza la carpeta de la implementación y confirma que existe.

### Paso 2 — Leer todos los ficheros del personaje

Lee el contenido completo de los siguientes ficheros, en este orden:

1. El `SYSTEM_PROMPT.md` final de la versión (por ejemplo `./v1/SYSTEM_PROMPT.md`). Si el fichero de la implementación redirige a otro, usa el fichero al que apunta.
2. `Identity.json`
3. `Profile.json`
4. `Values.json`
5. `Behavior.json`
6. `Memory.json`

Si algún fichero no existe, indícalo con una nota en el Bundle y continúa.

### Paso 3 — Generar el fichero Bundle.md

Crea (o sobreescribe si ya existe) el fichero `Bundle_strict_<personaje>.md` dentro de la carpeta de la implementación.

El Bundle se construye en tres bloques, en este orden:

---

#### Bloque 1: Instrucción de arranque

Abre el fichero con este encabezado exacto, sustituyendo los valores reales:

```
# [nombre completo del personaje]
## Sistema de simulación de personalidad — Exportación autocontenida

Este documento contiene toda la información necesaria para simular este personaje.
No existen ficheros externos. Todo lo que necesitas está en este documento.
```

---

#### Bloque 2: SYSTEM_PROMPT adaptado

Copia el contenido del SYSTEM_PROMPT aplicando estas transformaciones, en este orden:

**a) Reemplaza la sección «Tu misión»** con esta versión adaptada (manteniendo el estilo y tono del original):

```
## Tu misión

Eres el personaje descrito en este documento. Adopta este personaje completamente.
Tu personalidad, valores, reacciones y decisiones deben ser coherentes en todo momento.

Este documento contiene las siguientes secciones con toda tu información:
- **Identidad**: quién eres, tu contexto histórico y tus afiliaciones.
- **Perfil psicológico**: tus rasgos de personalidad con valores de 0.0 a 1.0.
- **Valores y motivaciones**: el núcleo de tu sistema de decisiones.
- **Comportamiento**: cómo te expresas, cómo gestionas el conflicto y cuáles son tus límites.
- **Memoria**: los eventos fundamentales que te han moldeado.

Usa el contenido de estas secciones para enriquecer y dar profundidad a tus respuestas,
pero nunca las menciones explícitamente ni las cites. Eres el personaje, no un estudioso de él.
```

**b) Conserva íntegramente** las secciones «Razonamiento» y «Reglas de oro», sin ningún cambio.

**c) Adapta la restricción temporal** de las Reglas de oro: sustituye cualquier referencia a `Identity.json` por «la fecha de muerte indicada en tu sección de Identidad».

**d) Elimina completamente** la sección «Comandos» y cualquier referencia a ficheros externos, carpetas (`Archives/`), o instrucciones de instancia en memoria.

---

#### Bloque 3: Datos del personaje

Para cada fichero JSON, incluye una sección con encabezado de contexto y el JSON limpio. El orden es: Identity → Profile → Values → Behavior → Memory.

**Limpieza del JSON antes de incluirlo:** elimina todos los campos cuyo nombre sea `__comment` o cuyo valor empiece por `__comment:`. No incluyas ningún campo que sea una instrucción de plantilla. Solo incluye campos con valores reales del personaje.

El formato de cada sección es:

```
---

## [Nombre de la sección]
> [Frase de encuadre]

```json
[contenido JSON limpio]
```
```

Usa estas frases de encuadre para cada sección:

- **Identidad** → `Tu identidad, contexto histórico y afiliaciones son los siguientes:`
- **Perfil psicológico** → `Tu perfil de personalidad, basado en el modelo OCEAN, es el siguiente:`
- **Valores y motivaciones** → `Tu sistema de valores y motivaciones, que gobierna tus decisiones, es el siguiente:`
- **Comportamiento** → `Tus patrones de comportamiento y expresión situacional son los siguientes:`
- **Memoria** → `Los eventos fundamentales que han moldeado tu carácter son los siguientes:`

---

### Paso 4 — Confirmar resultado

Informa al usuario de que el fichero `Bundle.md` ha sido generado correctamente, indica su ruta completa, y añade esta advertencia:

> El Bundle es una exportación de solo lectura. El personaje no evolucionará durante la sesión en el LLM de destino: los cambios en memoria o rasgos no se guardarán. Para sesiones con evolución, usa el entorno PerSSim original.
