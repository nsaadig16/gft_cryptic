# GFT-Críptico

Página estática para el juego diario de la oficina: cada día hay una pista críptica, cada persona responde en un post-it que echa en el bol, y quien acierta suma 1 punto. La página muestra la clasificación y las reglas del mini críptico.

Se despliega en GitHub Pages. No hay servidor ni dependencias: solo HTML, un archivo de datos y un script de Python.

## Archivos

| Archivo | Para qué sirve |
|---|---|
| `index.html` | La página (diseño, reglas y lógica de la clasificación). Casi nunca hay que tocarla. |
| `data.js` | Los datos: título, días de juego y aciertos de cada persona. Lo actualiza `apuntar.py`. |
| `apuntar.py` | Script que apunta los aciertos del día en `data.js`. |

## Uso diario

Un día de juego, desde la carpeta del proyecto:

```
python apuntar.py Ana Luis --push
```

Ana y Luis suman 1 punto, el resto 0. Con `--push`, el script guarda los datos, hace `git commit` y `git push`; la página se actualiza en uno o dos minutos.

Necesita Python 3 y nada más. Antes de apuntar, si hay más gente con acceso al repo, haz `git pull` para no pisar sus cambios.

### Opciones

| Comando | Qué hace |
|---|---|
| `python apuntar.py` | Modo interactivo: muestra los jugadores numerados y pregunta quién ha acertado (números o nombres separados por comas; vacío = nadie). Pide confirmación antes de guardar. |
| `python apuntar.py Ana Luis` | Apunta de forma directa quién ha acertado hoy. |
| `python apuntar.py --nadie` | Hoy no ha acertado nadie. |
| `python apuntar.py Ana --fecha 2026-11-20` | Apunta otro día (formato `AAAA-MM-DD`). |
| `--push` (con cualquiera de los anteriores) | Además hace `git add`, `commit` y `push`. |

Detalles:

- Los nombres no distinguen mayúsculas ni tildes, y basta con el principio si no hay ambigüedad (`lu` vale para Luis).
- Si escribes un nombre que no está en la lista, el script pregunta si quieres añadirlo como jugador nuevo, con 0 en los días anteriores.
- **Corregir un error:** vuelve a lanzar el comando para ese día (con `--fecha` si ya no es hoy). Los datos de ese día se sustituyen.
- Solo hay que correrlo los días de juego. Los fines de semana y festivos no se apunta nada.

## Editar a mano

`data.js` también se puede editar a mano (por ejemplo, desde la web de GitHub con el icono del lápiz). Respeta el formato:

```js
const DIAS = ["2026-11-18", "2026-11-19"];   // fechas AAAA-MM-DD, en orden

const PUNTUACIONES = {
  "Ana": [0, 1],   // un 1 (acertó) o un 0 (no acertó) por cada día de DIAS
  "Luis": [1, 1]
};
```

Para cambiar el título o el subtítulo, edita `CONFIG` en `data.js`. Las reglas del mini críptico están en `index.html` como HTML normal, en la sección marcada con un comentario.

## Qué muestra la página

- Clasificación ordenada por puntos (los empates comparten puesto, y se desempata por orden alfabético en la lista).
- Para cada persona, los últimos 5 días de juego con ✓ o –, y debajo el día de la semana.
- La fecha de la última actualización, tomada del último día de `DIAS`.
- Las reglas del mini críptico, con un enlace a [minicriptico.com/guia](https://minicriptico.com/guia).

## Despliegue en GitHub Pages

1. Sube `index.html`, `data.js`, `apuntar.py` y este `README.md` a la raíz de un repositorio.
2. En el repo, ve a *Settings → Pages*.
3. En *Source* elige *Deploy from a branch*, selecciona `main` y `/ (root)`, y guarda.
4. En uno o dos minutos la página estará en `https://<usuario>.github.io/<repo>/`.

## Probarlo en local

Abre `index.html` directamente en el navegador; no hace falta servidor. Necesita conexión a internet solo para cargar las tipografías de Google Fonts (si no hay, usa tipografías del sistema).

## Problemas habituales

- **La página no se actualiza:** comprueba que hiciste `push` (usa `--push`) y espera un minuto o dos. Si sigue igual, fuerza la recarga con Ctrl+F5.
- **El script dice que no encuentra `CONFIG`, `DIAS` o `PUNTUACIONES`:** `data.js` se ha editado a mano y ha perdido el formato. Comprueba que siguen existiendo esas tres líneas `const ...`.
- **Falla el `git push`:** los datos ya están guardados en `data.js`; haz `git pull` y vuelve a hacer `git push` a mano.
