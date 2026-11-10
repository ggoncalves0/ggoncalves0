import io
import json
import unittest
import xml.etree.ElementTree as ET
from unittest import mock

import gerar_stats as gs
from comum import TEMAS


def calendario(contagens: list[int]) -> dict:
    """Calendário de contribuições com uma contagem por dia, a partir de 1º de janeiro."""
    dias = [
        {"date": f"2026-01-{i + 1:02d}", "contributionCount": n} for i, n in enumerate(contagens)
    ]
    semanas = [{"contributionDays": dias[i : i + 7]} for i in range(0, len(dias), 7)]
    return {"totalContributions": sum(contagens), "weeks": semanas}


def repo(nome: str, *linguagens: tuple[str, str | None, int]) -> dict:
    arestas = [
        {"size": tamanho, "node": {"name": ling, "color": cor}} for ling, cor, tamanho in linguagens
    ]
    return {"name": nome, "languages": {"edges": arestas}}


def usuario(contagens: list[int], repos: list[dict], commits: int = 0) -> dict:
    """Resposta da API no mesmo formato que a consulta GraphQL devolve."""
    return {
        "repositories": {"nodes": repos},
        "contributionsCollection": {
            "totalCommitContributions": commits,
            "contributionCalendar": calendario(contagens),
        },
    }


def resumo(**mudancas) -> gs.Resumo:
    dados = {
        "contribuicoes": 24,
        "commits": 21,
        "dias_ativos": 15,
        "maior_sequencia": 4,
        "repositorios": 4,
        "linguagens": (
            gs.Linguagem("TypeScript", "#3178c6", 0.7),
            gs.Linguagem("Python", "#3572A5", 0.3),
        ),
    }
    dados.update(mudancas)
    return gs.Resumo(**dados)


class RespostaFalsa(io.BytesIO):
    """Imita a resposta de urllib.request.urlopen, que é usada com "with"."""

    def __enter__(self):
        return self

    def __exit__(self, *erro):
        self.close()


class TestResumir(unittest.TestCase):
    def test_conta_contribuicoes_dias_ativos_e_maior_sequencia(self):
        r = gs.resumir(usuario([1, 2, 0, 1, 1, 1, 0, 3], [], commits=5), "eu")
        self.assertEqual(r.contribuicoes, 9)
        self.assertEqual(r.commits, 5)
        self.assertEqual(r.dias_ativos, 6)
        self.assertEqual(r.maior_sequencia, 3)

    def test_sequencia_nao_depende_da_ordem_das_semanas(self):
        dados = usuario([1, 1, 1, 1, 1, 1, 1, 1, 0], [])
        dados["contributionsCollection"]["contributionCalendar"]["weeks"].reverse()
        self.assertEqual(gs.resumir(dados, "eu").maior_sequencia, 8)

    def test_soma_as_linguagens_de_todos_os_repositorios(self):
        repos = [
            repo("site", ("Python", "#3572A5", 300), ("CSS", "#663399", 100)),
            repo("api", ("Python", "#3572A5", 600)),
        ]
        r = gs.resumir(usuario([], repos), "eu")
        self.assertEqual([ling.nome for ling in r.linguagens], ["Python", "CSS"])
        self.assertAlmostEqual(r.linguagens[0].fracao, 0.9)
        self.assertEqual(r.repositorios, 2)

    def test_ignora_o_repositorio_do_perfil(self):
        repos = [repo("Eu", ("Python", "#3572A5", 999)), repo("app", ("Go", "#00ADD8", 1))]
        r = gs.resumir(usuario([], repos), "eu")
        self.assertEqual([ling.nome for ling in r.linguagens], ["Go"])
        self.assertEqual(r.repositorios, 1)

    def test_limita_a_quantidade_de_linguagens_e_preenche_cor_ausente(self):
        repos = [repo("app", *[(f"L{i}", None, 100 - i) for i in range(10)])]
        r = gs.resumir(usuario([], repos), "eu")
        self.assertEqual(len(r.linguagens), gs.MAX_LINGUAGENS)
        self.assertEqual(r.linguagens[0].cor, "#8b949e")

    def test_respeita_as_linguagens_ignoradas(self):
        repos = [repo("site", ("HTML", "#e34c26", 900), ("JavaScript", "#f1e05a", 100))]
        with mock.patch.object(gs, "IGNORAR_LINGUAGENS", {"HTML"}):
            r = gs.resumir(usuario([], repos), "eu")
        self.assertEqual([(ling.nome, ling.fracao) for ling in r.linguagens], [("JavaScript", 1.0)])

    def test_sem_codigo_publico(self):
        self.assertEqual(gs.resumir(usuario([0, 0], [repo("vazio")]), "eu").linguagens, ())


class TestBuscar(unittest.TestCase):
    def responder(self, conteudo: dict):
        resposta = RespostaFalsa(json.dumps(conteudo).encode())
        return mock.patch("urllib.request.urlopen", return_value=resposta)

    def test_envia_o_login_e_o_token(self):
        with self.responder({"data": {"user": {"ok": True}}}) as urlopen:
            self.assertEqual(gs.buscar("eu", "segredo"), {"ok": True})
        pedido = urlopen.call_args.args[0]
        self.assertEqual(json.loads(pedido.data)["variables"], {"login": "eu"})
        self.assertEqual(pedido.get_header("Authorization"), "bearer segredo")

    def test_erro_da_api_vira_excecao(self):
        resposta = {"data": {"user": None}, "errors": [{"message": "Could not resolve to a User"}]}
        with self.responder(resposta), self.assertRaises(RuntimeError):
            gs.buscar("ninguem", "segredo")


class TestPainel(unittest.TestCase):
    def test_gera_svg_valido_nos_dois_temas(self):
        for tema in TEMAS.values():
            ET.fromstring(gs.painel(tema, resumo()))

    def test_formata_numeros_porcentagens_e_plural(self):
        svg = gs.painel(
            TEMAS["dark"], resumo(contribuicoes=12345, maior_sequencia=1, repositorios=1)
        )
        for trecho in [">12.345<", "> dia</tspan>", "1 repositório público", ">70,0%<"]:
            self.assertIn(trecho, svg)

    def test_avisa_quando_nao_ha_linguagens(self):
        svg = gs.painel(TEMAS["light"], resumo(linguagens=()))
        self.assertIn("Ainda não há código público para analisar.", svg)

    def test_encurta_nomes_longos_de_linguagem(self):
        longa = gs.Linguagem("Visual Basic .NET Framework", "#945db7", 1.0)
        self.assertIn("…</text>", gs.painel(TEMAS["dark"], resumo(linguagens=(longa,))))


if __name__ == "__main__":
    unittest.main()
