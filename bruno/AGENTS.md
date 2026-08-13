# AGENTS.md

## Proyecto

Este directorio contiene juegos educativos HTML para Bruno, un niño de 4° grado de
Mendoza, Argentina. Cada juego es una app autocontenida que refuerza un tema del
manual escolar (Santillana · Mendoza).

Páginas:

- `index.html`: índice de juegos, con una tarjeta por juego.
- `aventura-matematica.html`: retos de matemática por una ruta de explorador.
- `galaxia-de-tablas.html`: tablas de multiplicar con temática espacial.
- `expedicion-naturaleza.html`: Ciencias Naturales (seres vivos, ambientes, Mendoza).
- `aventura-de-palabras.html`: Lengua (poesía, artículos, adjetivos, preposiciones).
- `viaje-al-nuevo-mundo.html`: Ciencias Sociales (exploración, conquista, fundación de ciudades).

## Tarea habitual

Lo normal acá es **agregar un juego nuevo a partir de fotos del manual**. El usuario
suele dejar imágenes de las páginas del libro en un directorio temporal (por ejemplo
`/tmp/bruno/`) y pedir un juego sobre ese tema.

El flujo es:

1. Leer las imágenes y extraer el contenido: definiciones, fechas, nombres, listas y
   los ejercicios del libro (esos ejercicios son la mejor guía de qué evaluar).
2. Copiar la estructura de un juego existente (`expedicion-naturaleza.html` es la
   referencia más completa) y adaptar tema, paleta y textos.
3. Agregar la tarjeta correspondiente en `index.html`, incluyendo las reglas CSS
   `.card.<clase>::after` y `.<clase> .go` con el color del juego nuevo.

## Convenciones de los juegos

- **Un solo archivo por juego**: HTML, CSS y JS embebidos. Sin frameworks, sin
  bundlers, sin dependencias externas (la única excepción es el `@import` de Google
  Fonts: `Fredoka`, `Baloo 2` y a veces `Caveat`).
- **Preguntas siempre distintas**: nunca una lista fija de preguntas. Cada tema tiene
  una función generadora (`genLoQueSea()`) que elige al azar el modo de pregunta, el
  protagonista y los distractores, usando los helpers `rnd`, `pick`, `shuffle`,
  `sample` y `others`. El array `POOL` repite cada generador según el peso que se le
  quiera dar, y `nextExercise()` evita repetir la misma consigna seguida.
- **Cada ejercicio devuelve un objeto** con: `topic`, `tag`, `prompt`, `hint`,
  `choices` (cada una `{label, ok, em}`), `explain` y opcionalmente `scenario` y
  `type` (`'tf'` para verdadero/falso, `'order'` para ordenar).
- **Siempre una sola opción correcta** y sin etiquetas repetidas entre las opciones.
- **`explain` es obligatorio**: el chico tiene que aprender algo aunque falle.
- **Mecánica común**: 3 vidas ❤️, racha 🔥 con bonus de puntos, confeti al acertar,
  barra de progreso con un personaje que avanza, e insignias por tema en la pantalla
  final con estrellas según la precisión.
- **UI divertida y para chicos**: bordes gruesos, sombras duras tipo "sticker",
  emojis grandes, animaciones suaves, botones grandes y táctiles. Debe funcionar bien
  en celular (probar con ancho angosto).
- **Contenido fiel al manual y en español rioplatense** (voseo: "Ordená", "Fijate",
  "Tenés"). No inventar datos que no estén en el libro.
- Incluir el enlace `⬅ Volver a los juegos` hacia `index.html`.

## Verificación

No hay build ni tests. Para validar un juego nuevo, extraer el `<script>` y ejercitar
los generadores con Node, comprobando que no haya preguntas rotas:

```bash
node -e "
  // stub mínimo de document, luego eval del script del juego
  // y correr nextExercise() miles de veces verificando:
  //  - exactamente una opción con ok:true
  //  - sin labels duplicados
  //  - explain no vacío
"
```

Interesa además contar cuántas variantes únicas de consigna produce: si son pocas,
faltan modos de pregunta.

Revisar también que los enlaces del índice existan:

```bash
grep -n "href=" index.html
```

## Git

- Commits pequeños y descriptivos.
- No tocar archivos fuera de `bruno/` salvo pedido explícito.
- No incluir archivos temporales ni las imágenes fuente del manual.
