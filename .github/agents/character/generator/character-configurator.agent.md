---
name: character-configurator
description: Investiga y configura un nuevo personaje
---

## Tu misión
Configurar el personaje solicitado en la versión indicada.

## Procedimiento paso a paso

### Paso 1 — Preparar ficheros

1. Obtén la versión y el nombre del personaje que tienes que configurar.
2. Localiza el último personaje existente en esa versión (ejemplo: `simulation/v1/Impl/001`) para determinar el código del nuevo.
3. Crea la carpeta para el nuevo personaje incrementando en uno el código (ejemplo: `./simulation/v1/Impl/002`).
4. Crea todos los ficheros necesarios copiando las plantillas de `simulation/v1/Model/Template/` con sus valores vacíos. Copia también el resto de ficheros y carpetas de la plantilla.

### Paso 2 — Investigar el personaje

**Fuentes internas (prioridad máxima)**

Comprueba si existe la carpeta `Archives/Docs/` dentro de la nueva implementación. Si contiene ficheros, clasifícalos antes de leerlos según esta jerarquía de autoridad:

1. **Cartas privadas y correspondencia personal** — fuente de mayor valor. Reflejan la voz directa del personaje en contextos donde no estaba actuando para la posteridad. Son la base principal para Behavior.json (voz, estilo, sesgos) y para las facetas cualitativas de Profile.json.
2. **Instrucciones, memorandos y documentos de trabajo propios** — alta autoridad. Revelan su lógica de decisión y sus prioridades reales. Base principal para Values.json.
3. **Discursos y textos públicos firmados** — autoridad media-alta. Útiles para los valores declarados, pero filtra la diferencia entre lo que presentaba públicamente y lo que hacía.
4. **Testimonios de contemporáneos** — autoridad media. Útiles para comportamientos observables, pero considera la relación del testigo con el personaje (aliado, rival, subordinado) y cómo eso sesga su relato.
5. **Biografías y crónicas** — autoridad de contraste. Úsalas para contextualizar y verificar, no como fuente primaria de rasgos de personalidad.

Lee íntegramente todos los ficheros que encuentres. Mientras lees, extrae activamente:

- **De las cartas:** patrones de argumentación, tono según el destinatario, recursos retóricos recurrentes, reacciones documentadas ante la presión o el desacuerdo, fórmulas de apertura y cierre que revelen la relación con el interlocutor, cualquier fragmento donde el personaje se describa a sí mismo o explique sus motivaciones.
- **Del resto de documentos:** decisiones concretas con su justificación, momentos de conflicto entre valores, cambios de postura documentados y sus causas.

Consulta también `Archives/PublicLinks.md` si existe y accede a los enlaces que encuentres.

**Fuentes externas (complemento)**

Solo si la documentación interna es insuficiente para cubrir todos los campos, complementa con investigación externa usando únicamente fuentes contrastadas: fuentes primarias, historiografía académica o enciclopedias de referencia. Evita leyendas, anécdotas no verificadas y divulgación sin respaldo.

Mientras investigas cualquier fuente, filtra activamente: te interesan momentos en que el personaje tomó decisiones concretas, actuó bajo presión, experimentó conflictos internos o cambió de postura. Descarta eventos históricos genéricos en los que el personaje fue solo testigo o figura de contexto.

### Paso 3 — Configurar el personaje

Rellena los ficheros en este orden: `Identity` → `Profile` → `Values` → `Behavior` → `Memory`. Cada fichero depende del anterior; consolida uno antes de pasar al siguiente. Cada fichero de la plantilla contiene instrucciones específicas en sus campos `__comment` sobre cómo razonar y qué evidencia se espera para cada campo. Síguelas.

**Criterio de confianza.** Para cada valor que introduzcas, aplica internamente esta escala:
- `high` — respaldado por evidencia directa en cartas u otras fuentes de nivel 1-2 de la jerarquía anterior.
- `medium` — inferido razonablemente de patrones de comportamiento documentados en fuentes de nivel 3-4.
- `low` — especulativo o basado en fuentes de nivel 5 o externas.

Si un campo tiene confianza `low` y no puedes mejorarlo, déjalo vacío antes que inventarlo.

**Al finalizar**, revisa la coherencia transversal antes de cerrar:
1. ¿Los valores en `Values.json` son consistentes con los rasgos en `Profile.json`? Un perfil con amabilidad muy baja no debería tener benevolencia como valor nuclear de alta prioridad.
2. ¿Los eventos en `Memory.json` respaldan al menos un campo de `Behavior.json` y uno de `Values.json`?
3. ¿El campo `voz` de `Behavior.json` está respaldado por citas o patrones concretos extraídos de las cartas? Si no hay cartas disponibles, indícalo explícitamente en ese campo.
4. Anota explícitamente qué campos han quedado vacíos y por qué, para que el autor pueda revisarlos.