#!/usr/bin/env python3
"""Gera o banner, a stack e os botões de contato do README, nos temas claro e escuro.

Uso:
    python scripts/gerar_assets.py

Para mudar textos ou tecnologias, edite PERFIL e STACK abaixo e rode o script
de novo. Ele só usa a biblioteca padrão do Python (3.10 ou mais novo).
O painel de estatísticas é gerado à parte, por scripts/gerar_stats.py.
"""

from html import escape

from comum import (
    ICONES,
    LARGURA_IMAGEM,
    RAIZ,
    TEMAS,
    Tema,
    cor_legivel,
    gradiente_destaque,
    largura_texto,
    salvar,
    svg,
)

PERFIL = {
    "saudacao": "> olá, eu sou",
    "nome": "Gabriel Gonçalves",
    "cargo": "Desenvolvedor Full Stack Júnior",
    "resumo": "Python · JavaScript · C# · HTML/CSS",
    "usuario": "gabriel-goncalves",
    "arquivo": "status.txt",
    "conteudo": "aberto a oportunidades",
    "email": "ggoncalvesy03@gmail.com",
}

# Tecnologias da stack, por linha. Os nomes são chaves de icones.json.
STACK = [
    ("linguagens", ["python", "javascript", "csharp", "html5", "css"]),
    ("web & dados", ["react", "flask", "mysql"]),
    ("ferramentas", ["git", "github"]),
]

# Ajustes finos de alguns ícones de marca:
# - javascript: letras escuras por trás, como no logo original, sem mudar a cor;
# - mysql: mostra só o golfinho, com o traço engrossado (o ícone completo traz o
#   nome escrito, que fica ilegível em tamanho pequeno).
AJUSTES = {
    "javascript": {"fundo_icone": "#1f2328", "cor_original": True},
    "mysql": {
        "caixa": (14.0, 3.6, 10.0, 10.1),
        "recorte": "13.8,3.2 24.4,3.2 24.4,14 22.3,14 22.3,12.9 13.8,12.9",
        "traco": 0.35,
    },
}

ALTURA_BANNER = 320
ALTURA_BOTAO = 44
TERMINAL = TEMAS["dark"]  # o terminal do banner é escuro nos dois temas


# --------------------------------------------------------------------------
# Ícones
# --------------------------------------------------------------------------


def dados_icone(nome: str) -> dict:
    return ICONES["proprios"].get(nome) or ICONES["marcas"][nome]


def _desenho_icone(nome: str, dados: dict, ajuste: dict, cor: str) -> str:
    """Conteúdo do ícone no sistema de coordenadas 24x24 do Simple Icons."""
    if "svg" in dados:
        return dados["svg"].format(c=cor)
    if "caixa" not in ajuste:
        return f'<path d="{dados["path"]}" fill="{cor}"/>'
    # Amplia só a área "caixa" do ícone e esconde o resto com o polígono "recorte".
    x0, y0, w, h = ajuste["caixa"]
    s = 24 / max(w, h)
    tx, ty = -x0 * s + (24 - w * s) / 2, -y0 * s + (24 - h * s) / 2
    return (
        f'<clipPath id="recorte-{nome}"><polygon points="{ajuste["recorte"]}"/></clipPath>'
        f'<g transform="translate({tx:.3f} {ty:.3f}) scale({s:.4f})">'
        f'<path d="{dados["path"]}" fill="{cor}" stroke="{cor}" '
        f'stroke-width="{ajuste["traco"]}" stroke-linejoin="round" '
        f'clip-path="url(#recorte-{nome})"/></g>'
    )


def icone(nome: str, x: float, y: float, tamanho: float, t: Tema) -> str:
    """Desenha o ícone `nome` na posição (x, y), sobre o fundo dos chips do tema."""
    dados = dados_icone(nome)
    ajuste = AJUSTES.get(nome, {})
    cor = "#" + dados["hex"]
    if not ajuste.get("cor_original"):
        cor = cor_legivel(cor, t.superficie, t.texto)
    corpo = _desenho_icone(nome, dados, ajuste, cor)
    if "fundo_icone" in ajuste:
        fundo = ajuste["fundo_icone"]
        corpo = f'<rect x="1.5" y="1.5" width="21" height="21" fill="{fundo}"/>' + corpo
    return f'<g transform="translate({x:.1f} {y:.1f}) scale({tamanho / 24:.4f})">{corpo}</g>'


# --------------------------------------------------------------------------
# Banner
# --------------------------------------------------------------------------


def banner(t: Tema) -> str:
    w, h = LARGURA_IMAGEM, ALTURA_BANNER
    p = {chave: escape(valor) for chave, valor in PERFIL.items()}
    prompt = f'<tspan fill="{TERMINAL.destaque2}">$</tspan>'
    linhas = [
        "<defs>",
        '  <linearGradient id="fundo" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{t.fundo}"/>'
        f'<stop offset="1" stop-color="{t.fundo2}"/></linearGradient>',
        f"  {gradiente_destaque(t)}",
        *(
            f'  <radialGradient id="brilho{sufixo}">'
            f'<stop offset="0" stop-color="{cor}" stop-opacity="{t.brilho_opacidade}"/>'
            f'<stop offset="1" stop-color="{cor}" stop-opacity="0"/></radialGradient>'
            for sufixo, cor in (("A", t.destaque1), ("B", t.destaque2))
        ),
        '  <pattern id="pontos" width="26" height="26" patternUnits="userSpaceOnUse">'
        f'<circle cx="2" cy="2" r="1.3" fill="{t.pontos}" '
        f'fill-opacity="{t.pontos_opacidade}"/></pattern>',
        f'  <clipPath id="recorte"><rect width="{w}" height="{h}" rx="20"/></clipPath>',
        "</defs>",
        '<g clip-path="url(#recorte)">',
        f'  <rect width="{w}" height="{h}" fill="url(#fundo)"/>',
        f'  <rect width="{w}" height="{h}" fill="url(#pontos)"/>',
        '  <circle cx="160" cy="-30" r="330" fill="url(#brilhoA)"/>',
        '  <circle cx="1090" cy="370" r="360" fill="url(#brilhoB)"/>',
        f'  <rect y="{h - 5}" width="{w}" height="5" fill="url(#destaque)"/>',
        "</g>",
        f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="19.5" fill="none" '
        f'stroke="{t.borda}"/>',
        "",
        '<text x="74" y="104" class="mono" font-size="20" letter-spacing="1.5" '
        f'fill="{t.destaque1}">{p["saudacao"]}</text>',
        '<text x="70" y="172" class="sans" font-size="64" font-weight="700" '
        f'fill="{t.texto}">{p["nome"]}</text>',
        '<text x="73" y="220" class="sans" font-size="30" font-weight="600" '
        f'fill="url(#destaque)">{p["cargo"]}</text>',
        '<text x="74" y="262" class="sans" font-size="20" '
        f'fill="{t.secundario}">{p["resumo"]}</text>',
        "",
        '<g transform="translate(772 58)">',
        '  <rect width="364" height="204" rx="12" '
        f'fill="{t.terminal_fundo}" stroke="{t.terminal_borda}"/>',
        '  <circle cx="22" cy="21" r="6" fill="#ff5f57"/>'
        '<circle cx="42" cy="21" r="6" fill="#febc2e"/>'
        '<circle cx="62" cy="21" r="6" fill="#28c840"/>',
        '  <text x="182" y="26" text-anchor="middle" class="mono" font-size="14" '
        f'fill="{TERMINAL.secundario}">~/gabriel</text>',
        f'  <line x1="0" y1="42" x2="364" y2="42" stroke="{TERMINAL.borda}"/>',
        '  <g class="mono" font-size="17">',
        f'    <text x="22" y="76" fill="{TERMINAL.texto}">{prompt} whoami</text>',
        f'    <text x="22" y="102" fill="{TERMINAL.secundario}">{p["usuario"]}</text>',
        f'    <text x="22" y="134" fill="{TERMINAL.texto}">{prompt} cat {p["arquivo"]}</text>',
        f'    <text x="22" y="160" fill="{TERMINAL.destaque1}">{p["conteudo"]}</text>',
        f'    <text x="22" y="190" fill="{TERMINAL.texto}">{prompt}</text>',
        f'    <rect class="cursor" x="40" y="176" width="10" height="18" fill="{TERMINAL.texto}"/>',
        "  </g>",
        "</g>",
    ]
    estilo = (
        "@keyframes piscar{50%{opacity:0}}.cursor{animation:piscar 1.1s step-end infinite}"
        "@media (prefers-reduced-motion:reduce){.cursor{animation:none}}"
    )
    return svg(w, h, f"{PERFIL['nome']} — {PERFIL['cargo']}", "\n".join(linhas), estilo)


# --------------------------------------------------------------------------
# Stack
# --------------------------------------------------------------------------

X_CHIPS, ALTURA_CHIP, ESPACO, ALTURA_LINHA, MARGEM = 236, 52, 12, 70, 30


def _distribuir_chips(itens: list[str]) -> list[list[tuple[str, str, float, float]]]:
    """Distribui os chips de uma linha da stack, quebrando quando não cabem na largura."""
    linhas, linha, x = [], [], X_CHIPS
    for nome in itens:
        texto = dados_icone(nome)["title"]
        w = 54 + largura_texto(texto, 18, negrito=True) + 20
        if x + w > LARGURA_IMAGEM - 32 and linha:
            linhas.append(linha)
            linha, x = [], X_CHIPS
        linha.append((nome, texto, x, w))
        x += w + ESPACO
    linhas.append(linha)
    return linhas


def stack(t: Tema) -> str:
    partes, y = [], MARGEM
    for rotulo, itens in STACK:
        linhas = _distribuir_chips(itens)
        partes.append(
            f'<text x="40" y="{y + ALTURA_CHIP / 2 + 6:.0f}" class="mono" font-size="17" '
            f'fill="{t.secundario}">{escape(rotulo)}</text>'
        )
        for i, linha in enumerate(linhas):
            yy = y + i * (ALTURA_CHIP + ESPACO)
            for nome, texto, x, w in linha:
                partes.append(
                    f'<rect x="{x:.1f}" y="{yy}" width="{w:.1f}" height="{ALTURA_CHIP}" rx="12" '
                    f'fill="{t.superficie}" stroke="{t.borda}"/>'
                    + icone(nome, x + 17, yy + 14, 24, t)
                    + f'<text x="{x + 54:.1f}" y="{yy + 32}" class="sans" font-size="18" '
                    f'font-weight="600" fill="{t.texto}">{escape(texto)}</text>'
                )
        y += len(linhas) * (ALTURA_CHIP + ESPACO) - ESPACO + (ALTURA_LINHA - ALTURA_CHIP)
    w, h = LARGURA_IMAGEM, y - (ALTURA_LINHA - ALTURA_CHIP) + MARGEM
    fundo = (
        f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="16" '
        f'fill="{t.fundo}" stroke="{t.borda}"/>'
        f'<line x1="206" y1="24" x2="206" y2="{h - 24}" stroke="{t.borda}" '
        'stroke-dasharray="4 6"/>'
    )
    nomes = ", ".join(dados_icone(n)["title"] for _, itens in STACK for n in itens)
    return svg(w, h, f"Tecnologias: {nomes}", fundo + "\n" + "\n".join(partes))


# --------------------------------------------------------------------------
# Botões de contato
# --------------------------------------------------------------------------


def badge(t: Tema, nome_icone: str, texto: str) -> str:
    w, h = 52 + largura_texto(texto, 16, negrito=True) + 20, ALTURA_BOTAO
    corpo = (
        f'<rect x="0.5" y="0.5" width="{w - 1:.1f}" height="{h - 1}" rx="22" '
        f'fill="{t.superficie}" stroke="{t.borda}"/>'
        + icone(nome_icone, 18, 11, 22, t)
        + '<text x="50" y="28" class="sans" font-size="16" font-weight="600" '
        f'fill="{t.texto}">{escape(texto)}</text>'
    )
    return svg(round(w), h, texto, corpo)


# --------------------------------------------------------------------------


def main() -> None:
    for nome_tema, tema in TEMAS.items():
        imagens = {
            "banner": banner(tema),
            "stack": stack(tema),
            "badge-email": badge(tema, "email", PERFIL["email"]),
            "badge-linkedin": badge(tema, "linkedin", "LinkedIn"),
        }
        for nome, conteudo in imagens.items():
            print(salvar(nome, nome_tema, conteudo).relative_to(RAIZ))


if __name__ == "__main__":
    main()
