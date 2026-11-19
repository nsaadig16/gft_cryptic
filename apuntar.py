#!/usr/bin/env python3
"""Apunta los aciertos del día en data.js.

Uso (desde la carpeta de la página):
  python apuntar.py                    # modo interactivo: te pregunta quién acertó
  python apuntar.py Ana Luis           # Ana y Luis acertaron hoy; el resto, 0
  python apuntar.py --nadie            # hoy no acertó nadie
  python apuntar.py Ana --fecha 2026-11-20   # apunta otro día (también sirve para corregir)
  python apuntar.py Ana Luis --push    # además hace git add, commit y push

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
// DIAS en AAAA-MM-DD, y un 1 (acertó) o un 0 (no acertó) por día y persona."""


def norm(texto):
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return sin_tildes.casefold().strip()


def load():
    """Lee CONFIG, DIAS y PUNTUACIONES de data.js. Devuelve (config, dias, tabla)."""
    txt = DATA.read_text(encoding="utf-8")
    txt = re.sub(r"^\s*//.*$", "", txt, flags=re.M)      # quita comentarios
    txt = re.sub(r",(\s*[\]}])", r"\1", txt)             # quita comas finales
    txt = re.sub(r"^(\s*)([A-Za-z_]\w*)(\s*:)", r'\1"\2"\3', txt, flags=re.M)  # claves sin comillas
    dec = json.JSONDecoder()
    out = {}
    for name in ("CONFIG", "DIAS", "PUNTUACIONES"):
        m = re.search(rf"const {name}\s*=\s*", txt)
        if not m:
            sys.exit(f"No encuentro «{name}» en data.js")
        out[name], _ = dec.raw_decode(txt, m.end())
    dias = out["DIAS"]
    tabla = {}
    for nombre, valores in out["PUNTUACIONES"].items():
        por_dia = {d: (1 if v else 0) for d, v in zip(dias, valores)}
        tabla[nombre] = {d: por_dia.get(d, 0) for d in dias}
    return out["CONFIG"], list(dias), tabla


def save(config, dias, tabla):
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
        "// Un elemento por día de juego, en orden. Formato AAAA-MM-DD.",
        "const DIAS = " + json.dumps(dias) + ";",
        "",
        "// 1 = acertó ese día, 0 = no acertó. Mismo orden que DIAS.",
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
        sys.exit(f"«{token}» puede ser: {', '.join(empiezan)}. Escribe el nombre completo.")
    try:
        r = input(f"«{token}» no está en la lista. ¿Añadirlo como jugador nuevo? [s/N] ")
    except EOFError:
        r = ""
    if r.strip().lower() not in ("s", "si", "sí", "y"):
        sys.exit("Cancelado.")
    tabla[token] = {d: 0 for d in dias}
    return token


def main():
    ap = argparse.ArgumentParser(description="Apunta los aciertos del día en data.js")
    ap.add_argument("nombres", nargs="*", help="quién acertó hoy")
    ap.add_argument("--fecha", help="día a apuntar (AAAA-MM-DD); por defecto, hoy")
    ap.add_argument("--nadie", action="store_true", help="hoy no acertó nadie")
    ap.add_argument("--push", action="store_true", help="hacer git add, commit y push al terminar")
    args = ap.parse_args()

    hoy = args.fecha or date.today().isoformat()
    try:
        date.fromisoformat(hoy)
    except ValueError:
        sys.exit("La fecha debe tener formato AAAA-MM-DD, por ejemplo 2026-11-20.")

    config, dias, tabla = load()
    interactivo = not (args.nombres or args.nadie)

    if interactivo:
        print(f"Jugadores ({hoy}):")
        for i, n in enumerate(tabla, 1):
            print(f"  {i}. {n}")
        try:
            raw = input("¿Quién ha acertado? Números o nombres separados por comas (vacío = nadie): ")
        except EOFError:
            sys.exit("Cancelado.")
        tokens = [t for t in raw.split(",") if t.strip()]
    else:
        tokens = args.nombres

    acertaron = {resolver(t, tabla, dias) for t in tokens}

    if interactivo:
        si = ", ".join(n for n in tabla if n in acertaron) or "nadie"
        r = input(f"Se apunta para {hoy}: acertaron {si}. ¿Guardar? [S/n] ")
        if r.strip().lower() in ("n", "no"):
            sys.exit("Cancelado, no se ha guardado nada.")

    if hoy in dias:
        print(f"Ya había datos del {hoy}: los sustituyo.")
    else:
        dias.append(hoy)
    for nombre, por_dia in tabla.items():
        por_dia[hoy] = 1 if nombre in acertaron else 0

    save(config, dias, tabla)

    print(f"\nGuardado el {hoy}. Clasificación:")
    totales = sorted(((sum(p.values()), n) for n, p in tabla.items()), key=lambda x: (-x[0], x[1].casefold()))
    for total, nombre in totales:
        marca = "✓" if nombre in acertaron else " "
        print(f"  {marca} {nombre:<20} {total}")

    if args.push:
        cwd = DATA.parent
        try:
            subprocess.run(["git", "add", DATA.name], cwd=cwd, check=True)
            subprocess.run(["git", "commit", "-m", f"Aciertos {hoy}"], cwd=cwd, check=True)
            subprocess.run(["git", "push"], cwd=cwd, check=True)
            print("Subido a GitHub. La página se actualiza en un minuto.")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            sys.exit(f"data.js está guardado, pero falló git: {e}")
    else:
        print("\nPara publicarlo: git add data.js && git commit -m \"Aciertos\" && git push")


if __name__ == "__main__":
    main()