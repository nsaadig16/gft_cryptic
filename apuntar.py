#!/usr/bin/env python3
"""Actualiza data.js: aciertos del día y pista del día.

Uso (desde la carpeta de la página):
  python apuntar.py                          # modo interactivo: te pregunta quién acertó
  python apuntar.py Ana Luis                 # Ana y Luis acertaron hoy; el resto, 0
  python apuntar.py --nadie                  # hoy no acertó nadie
  python apuntar.py --pista "Texto de la pista (4)"   # cambia la pista que sale en la página
  python apuntar.py --penalizar Marta        # Marta resta 1 punto hoy por trampas (el día ya debe estar apuntado)
  python apuntar.py Ana --fecha 2026-11-20   # apunta otro día (también sirve para corregir)
  python apuntar.py Ana Luis --push          # además hace git add, commit y push

Si ya había datos de ese día, se sustituyen. Solo usa la librería estándar de Python 3.
"""

import argparse
import json
import re
import subprocess
import sys
import unicodedata
from datetime import date
from pathlib import Path

DATA = Path(__file__).with_name("data.js")
HEADER = """// Este archivo lo actualiza apuntar.py (python apuntar.py).
// También puedes editarlo a mano, pero respeta el formato:
// DIAS en AAAA-MM-DD; por día y persona: 1 (acertó), 0 (no acertó) o -1 (penalizado por trampas)."""


def norm(texto):
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return sin_tildes.casefold().strip()


def load():
    """Lee data.js. Devuelve (config, dias, tabla, pista)."""
    txt = DATA.read_text(encoding="utf-8")
    txt = re.sub(r"^\s*//.*$", "", txt, flags=re.M)  # quita comentarios
    txt = re.sub(r",(\s*[\]}])", r"\1", txt)  # quita comas finales
    txt = re.sub(
        r"^(\s*)([A-Za-z_]\w*)(\s*:)", r'\1"\2"\3', txt, flags=re.M
    )  # claves sin comillas
    dec = json.JSONDecoder()
    out = {}
    for name in ("CONFIG", "DIAS", "PUNTUACIONES", "PISTA"):
        m = re.search(rf"const {name}\s*=\s*", txt)
        if not m:
            if name == "PISTA":
                out[name] = {"fecha": "", "texto": ""}
                continue
            sys.exit(f"No encuentro «{name}» en data.js")
        out[name], _ = dec.raw_decode(txt, m.end())
    dias = out["DIAS"]
    tabla = {}
    for nombre, valores in out["PUNTUACIONES"].items():
        por_dia = {
            d: (int(v) if isinstance(v, (int, float)) else 0)
            for d, v in zip(dias, valores)
        }
        tabla[nombre] = {d: por_dia.get(d, 0) for d in dias}
    return out["CONFIG"], list(dias), tabla, out["PISTA"]


def save(config, dias, tabla, pista):
    dias = sorted(set(dias))
    filas = []
    for nombre, por_dia in tabla.items():
        valores = ", ".join(str(por_dia.get(d, 0)) for d in dias)
        filas.append(f"  {json.dumps(nombre, ensure_ascii=False)}: [{valores}]")
    partes = [
        HEADER,
        "",
        "const CONFIG = " + json.dumps(config, ensure_ascii=False, indent=2) + ";",
        "",
        '// Pista que se muestra en la página. Cámbiala con: python apuntar.py --pista "texto (4)"',
        "const PISTA = " + json.dumps(pista, ensure_ascii=False, indent=2) + ";",
        "",
        "// Un elemento por día de juego, en orden. Formato AAAA-MM-DD.",
        "const DIAS = " + json.dumps(dias) + ";",
        "",
        "// 1 = acertó, 0 = no acertó, -1 = penalizado por trampas. Mismo orden que DIAS.",
        "const PUNTUACIONES = {\n" + ",\n".join(filas) + "\n};",
        "",
    ]
    DATA.write_text("\n".join(partes), encoding="utf-8")


def resolver(token, tabla, dias):
    """Convierte lo que escribe la persona (número o nombre) en un nombre de la lista."""
    nombres = list(tabla)
    token = token.strip()
    if token.isdigit() and 1 <= int(token) <= len(nombres):
        return nombres[int(token) - 1]
    for n in nombres:
        if norm(n) == norm(token):
            return n
    empiezan = [n for n in nombres if norm(n).startswith(norm(token))]
    if len(empiezan) == 1:
        return empiezan[0]
    if len(empiezan) > 1:
        sys.exit(
            f"«{token}» puede ser: {', '.join(empiezan)}. Escribe el nombre completo."
        )
    try:
        r = input(
            f"«{token}» no está en la lista. ¿Añadirlo como jugador nuevo? [s/N] "
        )
    except EOFError:
        r = ""
    if r.strip().lower() not in ("s", "si", "sí", "y"):
        sys.exit("Cancelado.")
    tabla[token] = {d: 0 for d in dias}
    return token


def subir(hoy):
    cwd = DATA.parent
    try:
        subprocess.run(["git", "add", DATA.name], cwd=cwd, check=True)
        subprocess.run(
            ["git", "commit", "-m", f"Actualización {hoy}"], cwd=cwd, check=True
        )
        subprocess.run(["git", "push"], cwd=cwd, check=True)
        print("Subido a GitHub. La página se actualiza en un minuto.")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        sys.exit(f"data.js está guardado, pero falló git: {e}")


def main():
    ap = argparse.ArgumentParser(
        description="Actualiza aciertos, penalizaciones y pista en data.js"
    )
    ap.add_argument("nombres", nargs="*", help="quién acertó hoy")
    ap.add_argument("--fecha", help="día a apuntar (AAAA-MM-DD); por defecto, hoy")
    ap.add_argument("--nadie", action="store_true", help="hoy no acertó nadie")
    ap.add_argument(
        "--penalizar",
        nargs="+",
        metavar="NOMBRE",
        help="penaliza (-1) por trampas con IA; ponlo al final del comando",
    )
    ap.add_argument(
        "--pista",
        help="texto de la pista del día, con la enumeración al final, p. ej. «... (4)»",
    )
    ap.add_argument(
        "--push", action="store_true", help="hacer git add, commit y push al terminar"
    )
    args = ap.parse_args()

    hoy = args.fecha or date.today().isoformat()
    try:
        date.fromisoformat(hoy)
    except ValueError:
        sys.exit("La fecha debe tener formato AAAA-MM-DD, por ejemplo 2026-11-20.")

    config, dias, tabla, pista = load()

    def terminar(mensaje, sugerencia):
        print(mensaje)
        if args.push:
            subir(hoy)
        else:
            print(
                f'\nPara publicarlo: git add data.js && git commit -m "{sugerencia}" && git push'
            )

    if args.pista is not None:
        pista = {"fecha": hoy, "texto": args.pista.strip()}
        print(f"Pista del {hoy}: {pista['texto']}")
        if not (args.nombres or args.nadie or args.penalizar):
            save(config, dias, tabla, pista)  # solo pista, sin tocar aciertos
            terminar("Guardada la pista (los aciertos no se han tocado).", "Pista")
            return

    penalizados = {resolver(t, tabla, dias) for t in (args.penalizar or [])}

    if penalizados and not (args.nombres or args.nadie):
        # Solo penalización: el día ya tiene que estar apuntado
        if hoy not in dias:
            sys.exit(
                f"El {hoy} todavía no tiene aciertos apuntados. Apúntalos primero, o usa --fecha con un día ya apuntado."
            )
        for n in penalizados:
            tabla[n][hoy] = -1
        save(config, dias, tabla, pista)
        terminar(
            f"Penalizado el {hoy} (-1): {', '.join(sorted(penalizados))}.",
            "Penalización",
        )
        return

    interactivo = not (args.nombres or args.nadie)

    if interactivo:
        print(f"Jugadores ({hoy}):")
        for i, n in enumerate(tabla, 1):
            print(f"  {i}. {n}")
        try:
            raw = input(
                "¿Quién ha acertado? Números o nombres separados por comas (vacío = nadie): "
            )
            raw_pen = input("¿Alguien penalizado por trampas? (vacío = nadie): ")
        except EOFError:
            sys.exit("Cancelado.")
        tokens = [t for t in raw.split(",") if t.strip()]
        penalizados = {
            resolver(t, tabla, dias) for t in raw_pen.split(",") if t.strip()
        }
    else:
        tokens = args.nombres

    acertaron = {resolver(t, tabla, dias) for t in tokens}

    if interactivo:
        si = ", ".join(n for n in tabla if n in acertaron) or "nadie"
        pen = ", ".join(n for n in tabla if n in penalizados) or "nadie"
        r = input(
            f"Se apunta para {hoy}: acertaron {si}; penalizados: {pen}. ¿Guardar? [S/n] "
        )
        if r.strip().lower() in ("n", "no"):
            sys.exit("Cancelado, no se ha guardado nada.")

    if hoy in dias:
        print(f"Ya había datos del {hoy}: los sustituyo.")
    else:
        dias.append(hoy)
    for nombre, por_dia in tabla.items():
        if nombre in penalizados:
            por_dia[hoy] = -1  # la penalización anula el acierto
        else:
            por_dia[hoy] = 1 if nombre in acertaron else 0

    save(config, dias, tabla, pista)

    print(f"\nGuardado el {hoy}. Clasificación:")
    totales = sorted(
        ((sum(p.values()), n) for n, p in tabla.items()),
        key=lambda x: (-x[0], x[1].casefold()),
    )
    for total, nombre in totales:
        marca = "✗" if nombre in penalizados else ("✓" if nombre in acertaron else " ")
        print(f"  {marca} {nombre:<20} {total}")

    if args.push:
        subir(hoy)
    else:
        print(
            '\nPara publicarlo: git add data.js && git commit -m "Aciertos" && git push'
        )


if __name__ == "__main__":
    main()
