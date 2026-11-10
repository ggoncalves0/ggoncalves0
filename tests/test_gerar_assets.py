import unittest
import xml.etree.ElementTree as ET

import gerar_assets as ga
from comum import TEMAS, contraste, cor_legivel


class TestImagens(unittest.TestCase):
    def test_gera_svgs_validos_nos_dois_temas(self):
        for tema in TEMAS.values():
            for imagem in (ga.banner(tema), ga.stack(tema), ga.badge(tema, "email", "a@b.com")):
                ET.fromstring(imagem)

    def test_stack_mostra_todas_as_tecnologias(self):
        svg = ga.stack(TEMAS["dark"])
        for _, itens in ga.STACK:
            for nome in itens:
                self.assertIn(f">{ga.dados_icone(nome)['title']}</text>", svg)

    def test_textos_sao_escapados(self):
        self.assertIn("&gt; olá, eu sou", ga.banner(TEMAS["dark"]))


class TestCores(unittest.TestCase):
    def test_cor_com_pouco_contraste_e_ajustada(self):
        fundo = "#ffffff"
        cor = cor_legivel("#f7df1e", fundo, "#1f2328")  # amarelo do JavaScript no fundo branco
        self.assertGreaterEqual(contraste(cor, fundo), 2.2)

    def test_cor_neutra_vira_a_cor_do_texto(self):
        self.assertEqual(cor_legivel("#000000", "#0d1117", "#e6edf3"), "#e6edf3")

    def test_cor_com_contraste_suficiente_nao_muda(self):
        self.assertEqual(cor_legivel("#3776ab", "#ffffff", "#1f2328"), "#3776ab")


if __name__ == "__main__":
    unittest.main()
