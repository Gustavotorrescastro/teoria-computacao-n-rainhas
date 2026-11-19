"""Gera graficos, relatorio PDF e apresentacao a partir dos CSVs medidos."""

from __future__ import annotations

import csv
from datetime import datetime
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate, Frame, Image, KeepTogether, PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "build" / "generated"
FIG = GENERATED / "figures"
PDF = GENERATED / "pdf"
PRES = GENERATED / "presentation"
SUMMARY = list(csv.DictReader((ROOT / "data" / "results" / "summary.csv").open(encoding="utf-8")))
DATA = {(r["instance"], r["language"], r["algorithm"]): r for r in SUMMARY}
MEMORY_SUMMARY = list(csv.DictReader((ROOT / "data" / "results" / "memory_summary.csv").open(encoding="utf-8")))
MEMORY = {(r["n"], r["language"], r["algorithm"]): r for r in MEMORY_SUMMARY}
GEOMETRIC_SUMMARY = list(csv.DictReader((ROOT / "data" / "results" / "geometric_summary.csv").open(encoding="utf-8")))
GEOMETRIC = {(r["n"], r["language"], r["algorithm"]): r for r in GEOMETRIC_SUMMARY}
LIMIT = json.loads((ROOT / "data" / "results" / "limit_60s.json").read_text(encoding="utf-8"))
ENVIRONMENT = json.loads((ROOT / "data" / "results" / "environment.json").read_text(encoding="utf-8"))
GEOMETRIC_ENVIRONMENT = json.loads((ROOT / "data" / "results" / "geometric_environment.json").read_text(encoding="utf-8"))
SIZES = (4, 5, 6, 7, 8, 9)
MEMORY_SIZES = (6, 12, 24, 48, 96, 192)
PAPER_URL = "https://jair.org/index.php/jair/article/view/11079"
REPO_URL = "https://github.com/Gustavotorrescastro/teoria-computacao-n-rainhas"


def number(value: float, digits: int = 2) -> str:
    return f"{value:.{digits}f}".replace(".", ",")


def mean_sd(item: dict[str, str], digits: int = 3) -> str:
    return number(float(item["mean_ms"]), digits) + " ± " + number(float(item["sd_ms"]), digits)


def ms(instance: str, language: str, algorithm: str) -> float:
    return float(DATA[(instance, language, algorithm)]["mean_ms"])


def partial_mean(n: int, language: str, algorithm: str) -> float:
    names = [f"partial_n{n}"] + [f"partial_n{n}_{i}" for i in range(2, 6)]
    return sum(ms(name, language, algorithm) for name in names) / len(names)


def plot_all() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    palette = {("Python", "brute"): "#bb3e03", ("Python", "backtracking"): "#005f73",
               ("C++", "brute"): "#e9a100", ("C++", "backtracking"): "#0a9396"}
    labels = {("Python", "brute"): "Força bruta / Python", ("Python", "backtracking"): "Backtracking / Python",
              ("C++", "brute"): "Força bruta / C++", ("C++", "backtracking"): "Backtracking / C++"}
    fig, ax = plt.subplots(figsize=(8.7, 4.7), layout="constrained")
    for key, color in palette.items():
        lang, alg = key
        values = [ms(f"empty_n{n}", lang, alg) for n in SIZES]
        ax.plot(SIZES, values, marker="o", color=color, label=labels[key], linewidth=2)
    ax.set(xlabel="Tamanho n do tabuleiro", ylabel="Tempo médio (ms)", title="Tempo de execução - tabuleiro vazio")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xticks(SIZES, [str(n) for n in SIZES])
    ax.grid(True, which="both", alpha=.23)
    ax.legend(fontsize=8, ncol=2)
    fig.savefig(FIG / "tempos_loglog.png", dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.7, 4.2), layout="constrained")
    for language, color in (("Python", "#bb3e03"), ("C++", "#005f73")):
        ratio = [ms(f"empty_n{n}", language, "brute") / (math.factorial(n) * n) for n in SIZES]
        ax.plot(SIZES, ratio, marker="o", linewidth=2, color=color, label=language)
    ax.set(xlabel="Tamanho n", ylabel="T(n) / (n! . n), em ms", title="Razão empírica da força bruta")
    ax.set_xticks(SIZES)
    ax.grid(alpha=.23)
    ax.legend()
    fig.savefig(FIG / "razao_teorica.png", dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.7, 4.2), layout="constrained")
    leaves = [int(DATA[(f"empty_n{n}", "Python", "brute")]["operations"]) for n in SIZES]
    attempts = [int(DATA[(f"empty_n{n}", "Python", "backtracking")]["operations"]) for n in SIZES]
    ax.plot(SIZES, leaves, marker="o", linewidth=2, color="#bb3e03", label="Permutações completas (n!)")
    ax.plot(SIZES, attempts, marker="o", linewidth=2, color="#005f73", label="Tentativas de posição no backtracking")
    ax.set(xlabel="Tamanho n", ylabel="Contagem de operações", title="Espaço de busca observado")
    ax.set_yscale("log")
    ax.set_xticks(SIZES)
    ax.grid(True, which="both", alpha=.23)
    ax.legend()
    fig.savefig(FIG / "operacoes.png", dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.7, 4.2), layout="constrained")
    types = ("empty_n9", "partial", "complete_n9")
    names = ("Vazio", "5 parciais (média)", "Completo")
    x = list(range(3))
    width = .19
    for j, key in enumerate(palette):
        lang, alg = key
        ax.bar([v + (j - 1.5) * width for v in x],
               [partial_mean(9, lang, alg) if t == "partial" else ms(t, lang, alg) for t in types],
               width, color=palette[key], label=labels[key])
    ax.set(xlabel="Tipo de entrada (n=9)", ylabel="Tempo médio (ms)", title="Efeito de rainhas já posicionadas")
    ax.set_xticks(x, names)
    ax.set_yscale("log")
    ax.grid(axis="y", which="both", alpha=.23)
    ax.legend(fontsize=8, ncol=2)
    fig.savefig(FIG / "casos_n9.png", dpi=200)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(8.7, 4.0), layout="constrained", sharey=False)
    for ax, language in zip(axes, ("Python", "C++")):
        for algorithm, color, label in (("brute", "#bb3e03", "Força bruta"),
                                        ("backtracking", "#005f73", "Backtracking")):
            peaks = [float(MEMORY[(str(n), language, algorithm)]["mean_peak_bytes"]) / 1024
                     for n in MEMORY_SIZES]
            ax.plot(MEMORY_SIZES, peaks, marker="o", linewidth=2, color=color, label=label)
        ax.set(xlabel="Tamanho n", title=language)
        ax.set_xscale("log", base=2)
        ax.set_yscale("log")
        ax.set_xticks(MEMORY_SIZES, [str(n) for n in MEMORY_SIZES])
        ax.grid(True, which="both", alpha=.23)
        ax.legend(fontsize=8)
    axes[0].set_ylabel("Pico de alocações dinâmicas (KiB)")
    fig.suptitle("Memória auxiliar medida - seis linhas livres", fontsize=12)
    fig.savefig(FIG / "memoria_alocacoes.png", dpi=200)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(8.7, 3.7), layout="constrained")
    for ax, language in zip(axes, ("Python", "C++")):
        for algorithm, color, label in (("brute", "#bb3e03", "Força bruta"),
                                        ("backtracking", "#005f73", "Backtracking")):
            measured = [float(GEOMETRIC[(str(n), language, algorithm)]["mean_ms"])
                        for n in MEMORY_SIZES]
            ax.plot(MEMORY_SIZES, measured, marker="o", linewidth=2, color=color, label=label)
        ax.set(xlabel="Tamanho n (seis linhas livres)", title=language)
        ax.set_xscale("log", base=2)
        ax.set_yscale("log")
        ax.set_xticks(MEMORY_SIZES, [str(n) for n in MEMORY_SIZES])
        ax.grid(True, which="both", alpha=.23)
        ax.legend(fontsize=8)
    axes[0].set_ylabel("Tempo médio (ms)")
    fig.suptitle("Tempo em seis tamanhos geométricos", fontsize=12)
    fig.savefig(FIG / "tempos_geometricos.png", dpi=200)
    plt.close(fig)


def setup_fonts() -> None:
    fonts = Path("C:/Windows/Fonts")
    pdfmetrics.registerFont(TTFont("Arial", str(fonts / "arial.ttf")))
    pdfmetrics.registerFont(TTFont("Arial-Bold", str(fonts / "arialbd.ttf")))
    pdfmetrics.registerFontFamily("Arial", normal="Arial", bold="Arial-Bold")


styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="TitleCustom", fontName="Arial-Bold", fontSize=19, leading=24,
                          textColor=colors.HexColor("#123945"), spaceAfter=14))
styles.add(ParagraphStyle(name="HeadingCustom", fontName="Arial-Bold", fontSize=13, leading=17,
                          textColor=colors.HexColor("#0b6575"), spaceBefore=14, spaceAfter=8))
styles.add(ParagraphStyle(name="SubCustom", fontName="Arial-Bold", fontSize=10, leading=14,
                          textColor=colors.HexColor("#123945"), spaceBefore=9, spaceAfter=4))
styles.add(ParagraphStyle(name="BodyCustom", fontName="Arial", fontSize=9.2, leading=13.7,
                          spaceAfter=6, alignment=TA_LEFT))
styles.add(ParagraphStyle(name="SmallCustom", fontName="Arial", fontSize=8, leading=11,
                          spaceAfter=4, alignment=TA_LEFT))
styles.add(ParagraphStyle(name="CaptionCustom", fontName="Arial", fontSize=8, leading=11,
                          textColor=colors.HexColor("#4f5b60"), spaceAfter=8, alignment=TA_CENTER))


def p(text: str, style: str = "BodyCustom") -> Paragraph:
    return Paragraph(text, styles[style])


def heading(text: str) -> Paragraph:
    return p(text, "HeadingCustom")


def sub(text: str) -> Paragraph:
    return p(text, "SubCustom")


def figure(name: str, caption: str, width: float = 16.6 * cm) -> list:
    from PIL import Image as PILImage
    path = FIG / name
    with PILImage.open(path) as im:
        aspect = im.height / im.width
    return [Image(str(path), width=width, height=width * aspect), p(caption, "CaptionCustom")]


def table(data: list[list[str]], widths: list[float] | None = None) -> Table:
    tab = Table([[p(str(cell), "SmallCustom") for cell in row] for row in data], colWidths=widths,
                repeatRows=1, hAlign="LEFT")
    tab.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dcebef")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f8f8")]),
        ("GRID", (0, 0), (-1, -1), .35, colors.HexColor("#cbd8db")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return tab


def footer(canv: canvas.Canvas, doc: BaseDocTemplate) -> None:
    canv.saveState()
    canv.setFont("Arial", 8)
    canv.setFillColor(colors.HexColor("#617077"))
    canv.drawString(2 * cm, 1.3 * cm, "Teoria da Computação | N-rainhas")
    canv.drawRightString(A4[0] - 2 * cm, 1.3 * cm, str(doc.page))
    canv.restoreState()


def make_report() -> None:
    PDF.mkdir(parents=True, exist_ok=True)
    path = PDF / "relatorio_n_rainhas.pdf"
    doc = BaseDocTemplate(str(path), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                          topMargin=1.75 * cm, bottomMargin=1.75 * cm)
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, leftPadding=0,
                  rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates(PageTemplate(id="report", frames=frame, onPage=footer))
    story: list = []
    story += [p("N-rainhas: força bruta e backtracking em Python e C++", "TitleCustom"),
              p("<b>Disciplina:</b> Teoria da Computação | <b>Professor:</b> Daniel Bezerra | <b>Revisão:</b> " + datetime.now().strftime("%d/%m/%Y")),
              p("<b>Equipe:</b> Bruno Augusto da Rocha Leite Filho; Gustavo Torres Castro; Diego Ferreira Magnata; Pablo Coelho Gonçalves de Alcântara Rosendo."),
              p("<b>Resumo.</b> Implementamos quatro programas para contar todas as soluções de N-rainhas, usando o mesmo conjunto de entradas em Python e C++. Em tabuleiro vazio de n=9, a força bruta levou "
                + number(ms("empty_n9", "Python", "brute")) + " ms em Python e " + number(ms("empty_n9", "C++", "brute"))
                + " ms em C++; o backtracking levou " + number(ms("empty_n9", "Python", "backtracking")) + " ms e "
                + number(ms("empty_n9", "C++", "backtracking")) + " ms, respectivamente. São 15 medições por combinação e entradas idênticas, com semente fixa."),
              heading("1. Descrição do problema e dos algoritmos"),
              p("O tabuleiro n x n recebe uma rainha por linha e por coluna; duas rainhas não podem compartilhar diagonal. Uma entrada contém n e zero ou mais rainhas já posicionadas. A saída é o número de maneiras de completar o tabuleiro. A instância vazia é o N-rainhas clássico; instâncias parciais também permitem discutir a versão de completamento."),
              sub("Algoritmo A - força bruta por permutações"),
              p("Após validar as rainhas fixas, o algoritmo distribui as colunas livres entre as linhas livres, gerando todas as m! permutações, onde m é o número de linhas livres. Somente na folha verifica todas as n diagonais, sem encerrar a varredura ao encontrar conflito, e soma uma solução se nenhuma colisão existir. Não há poda de diagonais durante a geração."),
              sub("Algoritmo B - backtracking com poda"),
              p("O algoritmo visita as linhas em ordem. Para cada coluna candidata, consulta três estruturas booleanas: colunas ocupadas, diagonais de diferença linha-coluna e diagonais de soma linha+coluna. Um conflito interrompe imediatamente o ramo. Uma configuração completa acrescenta uma solução; o retorno desfaz as marcações. As rainhas fixas restringem a única escolha da sua linha."),
              p("<b>Pseudocódigo A:</b> para cada permutação das colunas livres, formar tabuleiro; percorrer as n linhas checando diagonais; se válido, incrementar contador."),
              p("<b>Pseudocódigo B:</b> busca(linha): se linha=n, incrementar contador; senão, para cada coluna permitida na linha, se coluna e diagonais estiverem livres, marcar, chamar busca(linha+1), desmarcar."),
              heading("2. Classificação assintótica"),
              p("Na força bruta, cada uma das m! permutações custa Θ(n) para verificar diagonais. A geração também é limitada por O(m! m); como m≤n, o custo total em instâncias válidas é <b>Θ(n·m!)</b>, além da leitura/validação Θ(n). Para o tabuleiro vazio, m=n: <b>O(n·n!), Ω(n·n!) e Θ(n·n!)</b>. A memória auxiliar, incluindo a pilha recursiva, é O(n)."),
              p("No backtracking, defina A(n,P) como o número de posições candidatas efetivamente examinadas para a entrada parcial P. Cada tentativa usa O(1), mais a validação inicial Θ(n), logo o custo específico da entrada é <b>Θ(n + A(n,P))</b>. Isso dá O(n·n!) no pior limite combinatório e Ω(n) pelo processamento da entrada. A expressão Θ(n + A(n,P)) é o limite apertado; chamar Θ(n!) para toda entrada seria incorreto, pois a poda varia com P. A memória auxiliar, inclusive pilha, é O(n)."),
              KeepTogether([
                  heading("3. Melhor caso, pior caso e caso médio"),
                  p("No cenário sem rainhas fixas, A visita exatamente n! folhas para todo n, portanto seu custo praticamente independe de haver poucas ou muitas soluções. Em B, fixar uma rainha restringe as escolhas daquela linha: a árvore de busca parcial é um subconjunto da árvore do tabuleiro vazio. Assim, no conjunto de entradas com mesmo n e rainhas pré-posicionadas, o tabuleiro vazio maximiza as tentativas; conflitos fixos inválidos encerram a busca após a validação. Uma solução completamente fixada é o caso favorável para ambos, com custo Θ(n). Cinco entradas parciais aleatórias por tamanho formam o cenário médio amostral. Essa média não representa todas as configurações possíveis.")])]

    story += [heading("4. Aplicabilidade prática"),
              p("Força bruta é simples, serve como referência independente de corretude e funciona para n pequeno ou para tabuleiros quase completos. Seu crescimento fatorial inviabiliza n maior. Backtracking é preferível para enumerar ou contar soluções em tamanhos moderados, porque evita expandir configurações já impossíveis. Para apenas decidir se o tabuleiro vazio tem solução, os dois métodos são desnecessários: há uma solução para n=1 e para todo n≥4; n=2 e n=3 não têm solução [1]. Para instâncias parciais grandes, técnicas de propagação de restrições e SAT podem ser mais adequadas."),
              heading("5. Simulação e metodologia experimental"),
              p("O script de geração usa semente 20261116. Para cada n=4,5,6,7,8,9 há um tabuleiro vazio, cinco tabuleiros parciais com duas rainhas não atacantes sorteadas sem condicionar à existência de solução e um tabuleiro completamente preenchido; acrescentou-se n=4 com primeira rainha na coluna 0, impossível de completar. São 43 entradas. O incremento de uma unidade em n multiplica o espaço de permutações por n; por isso seis tamanhos pequenos já cobrem um crescimento maior que geométrico de trabalho, sem impor execuções inviáveis."),
              p("Cada combinação de linguagem e algoritmo usa o mesmo arquivo de entrada. O processo lê o arquivo antes do cronômetro; cada execução temporizada inclui somente a função do algoritmo. Há " + str(ENVIRONMENT["warmup"]) + " aquecimentos e " + str(ENVIRONMENT["repetitions"]) + " execuções medidas por entrada. As médias, desvios padrão, medianas e medidas brutas são salvos em CSV. Compilação: " + ENVIRONMENT["compiler"] + " com " + ENVIRONMENT["flags"] + "; Python " + ENVIRONMENT["python"].split()[0] + "; sistema " + ENVIRONMENT["platform"] + "; CPU " + ENVIRONMENT["cpu_name"] + "; RAM física " + number(float(ENVIRONMENT["ram_bytes"]) / 2**30, 1) + " GiB. Os tempos dependem deste ambiente e da carga do sistema."),
              p("Para o bônus de memória, uma rodada separada usa n=6,12,24,48,96,192, sempre com seis linhas livres e as demais rainhas fixas em uma solução válida. Assim as quatro versões recebem exatamente a mesma entrada, mas o fatorial das linhas livres permanece viável. São 15 processos independentes por combinação. Em Python, tracemalloc mede o pico de alocações rastreadas durante a chamada; em C++, um contador de operator new mede o pico de bytes dinamicamente alocados pelas mesmas funções. Leitura, inicialização do processo e escrita da saída ficam fora da medição. As medidas não são memória residente total e não devem ser comparadas diretamente entre linguagens."),
              p("A corretude foi verificada pelas quatro implementações nas " + str(len({r["instance"] for r in SUMMARY})) + " entradas, por contagens conhecidas dos tabuleiros vazios e por testes automatizados de casos de borda. Todos os programas retornaram os mesmos resultados. Tempos muito curtos, sobretudo em C++ com n pequeno ou tabuleiro completo, sofrem maior ruído de relógio e escalonamento; as conclusões de desempenho se apoiam sobretudo em n≥7."),
              PageBreak(),
              heading("6. Gráficos e tabelas comparativas"),
              p("A tabela apresenta média ± desvio padrão em milissegundos, com 15 repetições por célula, para entradas vazias. A coluna de soluções confirma a saída comum."),
              table([["n", "Soluções", "A / Python", "B / Python", "A / C++", "B / C++"]] + [
                  [str(n), DATA[(f"empty_n{n}", "Python", "brute")]["solutions"]] + [
                      mean_sd(DATA[(f"empty_n{n}", lang, alg)])
                      for lang, alg in (("Python", "brute"), ("Python", "backtracking"),
                                        ("C++", "brute"), ("C++", "backtracking"))]
                  for n in SIZES], [1.15*cm, 1.65*cm, 3.25*cm, 3.25*cm, 3.25*cm, 3.25*cm]),
              Spacer(1, 6),
              *figure("tempos_loglog.png", "Figura 1. Escala log-log: quatro implementações sobre as mesmas entradas vazias.")]

    n = 9
    py_speedup = ms("empty_n9", "Python", "brute") / ms("empty_n9", "Python", "backtracking")
    cpp_speedup = ms("empty_n9", "C++", "brute") / ms("empty_n9", "C++", "backtracking")
    language_ratio = ms("empty_n9", "Python", "brute") / ms("empty_n9", "C++", "brute")
    story += [heading("6. Análise dos resultados (continuação)"),
              p("Para n=9, a poda foi " + number(py_speedup, 1) + " vezes mais rápida em Python e " + number(cpp_speedup, 1)
                + " vezes em C++ na média. Mantido o algoritmo A, C++ foi " + number(language_ratio, 1)
                + " vezes mais rápido que Python. Esses fatores são observações deste equipamento e desta implementação, não propriedades assintóticas das linguagens."),
              *figure("razao_teorica.png", "Figura 2. T(n)/(n!·n) da força bruta: aproxima uma constante no intervalo maior, coerente com Θ(n!·n)."),
              *figure("operacoes.png", "Figura 3. Busca: a força bruta visita n! folhas; B registra tentativas de posições. As contagens têm unidades distintas e ilustram a poda."),
              KeepTogether([
                  heading("6. Efeito das entradas forçadas"),
                  *figure("casos_n9.png", "Figura 4. Para n=9, o tabuleiro vazio exige mais busca; a barra parcial é a média de cinco entradas; o completo exige validação curta.")]),
              p("O caso vazio de n=9 tem " + DATA[("empty_n9", "Python", "brute")]["solutions"] + " soluções; o completo tem " + DATA[("complete_n9", "Python", "brute")]["solutions"] + ". As cinco entradas parciais sorteadas têm, respectivamente, " + ", ".join(DATA[(name, "Python", "brute")]["solutions"] for name in ["partial_n9"] + [f"partial_n9_{i}" for i in range(2, 6)]) + " soluções. Há entradas parciais insolúveis, como n=4 com rainha fixa em (0,0); as quatro implementações concordaram. Para instâncias completas, o valor minúsculo de tempo em C++ torna razões de desempenho pouco informativas."),
              PageBreak(),
              heading("6. Escala geométrica complementar"),
              p("A série controlada dobra n de 6 a 192 mantendo m=6 linhas livres; as demais rainhas vêm de uma solução válida. Cada implementação recebeu as mesmas seis entradas, com " + str(GEOMETRIC_ENVIRONMENT["warmup"]) + " aquecimentos e " + str(GEOMETRIC_ENVIRONMENT["repetitions"]) + " repetições, totalizando " + str(len(GEOMETRIC_SUMMARY) * int(GEOMETRIC_ENVIRONMENT["repetitions"])) + " tempos medidos. Manter m fixo torna a força bruta viável e isola o efeito de n, sem representar o pior caso do tabuleiro vazio. O modelo teórico de A passa a Θ(n·6!)=Θ(n); em B, as posições tentadas ainda dependem das rainhas fixas."),
              p("Uma sondagem separada, com uma execução por tamanho, registrou o limite de 60 s do tabuleiro vazio na combinação limitante, força bruta em Python: n=10 levou "
                + number(float(LIMIT["observations"][0]["algorithm_seconds"]), 2)
                + " s para 3.628.800 folhas; n=11 excedeu 60 s. Essa sondagem não integra as médias de 15 repetições."),
              table([["n", "A / Python", "B / Python", "A / C++", "B / C++"]] + [
                  [str(size)] + [mean_sd(GEOMETRIC[(str(size), lang, alg)])
                                 for lang, alg in (("Python", "brute"), ("Python", "backtracking"),
                                                   ("C++", "brute"), ("C++", "backtracking"))]
                  for size in MEMORY_SIZES], [1.4*cm, 3.75*cm, 3.75*cm, 3.75*cm, 3.75*cm]),
              p("Tabela: média ± desvio padrão em ms para as entradas geométricas, 15 repetições por célula.", "CaptionCustom"),
              *figure("tempos_geometricos.png", "Figura 5. Tempos médios nas mesmas entradas de tamanho geométrico; seis linhas livres em cada tabuleiro."),
              PageBreak(),
              heading("6. Bônus: uso de memória"),
              p("A tabela mostra média ± desvio padrão do pico de alocações dinâmicas, em KiB, de 15 execuções por célula. A métrica não inclui toda a pilha recursiva."),
              table([["n", "A / Python", "B / Python", "A / C++", "B / C++"]] + [
                  [str(size)] + [number(float(MEMORY[(str(size), lang, alg)]["mean_peak_bytes"]) / 1024, 2)
                                 + " ± " + number(float(MEMORY[(str(size), lang, alg)]["sd_peak_bytes"]) / 1024, 2)
                                 for lang, alg in (("Python", "brute"), ("Python", "backtracking"),
                                                   ("C++", "brute"), ("C++", "backtracking"))]
                  for size in MEMORY_SIZES], [1.4*cm, 3.75*cm, 3.75*cm, 3.75*cm, 3.75*cm]),
              Spacer(1, 7),
              *figure("memoria_alocacoes.png", "Figura 6. Pico de alocações dinâmicas nas entradas de memória. Os painéis têm escalas próprias; compare tendências dentro de cada linguagem."),
              p("De n=6 a 192 (32 vezes maior), o pico medido passa de " + number(float(MEMORY[("6", "Python", "brute")]["mean_peak_bytes"]) / 1024, 2) + " para " + number(float(MEMORY[("192", "Python", "brute")]["mean_peak_bytes"]) / 1024, 2) + " KiB em Python/A e de " + number(float(MEMORY[("6", "C++", "brute")]["mean_peak_bytes"]) / 1024, 2) + " para " + number(float(MEMORY[("192", "C++", "brute")]["mean_peak_bytes"]) / 1024, 2) + " KiB em C++/A. O crescimento é compatível com estruturas auxiliares O(n): tabuleiro, vetores de ocupação e conjuntos de diagonais crescem com n. Saltos e patamares em Python refletem a capacidade interna de listas e conjuntos. A pilha recursiva não é coberta integralmente por esses contadores: nas entradas medidas, a profundidade máxima atingida é 7 chamadas em A (seis linhas livres) e n+1 em B. Para o problema geral, ambas as pilhas têm limite O(n). Os dados apoiam, mas não provam, a análise assintótica."),
              PageBreak(),
              heading("7. Reflexão sobre P e NP"),
              p("É essencial definir a pergunta. A <b>decisão do N-rainhas vazio</b> - existe uma solução? - está em P: basta verificar n, pois há solução para n=1 e n≥4 e não há para n=2 ou 3 [1]. Nosso experimento, por escolha metodológica, <b>conta todas as soluções</b>, uma tarefa diferente e muito mais cara que decidir existência. Portanto, o crescimento medido não demonstra que a decisão esteja fora de P."),
              p("O problema vizinho é <b>completar N-rainhas</b>: dadas rainhas já colocadas, é possível acrescentar as restantes sem ataques? Essa versão de decisão pertence a NP, pois um tabuleiro completo pode ser verificado em tempo polinomial. Gent, Jefferson e Nightingale [1] provaram que ela é NP-completa por uma cadeia de reduções polinomiais partindo de uma variante de satisfatibilidade; também mostraram #P-completude da versão de contagem do completamento. A diferença é que as posições pré-fixadas codificam restrições arbitrárias e eliminam a resposta simples que existe no tabuleiro vazio."),
              p("O backtracking com poda é um algoritmo exato para o problema vizinho e melhora muitas entradas na prática, mas sua redução da árvore não constitui uma prova de tempo polinomial. A dificuldade teórica se refere ao pior caso de todas as instâncias parciais, não a estas 43 amostras."),
              heading("Referência"),
              p("[1] GENT, Ian P.; JEFFERSON, Christopher; NIGHTINGALE, Peter. Complexity of n-Queens Completion. <i>Journal of Artificial Intelligence Research</i>, v. 59, p. 815-848, 2017. "
                + PAPER_URL, "SmallCustom"),
              heading("Ambiente, reprodutibilidade e responsabilidades"),
              p("O código-fonte, os geradores, a medição, os testes e os CSVs estão no checkout local do projeto. Os gráficos e PDFs gerados acompanham o pacote de entrega; o README contém os comandos de reprodução. Esta revisão não alterou o repositório remoto " + REPO_URL + "."),
              p("<b>Contribuições informadas no material anterior:</b> Bruno Augusto - força bruta e justificativa assintótica; Gustavo Torres Castro - metodologia experimental, CSVs e gráficos; Diego Magnata - backtracking, testes e apresentação; Pablo Coelho - texto final, referências e apresentação. Estas atribuições não foram verificadas nesta auditoria. Recomenda-se que todos revisem o código e a análise antes da apresentação."),
              heading("Declaração de uso de IA"),
              p("Durante o desenvolvimento, utilizamos o <b>ChatGPT (OpenAI Codex)</b> como ferramenta de IA generativa no estudo teórico, na implementação e revisão do código, na preparação dos experimentos, na análise dos resultados e na organização do relatório e da apresentação."),
              p("A IA foi utilizada diretamente para implementar e ajustar os algoritmos em Python e C++, os scripts de geração de entradas, medição de tempo e memória, testes e gráficos. Também ajudou a entender o funcionamento de cada implementação, discutir escolhas do código, identificar possíveis erros e esclarecer as classificações de complexidade. Na etapa experimental, apoiou a compreensão das métricas, a interpretação dos gráficos e a discussão das diferenças entre Python e C++."),
              p("<b>Exemplos de consultas:</b> diferenças entre força bruta e backtracking; justificativa de O, Ω e Θ; cuidados ao comparar Python e C++; interpretação de gráficos log-log; distinção entre N-rainhas vazio e completamento; organização da apresentação."),
              p("<b>Validação e responsabilidade:</b> O código e os resultados foram auditados tecnicamente nesta revisão. Os integrantes são responsáveis por compreender as implementações, revisar os materiais e explicar as conclusões do trabalho."),
              Spacer(1, 12),
              p("Fim do relatório.", "CaptionCustom")]
    doc.build(story)
    print(f"Relatório: {path}")


def slide_title(c: canvas.Canvas, title: str, subtitle: str = "") -> None:
    w, h = landscape(A4)
    c.setFillColor(colors.HexColor("#f8fbfb"))
    c.rect(0, 0, w, h, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#0b6575"))
    c.rect(0, h - 20, w, 20, fill=1, stroke=0)
    c.setFont("Arial-Bold", 25)
    c.setFillColor(colors.HexColor("#123945"))
    c.drawString(38, h - 68, title)
    if subtitle:
        c.setFont("Arial", 11)
        c.setFillColor(colors.HexColor("#5a6a70"))
        c.drawString(39, h - 88, subtitle)


def slide_bullets(c: canvas.Canvas, lines: list[str], y: float = 465) -> None:
    c.setFillColor(colors.HexColor("#263d44"))
    c.setFont("Arial", 15)
    for line in lines:
        c.drawString(54, y, "• " + line)
        y -= 39


def make_slides() -> None:
    PRES.mkdir(parents=True, exist_ok=True)
    path = PRES / "apresentacao_n_rainhas.pdf"
    c = canvas.Canvas(str(path), pagesize=landscape(A4))
    w, h = landscape(A4)
    slide_title(c, "N-rainhas: contar soluções", "Teoria da Computação | apresentação de Diego e Pablo | 8 a 10 minutos")
    slide_bullets(c, ["Uma rainha por linha e coluna, sem ataques diagonais", "Força bruta e backtracking em Python e C++", "Pergunta: quanto a poda reduz a busca e o tempo?"], h-180)
    c.showPage()
    slide_title(c, "O problema em um tabuleiro 4 x 4", "Uma solução: colunas [1, 3, 0, 2], de cima para baixo")
    board = [1, 3, 0, 2]
    cell = 63
    for row in range(4):
        for col in range(4):
            x, y = 62 + col * cell, 170 + (3 - row) * cell
            c.setFillColor(colors.HexColor("#e7f0f2" if (row + col) % 2 == 0 else "#98bec7"))
            c.rect(x, y, cell, cell, fill=1, stroke=0)
            if board[row] == col:
                c.setFillColor(colors.HexColor("#123945"))
                c.setFont("Arial-Bold", 36)
                c.drawCentredString(x + cell / 2, y + 15, "Q")
    c.setFont("Arial", 15)
    c.setFillColor(colors.HexColor("#263d44"))
    for y, line in zip((405, 355, 305, 255),
                       ("Uma coluna distinta em cada linha", "Diferenças linha-coluna distintas",
                        "Somas linha+coluna distintas", "Entrada parcial: algumas rainhas fixas")):
        c.drawString(370, y, line)
    c.showPage()
    slide_title(c, "Duas formas de percorrer as escolhas")
    c.setFont("Arial-Bold", 18)
    c.setFillColor(colors.HexColor("#bb3e03"))
    c.drawString(50, 430, "A. Força bruta")
    c.setFillColor(colors.HexColor("#005f73"))
    c.drawString(425, 430, "B. Backtracking")
    c.setFont("Arial", 15)
    c.setFillColor(colors.HexColor("#263d44"))
    for y, line in zip((370, 327, 284, 241),
                       ("Distribui colunas sem repetir", "Gera todas as m! permutações", "Confere diagonais só na folha", "Conta as configurações válidas")):
        c.drawString(55, y, line)
    for y, line in zip((370, 327, 284, 241),
                       ("Testa coluna e diagonais", "Conflito: corta o ramo", "Sem conflito: avança uma linha", "Desfaz a escolha ao retornar")):
        c.drawString(430, y, line)
    c.setStrokeColor(colors.HexColor("#b7cdd2"))
    c.line(405, 210, 405, 440)
    c.setFont("Arial-Bold", 14)
    c.setFillColor(colors.HexColor("#123945"))
    c.drawString(55, 170, "n=4: A examina 24 folhas")
    c.setFont("Arial", 12)
    c.drawString(55, 135, "Mesmo as inválidas chegam ao teste final.")
    c.drawString(470, 180, "B: rainha na linha 0, coluna 1")
    c.setStrokeColor(colors.HexColor("#98bec7"))
    for x in (470, 550, 630, 710):
        c.line(620, 160, x, 112)
    c.setFont("Arial-Bold", 12)
    for x, label in zip((458, 538, 618, 698), ("0 ×", "1 ×", "2 ×", "3 ok")):
        c.drawString(x, 91, label)
    c.setFont("Arial", 11)
    c.drawString(470, 60, "Três ramos cortados; apenas um avança.")
    c.showPage()
    slide_title(c, "O custo da busca", "n é o tamanho; m é o número de linhas livres; A é o número de tentativas no backtracking")
    slide_bullets(c, ["Força bruta: Θ(n · m!) em entradas válidas", "Tabuleiro vazio: O, Ω e Θ(n · n!)", "Backtracking: Θ(n + A); limite superior O(n · n!)", "Memória auxiliar: O(n) nas duas implementações", "Melhor entrada completa: Θ(n); médio depende da amostra"], h-150)
    c.showPage()
    slide_title(c, "Como medimos", "As quatro variantes recebem os mesmos arquivos")
    slide_bullets(c, ["43 entradas: n=4 a 9, vazias, parciais e completas", "Semente fixa 20261116 para as parciais", "3 aquecimentos e 15 tempos por combinação", "Leitura e impressão fora do cronômetro", "CSV bruto, média, desvio padrão e mediana auditados"], h-150)
    c.showPage()
    slide_title(c, "Tabuleiro vazio: crescimento fatorial", "Média em ms; a tabela do relatório apresenta os desvios padrão")
    c.drawImage(str(FIG / "tempos_loglog.png"), 52, 30, width=w-104, height=h-135, preserveAspectRatio=True, anchor="c")
    c.showPage()
    slide_title(c, "Seis linhas livres: outra série", "n dobra de 6 a 192, mas m=6 permanece fixo; não representa o tabuleiro vazio")
    c.drawImage(str(FIG / "tempos_geometricos.png"), 52, 30, width=w-104, height=h-135,
                preserveAspectRatio=True, anchor="c")
    c.showPage()
    slide_title(c, "O que aconteceu em n=9 vazio", "Tempo em ms: média ± desvio padrão, 15 execuções")
    slide_bullets(c, ["Python A: " + mean_sd(DATA[("empty_n9", "Python", "brute")]) + "    B: " + mean_sd(DATA[("empty_n9", "Python", "backtracking")]),
                      "C++ A: " + mean_sd(DATA[("empty_n9", "C++", "brute")]) + "    B: " + mean_sd(DATA[("empty_n9", "C++", "backtracking")]),
                      DATA[("empty_n9", "Python", "brute")]["solutions"] + " soluções; " + DATA[("empty_n9", "Python", "brute")]["operations"] + " folhas em A",
                      DATA[("empty_n9", "Python", "backtracking")]["operations"] + " tentativas de posição em B",
                      "As unidades dessas duas contagens são diferentes"], h-155)
    c.showPage()
    slide_title(c, "Conclusão e P × NP")
    slide_bullets(c, ["A poda reduziu a busca nas entradas medidas", "Tempos observados não provam um limite assintótico", "Decidir N-rainhas vazio está em P", "Completar um tabuleiro parcial é NP-completo", "Contar seus completamentos é #P-completo"], h-150)
    c.setFont("Arial", 8)
    c.drawString(48, 28, "Fonte teórica: Gent, Jefferson e Nightingale, JAIR 59 (2017), doi:10.1613/jair.5512.")
    c.showPage()
    c.save()
    notes = PRES / "roteiro_8_a_10_minutos.md"
    notes.write_text("""# Roteiro de apresentação (8 a 10 minutos)

Distribuição sugerida de falas, sujeita à revisão de Diego e Pablo. Os números dos slides são gerados dos CSVs medidos.

1. **0:00–0:40, Diego, slide 1:** apresente a pergunta experimental: comparar busca exaustiva e poda nas mesmas entradas.
2. **0:40–1:35, Diego, slide 2:** mostre uma solução 4 x 4. Explique colunas e diagonais; indique que uma entrada pode fixar rainhas.
3. **1:35–2:40, Diego, slide 3:** em A, todas as permutações chegam à verificação final. Em B, um conflito impede a expansão do ramo. Explique o desfazer da escolha.
4. **2:40–3:35, Diego, slide 4:** defina m e A. Diferencie o limite apertado de A, a expressão dependente da entrada para B e o espaço O(n).
5. **3:35–4:25, Pablo, slide 5:** descreva as 43 entradas, a semente, os 3 aquecimentos, as 15 medições e o escopo do cronômetro.
6. **4:25–5:35, Pablo, slide 6:** leia o gráfico logarítmico. A série vazia revela o crescimento fatorial; compare métodos e linguagens sem extrapolar além dos n medidos.
7. **5:35–6:25, Pablo, slide 7:** mostre que manter seis linhas livres muda a pergunta experimental. O crescimento em n aqui não substitui o caso vazio.
8. **6:25–7:35, Pablo, slide 8:** use média ± desvio padrão e as contagens de n=9. As unidades de folhas e tentativas diferem; tempos muito curtos têm mais ruído relativo.
9. **7:35–8:50, Diego e Pablo, slide 9:** Pablo conclui a comparação; Diego explica P, NP e #P. Reservem até 1 minuto para perguntas ou variação de ritmo.

O bônus de memória está no relatório e pode entrar nas perguntas. A declaração de uso de IA permanece no relatório. Cada apresentador deve revisar as quatro implementações e os dados antes da fala.
""", encoding="utf-8")
    print(f"Apresentação: {path}")


def main() -> None:
    setup_fonts()
    plot_all()
    make_report()
    make_slides()


if __name__ == "__main__":
    main()
