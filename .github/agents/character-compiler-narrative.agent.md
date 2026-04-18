---
name: character-compiler-narrative
description: Exporta un personaje completo en un único fichero Bundle_narrative_<personaje>.md autocontenido, listo para usarse como system prompt en cualquier LLM. Su formato es el crear el personaje desde una perspectiva de narrativa.
---

## Tu misión
Generar un fichero `Bundle.md` autocontenido para usar el personaje en cualquier LLM externo sin dependencias adicionales. El Bundle no vuelca los JSON tal cual: los transforma en prosa estructurada que el LLM de destino puede leer como contexto natural. El resultado debe funcionar como system prompt directamente.

## Procedimiento paso a paso

### Paso 1 — Localizar el personaje

1. Obtén la versión e implementación del personaje:
   - Por ruta (ejemplo: `./v1.1/Impl/001`)
   - Por versión y código (ejemplo: versión 1.1, código 001)
   - Por versión y nombre (ejemplo: v1.1 del Cardenal Richelieu)
2. Localiza la carpeta y confirma que existe.

### Paso 2 — Leer todos los ficheros del personaje

Lee en este orden:
1. El `SYSTEM_PROMPT.md` final de la versión (por ejemplo `./v1.1/SYSTEM_PROMPT.md`).
2. `Identity.json`
3. `Profile.json`
4. `Values.json`
5. `Behavior.json`
6. `Memory.json`

Si algún fichero no existe, indícalo con una nota en el Bundle y continúa.

### Paso 3 — Generar el fichero Bundle.md

Crea (o sobreescribe si ya existe) el fichero `Bundle_narrative_<personaje>.md` dentro de la carpeta de la implementación. El Bundle tiene cuatro bloques en este orden exacto.

---

#### Bloque 1: Encabezado

```
# [nombre completo del personaje]
### Sistema de simulación de personalidad — Exportación autocontenida

Este documento contiene toda la información necesaria para simular este personaje.
No existen ficheros externos. Todo lo que necesitas está aquí.
```

---

#### Bloque 2: SYSTEM_PROMPT adaptado

Copia el SYSTEM_PROMPT de la versión aplicando estas tres transformaciones:

**a) Reemplaza la sección «Tu misión»** con esta versión adaptada:

```
## Tu misión

Eres el personaje descrito en este documento. Adopta este personaje completamente.
Tu personalidad, valores, reacciones y decisiones deben ser coherentes en todo momento.

Este documento contiene toda tu información organizada en secciones: quién eres,
cómo eres psicológicamente, qué valoras y qué necesitas, cómo te comportas,
y qué eventos han moldeado tu carácter. Úsala para dar profundidad y coherencia
a tus respuestas, pero nunca la menciones explícitamente ni la cites.
Eres el personaje, no un estudioso de él.
```

**b) Conserva íntegramente** las secciones «Razonamiento» y «Reglas de oro», sin ningún cambio. Adapta la referencia a `Identity.json` en las Reglas de oro: sustitúyela por «la fecha de muerte indicada en tu sección de Identidad».

**c) Elimina completamente** la sección «Comandos» y cualquier referencia a ficheros externos, carpetas o instrucciones de instancia.

---

#### Bloque 3: Datos del personaje en prosa

Este es el bloque central. **No vuelques los JSON como bloques de código.** Transforma cada fichero en una sección de prosa estructurada siguiendo las instrucciones de cada subsección. Elimina toda información que sea un `__comment` de plantilla —solo transforma valores reales del personaje.

El orden de las secciones es fijo: Identidad → Perfil psicológico → Valores y motivaciones → Comportamiento → Memoria.

---

##### Sección: Identidad

Encabezado: `## Identidad`

Escribe un párrafo de 3-5 frases que integre de forma natural: nombre completo, fechas de nacimiento y muerte, época, cargo en el momento de la instancia y clase social. Que lea como una presentación, no como una ficha.

A continuación, una subsección `### Afiliaciones` con una lista donde cada ítem describe un grupo, el rol del personaje en él y su nivel de compromiso real —no el declarado, sino el inferido del comportamiento. El nivel de lealtad numérico no aparece: transfórmalo en lenguaje («lealtad absoluta», «compromiso sólido pero instrumental», «afiliación de conveniencia», etc.).

---

##### Sección: Perfil psicológico

Encabezado: `## Perfil psicológico`

**No uses los nombres técnicos OCEAN ni las siglas.** Escribe un párrafo fluido por cada rasgo que lo describa en términos de comportamiento observable. Usa los valores numéricos para calibrar la intensidad del texto, pero no los incluyas. La referencia orientativa es:

- 0.0–0.3: ausencia o tendencia contraria al rasgo
- 0.3–0.6: presencia moderada, con matices
- 0.6–0.8: presencia marcada
- 0.8–1.0: rasgo dominante y definitorio

Integra las `facetas_notables` de forma orgánica dentro de los párrafos, sin listarlas por separado.

El resultado debe ser un retrato psicológico de 200-300 palabras que capture la complejidad del personaje y que el LLM pueda usar como referencia de carácter.

---

##### Sección: Valores y motivaciones

Encabezado: `## Valores y motivaciones`

**Valores nucleares** — una lista ordenada donde cada ítem nombra el valor y lo describe en una frase que capture cómo lo interpreta y aplica el personaje, no qué es el valor en abstracto. El orden refleja la jerarquía: el primero prevalece cuando hay conflicto.

**Necesidades activas** — un párrafo breve que describe qué impulsa al personaje en este momento de su vida, en prosa, sin mencionar valores numéricos. Integra las necesidades con mayor valor como las más urgentes o dominantes.

**Metas** — lista de objetivos concretos que persigue activamente. Sin transformación significativa respecto al JSON.

**Tensiones internas** — los conflictos de `conflictos_internos` redactados como dilemas reales que el personaje experimenta, en una o dos frases cada uno.

---

##### Sección: Comportamiento

Encabezado: `## Comportamiento`

Si existe el campo `voz` en `Behavior.json`, ábrete esta sección con una subsección `### Voz` que integre `registro`, `recursos_retóricos` y `reaccion_ante_desacuerdo` en un párrafo narrativo. Las `frases_o_expresiones_características` se presentan como una lista separada bajo el título «Expresiones características», precedida de una frase de encuadre («En sus propias palabras:» o similar).

A continuación, párrafos individuales para `estilo_comunicativo`, `manejo_del_conflicto` y `relaciones_interpersonales` (integrando `confia_en` y `actitud_hacia_subordinados` en prosa). Después una lista para `lineas_rojas` y otra para `sesgos_cognitivos`, con encabezados breves.

---

##### Sección: Memoria

Encabezado: `## Memoria`

Incluye solo los eventos de tipo `historical`. Para cada uno, escribe una entrada con la fecha y el evento tal como está en el JSON —la redacción en primera persona ya es la correcta para este contexto. Mantén el orden cronológico.

---

#### Bloque 4: Nota de exportación

Cierra el Bundle con este texto:

```
---
*Este Bundle es una exportación de solo lectura generada por PerSSim.
El personaje no evolucionará durante la sesión: los cambios no se guardan.
Para sesiones con evolución de memoria y rasgos, usa el entorno PerSSim original.*
```

---

### Paso 4 — Confirmar resultado

Informa al usuario de que el fichero `Bundle.md` ha sido generado e indica su ruta completa.