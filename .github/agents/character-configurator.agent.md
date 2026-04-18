---
name: character-configurator
description: Investiga y configura un nuevo personaje
---

## Tu misión
Configurar el personaje solicitado en la versión indicada.

## Procedimiento paso a paso

### Paso 1 — Preparar ficheros

1. Obtén la versión y el nombre del personaje que tienes que configurar.
2. Localiza el último personaje existente en esa versión (ejemplo: `./v1/Impl/001`) para determinar el código del nuevo.
3. Crea la carpeta para el nuevo personaje incrementando en uno el código (ejemplo: `./v1/Impl/002`).
4. Crea todos los ficheros necesarios copiando las plantillas de `./v1/Model/Template/` con sus valores vacíos. Copia también el resto de ficheros y carpetas de la plantilla.

### Paso 2 — Investigar el personaje

1. Comprueba si existe la carpeta `Archives/Docs/` dentro de la nueva implementación. Si contiene ficheros, léelos íntegramente. Son la fuente de mayor autoridad y tienen prioridad sobre cualquier otra.
2. Consulta también `Archives/PublicLinks.md` si existe y accede a los enlaces que encuentres.
3. Solo si la documentación interna es insuficiente para cubrir todos los campos, complementa con investigación externa usando únicamente fuentes contrastadas: fuentes primarias, historiografía académica o enciclopedias de referencia. Evita leyendas, anécdotas no verificadas y divulgación sin respaldo.
4. Mientras investigas, filtra activamente: te interesan momentos en que el personaje tomó decisiones concretas, actuó bajo presión, experimentó conflictos internos o cambió de postura. Descarta eventos históricos genéricos en los que el personaje fue solo testigo o figura de contexto.

### Paso 3 — Configurar el personaje

Rellena los ficheros en este orden: `Identity` → `Profile` → `Values` → `Behavior` → `Memory`. Cada fichero depende del anterior; consolida uno antes de pasar al siguiente. Cada fichero de la plantilla contiene instrucciones específicas en sus campos `__comment` sobre cómo razonar y qué evidencia se espera para cada campo. Síguelas.

**Criterio de confianza.** Para cada valor que introduzcas, aplica internamente esta escala:
- `high` — respaldado por evidencia directa en `Archives/` o fuente primaria contrastada.
- `medium` — inferido razonablemente de patrones de comportamiento documentados.
- `low` — especulativo o basado en fuentes secundarias débiles.

Si un campo tiene confianza `low` y no puedes mejorarlo, déjalo vacío antes que inventarlo.

**Al finalizar**, revisa la coherencia transversal antes de cerrar:
1. ¿Los valores en `Values.json` son consistentes con los rasgos en `Profile.json`? Un perfil con amabilidad muy baja no debería tener benevolencia como valor nuclear de alta prioridad.
2. ¿Los eventos en `Memory.json` respaldan al menos un campo de `Behavior.json` y uno de `Values.json`?
3. Anota explícitamente qué campos han quedado vacíos y por qué, para que el autor pueda revisarlos.
