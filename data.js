// Este archivo lo actualiza apuntar.py (python apuntar.py).
// También puedes editarlo a mano, pero respeta el formato:
// DIAS en AAAA-MM-DD; por día y persona: 1 (acertó), 0 (no acertó) o -1 (penalizado por trampas).

const CONFIG = {
  "titulo": "GFT-Críptico",
  "subtitulo": "Una pista críptica cada día. Tu respuesta, en un post-it dentro del bol. Si aciertas, sumas un punto."
};

// Pista que se muestra en la página. Cámbiala con: python apuntar.py --pista "texto (4)"
const PISTA = {
  "fecha": "2026-11-20",
  "texto": "Calcio, hierro y mil gigabytes juntos preparan el despertar (8)"
};

// Un elemento por día de juego, en orden. Formato AAAA-MM-DD.
const DIAS = ["2026-11-13", "2026-11-16", "2026-11-17", "2026-11-18", "2026-11-19", "2026-11-20"];

// 1 = acertó, 0 = no acertó, -1 = penalizado por trampas. Mismo orden que DIAS.
const PUNTUACIONES = {
  "Claudia Simón (casb)": [0, 0, 0, 0, 0, 1],
};
