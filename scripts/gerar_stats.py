#!/usr/bin/env python3
"""Gera o painel de estatísticas do GitHub (assets/stats-dark.svg e assets/stats-light.svg).

Ele roda sozinho todo dia pelo GitHub Actions (.github/workflows/estatisticas.yml),
com o token automático do repositório. Para rodar no seu computador, crie um
token em https://github.com/settings/tokens (não precisa marcar nenhuma
permissão) e execute:

    GITHUB_TOKEN=seu_token python scripts/gerar_stats.py
"""

import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from html import escape

from comum import (
    ICONES,
    LARGURA_IMAGEM,
    RAIZ,
    TEMAS,
    Tema,
    gradiente_destaque,
    largura_texto,
    salvar,
    svg,
)

USUARIO = os.environ.get("GITHUB_USER", "ggoncalves0")
MAX_LINGUAGENS = 6
IGNORAR_LINGUAGENS: set[str] = set()  # ex.: {"HTML", "CSS"} para tirar linguagens do painel

API_GRAPHQL = "https://api.github.com/graphql"
# Busca até 100 repositórios públicos, o que basta para um perfil pessoal.
CONSULTA = """
query($login: String!) {
  user(login: $login) {
    repositories(ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC, first: 100) {
      nodes {
        name
        languages(first: 20, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
    contributionsCollection {
      totalCommitContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""

ALTURA_PAINEL = 314
X_LINGUAGENS, LARGURA_BARRA, Y_BARRA = 650, 510, 74
LARGURA_CARTAO, ALTURA_CARTAO = 262, 96
FRACAO_MINIMA = 0.0005  # abaixo disso, o resto das linguagens não aparece na barra


@dataclass(frozen=True)
class Linguagem:
    nome: str
    cor: str
    fracao: float  # parte do total de bytes de código, de 0 a 1


@dataclass(frozen=True)
class Resumo:
    contribuicoes: int
    commits: int
    dias_ativos: int
    maior_sequencia: int
    repositorios: int
    linguagens: tuple[Linguagem, ...]


# --------------------------------------------------------------------------
# Dados
# --------------------------------------------------------------------------


def buscar(usuario: str, token: str) -> dict:
    """Consulta a API GraphQL do GitHub e devolve os dados do usuário."""
    corpo = json.dumps({"query": CONSULTA, "variables": {"login": usuario}}).encode()
    pedido = urllib.request.Request(
        API_GRAPHQL,
        data=corpo,
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": f"{usuario}-readme-stats",
        },
    )
    with urllib.request.urlopen(pedido, timeout=30) as resposta:
        dados = json.load(resposta)
    if dados.get("errors") or not (dados.get("data") or {}).get("user"):
        raise RuntimeError(f"a API do GitHub respondeu com erro: {dados.get('errors')}")
    return dados["data"]["user"]


def _atividade(calendario: dict) -> tuple[int, int]:
    """Conta os dias com contribuição e a maior sequência de dias seguidos."""
    dias = sorted(
        (dia["date"], dia["contributionCount"])
        for semana in calendario["weeks"]
        for dia in semana["contributionDays"]
    )
    ativos = sequencia = maior = 0
    for _, quantidade in dias:
        if quantidade > 0:
            ativos += 1
            sequencia += 1
            maior = max(maior, sequencia)
        else:
            sequencia = 0
    return ativos, maior


def _linguagens(repos: list[dict]) -> tuple[Linguagem, ...]:
    """Soma os bytes de cada linguagem e devolve as mais usadas, da maior para a menor."""
    bytes_por_linguagem: dict[str, int] = {}
    cores: dict[str, str] = {}
    for repo in repos:
        for aresta in repo["languages"]["edges"]:
            nome = aresta["node"]["name"]
            if nome in IGNORAR_LINGUAGENS:
                continue
            bytes_por_linguagem[nome] = bytes_por_linguagem.get(nome, 0) + aresta["size"]
            cores[nome] = aresta["node"]["color"] or "#8b949e"
    total = sum(bytes_por_linguagem.values())
    if not total:
        return ()
    ranking = sorted(bytes_por_linguagem.items(), key=lambda item: item[1], reverse=True)
    return tuple(
        Linguagem(nome, cores[nome], tamanho / total) for nome, tamanho in ranking[:MAX_LINGUAGENS]
    )


def resumir(usuario_dados: dict, login: str) -> Resumo:
    """Transforma a resposta da API nos números que aparecem no painel."""
    contribuicoes = usuario_dados["contributionsCollection"]
    calendario = contribuicoes["contributionCalendar"]
    ativos, maior = _atividade(calendario)
    # O repositório do perfil (o que tem o seu nome de usuário) fica de fora:
    # ele só guarda o README e os scripts que geram estas imagens.
    repos = [
        repo
        for repo in usuario_dados["repositories"]["nodes"]
        if repo["name"].lower() != login.lower()
    ]
    return Resumo(
        contribuicoes=calendario["totalContributions"],
        commits=contribuicoes["totalCommitContributions"],
        dias_ativos=ativos,
        maior_sequencia=maior,
        repositorios=len(repos),
        linguagens=_linguagens(repos),
    )


# --------------------------------------------------------------------------
# Desenho
# --------------------------------------------------------------------------


def _numero(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def _porcentagem(fracao: float) -> str:
    return f"{fracao * 100:.1f}".replace(".", ",") + "%"


def _plural(n: int, singular: str, plural: str) -> str:
    return singular if n == 1 else plural


def _encurtar(texto: str, tamanho: float, maximo: float) -> str:
    """Corta o texto com reticências se ele passar da largura máxima."""
    if largura_texto(texto, tamanho, negrito=True) <= maximo:
        return texto
    while texto and largura_texto(texto + "…", tamanho, negrito=True) > maximo:
        texto = texto[:-1]
    return texto.rstrip() + "…"


def _cartoes_atividade(t: Tema, r: Resumo) -> list[str]:
    """Os quatro cartões de atividade, em uma grade 2x2."""
    seq = r.maior_sequencia
    metricas = [
        ("pulse", r.contribuicoes, "", "contribuições"),
        ("git-commit", r.commits, "", "commits"),
        ("calendar", r.dias_ativos, "", "dias com atividade"),
        ("flame", seq, _plural(seq, " dia", " dias"), "maior sequência"),
    ]
    cartoes = []
    for i, (nome_icone, valor, unidade, rotulo) in enumerate(metricas):
        x = 40 + (i % 2) * (LARGURA_CARTAO + 16)
        y = 74 + (i // 2) * (ALTURA_CARTAO + 16)
        sufixo = ""
        if unidade:
            sufixo = (
                f'<tspan font-size="18" font-weight="600" fill="{t.secundario}">{unidade}</tspan>'
            )
        cartoes.append(
            f'<rect x="{x}" y="{y}" width="{LARGURA_CARTAO}" height="{ALTURA_CARTAO}" rx="12" '
            f'fill="{t.superficie}" stroke="{t.borda}"/>'
            f'<path transform="translate({x + LARGURA_CARTAO - 42} {y + 20}) scale(1.25)" '
            f'd="{ICONES["octicons"][nome_icone]}" fill="{t.destaque1}"/>'
            f'<text x="{x + 22}" y="{y + 54}" class="sans" font-size="40" font-weight="700" '
            f'fill="url(#destaque)">{_numero(valor)}{sufixo}</text>'
            f'<text x="{x + 22}" y="{y + 80}" class="sans" font-size="16" '
            f'fill="{t.secundario}">{escape(rotulo)}</text>'
        )
    return cartoes


def _barra_linguagens(t: Tema, linguagens: tuple[Linguagem, ...]) -> str:
    """Barra empilhada com a parte de cada linguagem, separadas por um fio."""
    resto = 1 - sum(ling.fracao for ling in linguagens)
    segmentos = [(ling.cor, ling.fracao) for ling in linguagens]
    if resto > FRACAO_MINIMA:
        segmentos.append((t.borda, resto))
    barra, x = [], X_LINGUAGENS
    for i, (cor, fracao) in enumerate(segmentos):
        w = LARGURA_BARRA * fracao
        barra.append(f'<rect x="{x:.2f}" y="{Y_BARRA}" width="{w:.2f}" height="14" fill="{cor}"/>')
        x += w
        if i < len(segmentos) - 1:
            barra.append(
                f'<rect x="{x - 1:.2f}" y="{Y_BARRA}" width="2" height="14" fill="{t.fundo}"/>'
            )
    return f'<g clip-path="url(#barra)">{"".join(barra)}</g>'


def _legenda_linguagens(t: Tema, linguagens: tuple[Linguagem, ...]) -> list[str]:
    """Legenda em duas colunas de três linhas: bolinha, nome e porcentagem."""
    itens = []
    for i, ling in enumerate(linguagens):
        coluna, linha = divmod(i, 3)
        x, y = X_LINGUAGENS + coluna * 265, 134 + linha * 44
        itens.append(
            f'<circle cx="{x + 7}" cy="{y - 6}" r="7" fill="{ling.cor}" '
            f'stroke="{t.texto}" stroke-opacity="0.15"/>'
            f'<text x="{x + 24}" y="{y}" class="sans" font-size="18" font-weight="600" '
            f'fill="{t.texto}">{escape(_encurtar(ling.nome, 18, 150))}</text>'
            f'<text x="{x + 245}" y="{y}" text-anchor="end" class="mono" font-size="16" '
            f'fill="{t.secundario}">{_porcentagem(ling.fracao)}</text>'
        )
    return itens


def _titulo(r: Resumo) -> str:
    """Descrição do painel para leitores de tela."""
    linguagens = ", ".join(f"{ling.nome} {_porcentagem(ling.fracao)}" for ling in r.linguagens)
    dias = _plural(r.maior_sequencia, "dia", "dias")
    return (
        f"Estatísticas do GitHub nos últimos 12 meses: {r.contribuicoes} contribuições, "
        f"{r.commits} commits, {r.dias_ativos} dias com atividade e maior sequência de "
        f"{r.maior_sequencia} {dias}. Linguagens mais usadas: {linguagens or 'nenhuma'}."
    )


def painel(t: Tema, r: Resumo) -> str:
    w, h = LARGURA_IMAGEM, ALTURA_PAINEL
    partes = [
        "<defs>",
        f"  {gradiente_destaque(t)}",
        f'  <clipPath id="barra"><rect x="{X_LINGUAGENS}" y="{Y_BARRA}" '
        f'width="{LARGURA_BARRA}" height="14" rx="7"/></clipPath>',
        "</defs>",
        f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="16" '
        f'fill="{t.fundo}" stroke="{t.borda}"/>',
        f'<line x1="610" y1="28" x2="610" y2="{h - 28}" stroke="{t.borda}" '
        'stroke-dasharray="4 6"/>',
        f'<text x="40" y="52" class="mono" font-size="17" '
        f'fill="{t.secundario}">últimos 12 meses</text>',
        f'<text x="{X_LINGUAGENS}" y="52" class="mono" font-size="17" '
        f'fill="{t.secundario}">linguagens mais usadas</text>',
        *_cartoes_atividade(t, r),
    ]
    if r.linguagens:
        partes.append(_barra_linguagens(t, r.linguagens))
        partes.extend(_legenda_linguagens(t, r.linguagens))
    else:
        partes.append(
            f'<text x="{X_LINGUAGENS}" y="134" class="sans" font-size="18" '
            f'fill="{t.secundario}">Ainda não há código público para analisar.</text>'
        )
    repos = _plural(r.repositorios, "repositório público", "repositórios públicos")
    partes.append(
        f'<text x="{X_LINGUAGENS}" y="280" class="mono" font-size="14" '
        f'fill="{t.secundario}">calculado em {r.repositorios} {repos}</text>'
    )
    return svg(w, h, _titulo(r), "\n".join(partes))


# --------------------------------------------------------------------------


def main() -> None:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("Defina a variável GITHUB_TOKEN (veja as instruções no topo deste arquivo).")
    try:
        dados = buscar(USUARIO, token)
    except (urllib.error.URLError, RuntimeError) as erro:
        sys.exit(f"Não foi possível buscar as estatísticas: {erro}")
    resumo = resumir(dados, USUARIO)
    for nome_tema, tema in TEMAS.items():
        print(salvar("stats", nome_tema, painel(tema, resumo)).relative_to(RAIZ))


if __name__ == "__main__":
    main()
