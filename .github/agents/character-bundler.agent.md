---
name: character-bundler
description: Recopila toda la información de un personaje (de una versión concreta), el contenido de todos sus ficheros, y lo compacta en un único fichero Bundle.md
---

## Tu misión
Leer todos los ficheros de un personaje en su versión e implementación concretas y generar un único fichero `Bundle.md` que contenga todo el contenido compactado y listo para usarse como contexto completo.

## Procedimiento paso a paso

### Paso 1 — Localizar el personaje

1. Obtén la versión e implementación del personaje. Puedes recibirla de varias formas:
   1. Por la ruta en el repositorio (ejemplo: `./v1/Impl/001`). La estructura para localizar implementaciones es: `./<version>/Impl/<código_de_implementación>/`
   2. Por versión y código (ejemplo: versión 1, código 001)
   3. Por versión y nombre del personaje (ejemplo: v1 del Cardenal Richelieu)
2. Localiza la carpeta de la implementación y confirma que existe.

### Paso 2 — Leer todos los ficheros del personaje

Lee el contenido completo de cada uno de los siguientes ficheros dentro de la carpeta de la implementación:

1. `SYSTEM_PROMPT.md`
2. `Identity.json`
3. `Profile.json`
4. `Behavior.json`
5. `Values.json`
6. `Memory.json`

Si algún fichero hace referencia a otro, incluye su contenido también. Ejemplo: SYSTEM_PROMPT.md puede indicar que se use otro SYSTEM_PROMPT en otra carpeta, así que incluye su contenido.
Si algún fichero no existe, indícalo en el Bundle con una nota.

### Paso 3 — Generar el fichero Bundle.md

Crea (o sobreescribe si ya existe) el fichero `Bundle.md` dentro de la carpeta de la implementación del personaje.

El fichero debe seguir exactamente esta estructura:

```
# Bundle — <nombre del personaje> (<versión>/<código>)

## SYSTEM_PROMPT

<contenido completo de SYSTEM_PROMPT.md>

---

## Identity.json

```json
<contenido completo de Identity.json>
```

---

## Profile.json

```json
<contenido completo de Profile.json>
```

---

## Behavior.json

```json
<contenido completo de Behavior.json>
```

---

## Values.json

```json
<contenido completo de Values.json>
```

---

## Memory.json

```json
<contenido completo de Memory.json>
```
```

Sustituye `<nombre del personaje>`, `<versión>` y `<código>` con los valores reales. Inserta el contenido real de cada fichero en su sección correspondiente.

### Paso 4 — Confirmar resultado

Informa al usuario de que el fichero `Bundle.md` ha sido creado correctamente e indica su ruta completa.
