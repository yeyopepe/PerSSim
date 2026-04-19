# PerSSim — Base de investigación

Este documento recoge el estado del arte científico y las decisiones de diseño que fundamentan el framework PerSSim. Está organizado en cuatro bloques: el estado actual de la psicología del modelado de personalidad, los intentos previos de simulación computacional, el modelo de toma de decisiones jerárquico que adopta PerSSim, y las decisiones de diseño concretas que derivan de todo lo anterior.

---

## 1. Estado actual de la psicología sobre modelado de personalidad

El modelado computacional de la personalidad humana es uno de los retos más ambiciosos en la intersección entre psicología, ciencias cognitivas e inteligencia artificial. Ningún marco teórico único es suficiente: cada uno captura una dimensión distinta del problema.

### 1.1 El modelo Big Five / OCEAN

El marco más robusto y ampliamente adoptado en psicología científica es el Modelo de los Cinco Grandes Factores (Big Five o OCEAN), desarrollado originalmente por Lewis Goldberg y formalizado por Costa y McCrae. Define la personalidad a través de cinco dimensiones continuas:

- **Openness** (Apertura): curiosidad intelectual, creatividad, apreciación estética.
- **Conscientiousness** (Responsabilidad): autodisciplina, planificación, orientación al logro.
- **Extraversion** (Extraversión): sociabilidad, asertividad, búsqueda de estimulación.
- **Agreeableness** (Amabilidad): cooperación, empatía, confianza interpersonal.
- **Neuroticism** (Neuroticismo): tendencia a la inestabilidad emocional, ansiedad, reactividad al estrés.

Cada dimensión se expresa como valor continuo, no binario. Investigaciones recientes (Sorokovikova et al., 2024; Park et al., 2023) confirman que los LLMs pueden simular estos rasgos de forma determinista cuando se les indica mediante prompts estructurados. Modelos avanzados como GPT-4o muestran alta fidelidad en tests psicométricos estándar (BFI, IPIP-NEO).

**Fortaleza clave:** validación en más de 80 países, instrumentos estandarizados, correlación demostrada con comportamientos observables. Es el punto de partida más sólido para un modelo de datos.

**Limitación importante:** el Big Five describe el *cómo* de la personalidad —tendencias estables de comportamiento— pero no explica el *por qué* motivacional. No predice bien las decisiones en situaciones de conflicto de valores.

### 1.2 HEXACO y la dimensión de Honesty-Humility

Desarrollado por Ashton y Lee (2004) a partir de estudios lexicográficos cross-culturales, HEXACO añade un sexto factor al modelo OCEAN: **Honesty-Humility**. Este rasgo captura la tendencia a ser sincero, justo y no manipulador, y su polo bajo agrupa los rasgos de la tríada oscura: narcisismo, maquiavelismo y psicopatía.

Para simulaciones históricas, la dimensión H-H es especialmente relevante porque una proporción desproporcionada de los personajes que *protagonizan* los grandes eventos históricos puntúan bajo en ella. La tríada oscura no es simplemente «maldad»: genera patrones de comportamiento específicos y predecibles que son distintos de tener valores egoístas.

- **Narcisismo:** grandiosidad, necesidad de admiración, reacción desproporcionada a la crítica. El narcisista puede actuar contra sus propios intereses estratégicos si su ego está amenazado.
- **Maquiavelismo:** disposición a manipular e instrumentalizar de forma calculada. Lo que frena al maquiavélico no es la moral sino la utilidad esperada.
- **Psicopatía:** impulsividad, ausencia de empatía y remordimiento. La variante primaria (frialdad sin ansiedad) es más estable y socialmente funcional que la secundaria.

PerSSim implementa H-H como campo adicional en `Profile.json` en lugar de adoptar HEXACO completo, preservando la compatibilidad con la mayor base de investigación existente sobre Big Five en LLMs.

### 1.3 La Teoría de Valores Básicos de Schwartz

Desarrollada por Shalom Schwartz (1992, refinada en 2012), esta teoría identifica 19 valores básicos organizados en un continuum circular donde los valores adyacentes son compatibles y los opuestos generan tensión motivacional. A diferencia de los rasgos Big Five, los valores explican el *por qué* de las decisiones.

Los valores se organizan en cuatro dimensiones de orden superior: Apertura al cambio, Conservación, Autoengrandecimiento y Autotrascendencia. Investigaciones con LLMs usando el Portrait Values Questionnaire (Schwartz et al., 2024) confirman que los modelos pueden expresar perfiles de valores diferenciados que predicen sus respuestas ante dilemas éticos.

**Relevancia para PerSSim:** los valores de Schwartz están organizados en una jerarquía individual de prioridades que guía las decisiones cuando hay conflicto entre opciones. Este es exactamente el mecanismo que implementa `Values.json`: una lista ordenada de valores nucleares donde la prioridad determina qué prevalece cuando dos valores entran en conflicto directo.

### 1.4 Marcos complementarios

**Jerarquía de necesidades de Maslow.** Aunque su representación piramidal rígida ha sido revisada, el núcleo es útil: las necesidades fisiológicas, de seguridad, afiliación, estima y autorrealización tienen distinto peso según el contexto vital del individuo. El nivel de satisfacción de cada necesidad condiciona qué motivaciones son salientes en cada momento. PerSSim implementa esto en el campo `necesidades_activas` de `Values.json`.

**Identidad Social (Tajfel & Turner).** Define cómo los individuos construyen su identidad a partir de los grupos a los que pertenecen. Para personajes históricos, las identidades de grupo son frecuentemente las más determinantes del comportamiento político y social. PerSSim implementa esto en `identidades_de_grupo` dentro de `Identity.json`.

**Psicología narrativa (McAdams).** La identidad personal es una narrativa autobiográfica en construcción continua. La personalidad no es un conjunto de rasgos fijos sino una historia que el individuo se cuenta sobre quién es y por qué actúa. Esta perspectiva fundamenta el uso del corpus biográfico —cartas, diarios, discursos— como fuente primaria de configuración: son precisamente esa narrativa en primera persona.

**Psicología del desarrollo adulto (Erikson, Levinson).** La personalidad no es estática: tiene patrones de cambio a lo largo de la vida con transiciones reconocibles. Para simulaciones en distintos momentos vitales de un personaje, el estado evolutivo importa. PerSSim lo gestiona mediante el campo `id` con año de instancia y el comando `/Fecha`, que permite situar al personaje en un momento concreto de su trayectoria.

---

## 2. Intentos previos de modelado y simulación

### 2.1 Agentes BDI (Belief-Desire-Intention)

El modelo BDI, formalizado por Bratman (1987) y adaptado para software por Rao y Georgeff (1995), es la arquitectura de agente racional más influyente en IA clásica. Representa el estado mental del agente en tres componentes:

- **Beliefs:** representación del estado del mundo, subjetiva y potencialmente incorrecta.
- **Desires:** objetivos que el agente desearía alcanzar, posiblemente conflictivos.
- **Intentions:** el subconjunto de deseos al que el agente ha comprometido recursos.

El ciclo BDI actualiza creencias, delibera sobre deseos para adoptar intenciones, y ejecuta planes. Su ventaja es separar la deliberación de la ejecución. Su limitación principal es que requiere que el diseñador defina explícitamente el espacio de planes, inviable para entornos abiertos. La combinación BDI + LLM resuelve este problema al delegar la generación de planes al modelo de lenguaje.

Investigaciones recientes han combinado BDI con Big Five en la arquitectura **P-R-B** (Personality-Role-Belief, 2026), que usa rasgos OCEAN para inicializar las creencias del agente sistemáticamente. El proyecto **CharacterBox** (2024) implementa agentes LLM con modelado BDI y memoria vectorial, supervisados por un agente narrador.

### 2.2 Generative Agents (Stanford, Park et al., 2023-2024)

El trabajo seminal de Park et al. introdujo agentes computacionales que simulan comportamiento humano creíble en entornos sandbox. La arquitectura tiene tres componentes: un *memory stream* en lenguaje natural, *reflection* periódica que sintetiza memorias en ideas de mayor nivel, y *planning* basado en el perfil, las memorias y las reflexiones.

En un trabajo posterior (2024), el mismo grupo escaló la arquitectura a 1.052 individuos reales, cada uno representado por su transcripción completa de entrevista de dos horas. Los agentes replicaron las respuestas de los participantes en encuestas de ciencias sociales con un **85% de precisión** respecto a la autoconsistencia humana dos semanas después.

**Implicación directa para PerSSim:** para personajes históricos reales, el equivalente de la «entrevista» es el corpus biográfico: cartas, diarios, discursos, testimonios de contemporáneos. Cuanto más rico y en primera persona sea este corpus, mejor será la simulación. Esto fundamenta la arquitectura de `Archives/Docs/` y la jerarquía de autoridad de fuentes.

### 2.3 Character-LLM y simulación de figuras históricas

El proyecto Character-LLM (Shao et al., 2023) aborda directamente la simulación de personajes históricos reales: Beethoven, Cleopatra, Julio César. Su metodología incluye *Experience Reconstruction* (generación de escenas de experiencia detalladas a partir de datos biográficos) y *Protective Experiences* (experiencias diseñadas para anclar al agente a su época, evitando conocimiento anacrónico). Los agentes entrenados mostraron mayor consistencia de carácter que los basados solo en prompts.

PerSSim adopta el concepto de Protective Experiences mediante la regla de oro de restricción temporal del SYSTEM_PROMPT y el comando `/Fecha`.

### 2.4 PsyAgent (2026)

PsyAgent combina un perfil de rasgos Big Five (Individual Structure) con un catálogo de marcos contextuales de rol-relación-norma (Multi-Scenario Contexting). Los prompts estructurados acoplan el contexto activo con el perfil para generar comportamiento estable pero sensible al contexto. Mejora la fidelidad de rasgos y la estabilidad a largo plazo frente a modelos base de mayor tamaño.

### 2.5 Videojuegos como precedente

The Sims (Maxis, 2000) implementó un sistema de personalidad con cinco rasgos numéricos y un sistema de «needs» que modulaba la selección de acciones. Es el precedente más influyente del modelado de personalidad en tiempo real. Los juegos de rol contemporáneos (Mass Effect, Dragon Age) usan árboles de comportamiento con rasgos que ajustan probabilidades de selección de acción — eficaces para comportamientos simples pero que no escalan a interacciones abiertas.

---

## 3. El modelo de toma de decisiones de PerSSim

### 3.1 Jerarquía de cinco capas

PerSSim estructura la toma de decisiones del agente en cinco capas jerárquicas donde las capas superiores filtran y condicionan a las inferiores. El flujo es top-down con feedback bottom-up.

| Capa | Concepto psicológico | Fichero | Velocidad de cambio |
|---|---|---|---|
| 1. Valores nucleares | Schwartz / Moral Foundations | `Values.json` → `valores_nucleares` | Décadas |
| 2. Necesidades activas | Maslow / homeostasis | `Values.json` → `necesidades_activas` | Días / semanas |
| 3. Metas e intereses | BDI Desires / Goals | `Values.json` → `metas_vitales` | Meses / años |
| 4. Disposiciones situacionales | Big Five + Emociones | `Profile.json` + `Behavior.json` | Estable en adultos |
| 5. Respuestas contextuales | BDI Intentions + Plans | Razonamiento del LLM | Segundos / minutos |

Una situación activa la Capa 5, que consulta las disposiciones de la Capa 4, que selecciona entre las metas de la Capa 3 la más compatible con los valores de la Capa 1 teniendo en cuenta el estado de necesidades de la Capa 2.

### 3.2 El razonamiento en cadena como mecanismo de decisión

El SYSTEM_PROMPT implementa este modelo mediante una cadena de razonamiento de cinco pasos que el agente ejecuta internamente antes de cada respuesta:

1. ¿Esta acción entra en conflicto con mis valores nucleares? *(Capa 1)*
2. ¿Qué necesidades mías están en juego en este momento? *(Capa 2)*
3. ¿Cómo afecta esta acción a mis metas vitales? *(Capa 3)*
4. ¿Cómo reaccionaría típicamente alguien con mi personalidad? *(Capa 4)*
5. Dada la situación concreta, ¿cuál es mi respuesta más auténtica? *(Capa 5)*

El razonamiento es interno y no se muestra: la única respuesta visible es la del personaje en primera persona.

### 3.3 Conflicto entre valores y resolución

Schwartz demostró que los valores no son aditivos sino que compiten en un continuum circular. La resolución de estos conflictos define el carácter del personaje más que sus valores individuales. PerSSim implementa esto mediante el orden de `valores_nucleares` en `Values.json`: cuando dos valores entran en conflicto, el de mayor prioridad prevalece. El campo `conflictos_internos` documenta las tensiones recurrentes del personaje, que son las más reveladoras de su carácter.

### 3.4 Evolución de la personalidad

La resistencia al cambio varía por capa. Los valores nucleares (Capa 1) son casi inmutables y requieren evidencia muy sólida y sostenida para modificarse. Las necesidades activas (Capa 2) pueden ajustarse con más frecuencia según el contexto de la sesión. El perfil OCEAN cambia muy lentamente y solo ante patrones consistentes a lo largo de múltiples sesiones.

El comando `/Actualizar` implementa este mecanismo: propone cambios justificados con evidencia de sesión explícita, con mayor umbral de exigencia para las capas superiores.

---

## 4. Decisiones de diseño de PerSSim

### 4.1 JSON como formato base

El formato JSON para los ficheros de configuración responde a tres criterios: es nativo para LLMs (entrenados con grandes cantidades de JSON estructurado), soporta validación formal, y puede inyectarse directamente como contexto. Los campos `__comment` en las plantillas actúan como instrucciones embebidas para el agente configurador sin afectar al funcionamiento del agente de simulación.

### 4.2 Separación de responsabilidades entre ficheros

La separación en cinco ficheros (Identity, Profile, Values, Behavior, Memory) no es arbitraria: cada uno corresponde a una capa o conjunto de capas del modelo de decisión, tiene una velocidad de cambio distinta, y puede actualizarse independientemente. Esto permite, por ejemplo, usar `/Fecha` para retroceder en el tiempo afectando a Memory y desencadenando cambios en Values y Profile sin tocar Identity.

### 4.3 Las cartas como fuente privilegiada

El campo `voz` en `Behavior.json` existe porque las cartas y la correspondencia personal son cualitativamente distintas de cualquier otra fuente: reflejan la voz directa del personaje en contextos no performativos, son la base para reproducir su registro comunicativo real, y contienen con frecuencia los momentos de mayor sinceridad. Esta distinción fundamenta la jerarquía de autoridad de fuentes del agente configurador, donde las cartas privadas ocupan el nivel más alto.

### 4.4 La instancia en memoria como mecanismo de evolución

El SYSTEM_PROMPT instruye al agente a mantener en memoria una copia de todos los ficheros (la instancia) que puede actualizar durante la sesión sin modificar los ficheros originales. Esto permite que el personaje evolucione de forma coherente a lo largo de una conversación larga, preservando a la vez la configuración base para poder reiniciar. Es el equivalente computacional de la distinción entre personalidad base y estado situacional.

### 4.5 El Bundle como exportación de solo lectura

El agente `character-bundler` genera un fichero autocontenido para usar el personaje en cualquier LLM externo. La decisión de hacerlo de solo lectura —sin comandos, sin referencias a ficheros externos— responde a un criterio de fidelidad: el SYSTEM_PROMPT que gobierna el comportamiento se conserva intacto en sus secciones de razonamiento y reglas, que son el núcleo funcional. Solo se eliminan los comandos que dependen de la infraestructura PerSSim y las referencias a ficheros que no existen en el contexto de exportación.

---

## Referencias principales

- Ashton, M.C. & Lee, K. (2004). A defence of the lexical approach to the study of personality structure. *European Journal of Personality*.
- Bratman, M. (1987). *Intention, Plans, and Practical Reason*. Harvard University Press.
- McAdams, D.P. (2008). The Life Story Interview. Northwestern University.
- Park, J.S. et al. (2023). Generative Agents: Interactive Simulacra of Human Behavior. *UIST '23*.
- Park, J.S. et al. (2024). Generative Agent Simulations of 1,000 People. *arXiv:2411.10109*.
- Paulhus, D.L. & Williams, K.M. (2002). The Dark Triad of personality. *Journal of Research in Personality*.
- Rao, A.S. & Georgeff, M.P. (1995). BDI Agents: From Theory to Practice. *ICMAS '95*.
- Schwartz, S.H. (1992). Universals in the content and structure of values. *Advances in Experimental Social Psychology*.
- Schwartz, S.H. et al. (2012). Refining the Theory of Basic Individual Values. *Journal of Personality and Social Psychology*.
- Shao, Y. et al. (2023). Character-LLM: A Trainable Agent for Role-Playing. *arXiv:2310.10158*.
- Sorokovikova, A. et al. (2024). LLMs Simulate Big Five Personality Traits. *arXiv*.