"""Tema visual e utilitários usados pelos scripts que geram as imagens do README."""

import json
import pathlib
from dataclasses import dataclass
from html import escape

RAIZ = pathlib.Path(__file__).resolve().parent.parent
ASSETS = RAIZ / "assets"
ICONES = json.loads((RAIZ / "scripts" / "icones.json").read_text(encoding="utf-8"))

LARGURA_IMAGEM = 1200  # em pixels; o GitHub reduz as imagens para caber na página


@dataclass(frozen=True)
class Tema:
    """Cores de um tema do GitHub (claro ou escuro)."""

    fundo: str
    fundo2: str  # segunda cor do degradê do banner
    superficie: str  # fundo dos chips e cartões
    borda: str
    texto: str
    secundario: str  # textos de apoio
    destaque1: str  # violeta
    destaque2: str  # ciano
    pontos: str  # pontinhos do fundo do banner
    pontos_opacidade: float
    brilho_opacidade: float
    terminal_fundo: str
    terminal_borda: str


TEMAS = {
    "dark": Tema(
        fundo="#0d1117",
        fundo2="#12162b",
        superficie="#161b22",
        borda="#30363d",
        texto="#e6edf3",
        secundario="#8b949e",
        destaque1="#a78bfa",
        destaque2="#22d3ee",
        pontos="#ffffff",
        pontos_opacidade=0.06,
        brilho_opacidade=0.30,
        terminal_fundo="#161b22",
        terminal_borda="#30363d",
    ),
    "light": Tema(
        fundo="#ffffff",
        fundo2="#f4f1ff",
        superficie="#f6f8fa",
        borda="#d0d7de",
        texto="#1f2328",
        secundario="#59636e",
        destaque1="#7c3aed",
        destaque2="#0891b2",
        pontos="#1f2328",
        pontos_opacidade=0.07,
        brilho_opacidade=0.16,
        terminal_fundo="#161b22",
        terminal_borda="#161b22",
    ),
}

SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"

# Larguras aproximadas dos caracteres na fonte Arial, em milésimos do tamanho da fonte.
_LARGURAS = dict(
    zip(
        "abcdefghijklmnopqrstuvwxyz",
        [556, 556, 500, 556, 556, 278, 556, 556, 222, 222, 500, 222, 833,
         556, 556, 556, 556, 333, 500, 278, 556, 500, 722, 500, 500, 500],
        strict=True,
    )
)  # fmt: skip
_LARGURAS.update(
    zip(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        [667, 667, 722, 722, 667, 611, 778, 722, 278, 500, 667, 556, 833,
         722, 778, 667, 778, 722, 667, 611, 722, 667, 944, 667, 667, 611],
        strict=True,
    )
)  # fmt: skip
_LARGURAS.update(dict.fromkeys("0123456789", 556))
_LARGURAS.update({" ": 278, ".": 278, ",": 278, "-": 333, "·": 278, "/": 278, ":": 278,
                  "&": 667, "@": 1015, "#": 556, "(": 333, ")": 333, "%": 889})  # fmt: skip
_SEM_ACENTO = str.maketrans("áàâãäéêèíîóôõöúüçÁÀÂÃÉÊÍÓÔÕÚÇ", "aaaaaeeeiioooouucAAAAEEIOOOUC")


def largura_texto(texto: str, tamanho: float, negrito: bool = False) -> float:
    """Estima a largura de um texto em pixels, para dimensionar o que fica ao redor dele."""
    total = sum(_LARGURAS.get(c, 556) for c in texto.translate(_SEM_ACENTO))
    return total / 1000 * tamanho * (1.07 if negrito else 1.0)


def _rgb(cor: str) -> list[int]:
    cor = cor.lstrip("#")
    return [int(cor[i : i + 2], 16) for i in (0, 2, 4)]


def _luminancia(cor: str) -> float:
    def canal(valor: int) -> float:
        v = valor / 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4

    r, g, b = (canal(v) for v in _rgb(cor))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contraste(cor1: str, cor2: str) -> float:
    """Razão de contraste entre duas cores, como definida pela WCAG (de 1 a 21)."""
    clara, escura = sorted((_luminancia(cor1), _luminancia(cor2)), reverse=True)
    return (clara + 0.05) / (escura + 0.05)


def cor_legivel(cor: str, fundo: str, texto: str, minimo: float = 2.2) -> str:
    """Ajusta uma cor de marca para ela aparecer bem sobre o fundo do tema."""
    if contraste(cor, fundo) >= minimo:
        return cor
    if max(_rgb(cor)) - min(_rgb(cor)) < 40:  # cor neutra (preta ou branca): usa a cor do texto
        return texto
    for passo in range(1, 11):  # cor viva: aproxima da cor do texto até ficar legível
        t = passo / 10
        canais = zip(_rgb(cor), _rgb(texto), strict=True)
        mistura = "#" + "".join(f"{round(a + (b - a) * t):02x}" for a, b in canais)
        if contraste(mistura, fundo) >= minimo:
            return mistura
    return texto


def gradiente_destaque(t: Tema) -> str:
    """Degradê violeta → ciano usado nos títulos e números de destaque."""
    return (
        '<linearGradient id="destaque" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{t.destaque1}"/>'
        f'<stop offset="1" stop-color="{t.destaque2}"/></linearGradient>'
    )


def svg(largura: int, altura: int, titulo: str, corpo: str, estilo: str = "") -> str:
    """Monta um documento SVG completo, com título acessível para leitores de tela."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{largura}" height="{altura}" '
        f'viewBox="0 0 {largura} {altura}" role="img" aria-labelledby="titulo">\n'
        f'<title id="titulo">{escape(titulo)}</title>\n'
        f"<style>.sans{{font-family:{SANS}}}.mono{{font-family:{MONO}}}{estilo}</style>\n"
        f"{corpo}\n</svg>\n"
    )


def salvar(nome: str, nome_tema: str, conteudo: str) -> pathlib.Path:
    """Grava assets/<nome>-<tema>.svg e devolve o caminho do arquivo."""
    ASSETS.mkdir(exist_ok=True)
    caminho = ASSETS / f"{nome}-{nome_tema}.svg"
    caminho.write_text(conteudo, encoding="utf-8")
    return caminho
