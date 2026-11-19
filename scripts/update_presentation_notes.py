"""Replace obsolete internal notes without changing slide content or layout."""

from __future__ import annotations

import argparse
import os
import posixpath
import tempfile
import zipfile
from copy import copy
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DECK = ROOT / "docs/entrega/Apresentacao_N_Rainhas.pptx"
DEFAULT_OUTPUT = ROOT / "build/generated/presentation/Apresentacao_N_Rainhas_notas_preview.pptx"

P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS = {"p": P_NS, "a": A_NS, "r": R_NS}
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"

NOTES = {
    1: "A configuração de uma solução pode ser representada por uma permutação de colunas. A busca conta todas as configurações válidas e compara força bruta e backtracking em Python e C++.",
    2: "Uma solução tem uma rainha por linha e por coluna e nenhuma dupla na mesma diagonal. Entradas parciais fixam posições; o tabuleiro vazio n=9 tem 352 soluções.",
    3: "A força bruta enumera as permutações das colunas livres e testa diagonais nas folhas completas. O backtracking testa coluna e diagonais a cada escolha, abandona conflitos e desfaz marcações ao retornar.",
    4: "Para n=4 vazio, a força bruta percorre 4!=24 folhas e encontra duas soluções. No ramo desenhado, (linha 0, coluna 1) elimina as colunas 0, 1 e 2 na linha 1. A coluna 3 segue para (2,0) e (3,2), formando [1,3,0,2].",
    5: "Com m linhas livres, a força bruta completa m! permutações e examina n linhas em cada folha: Θ(n·m!). No tabuleiro vazio, m=n. No backtracking, A(n,P) conta candidatas testadas para entrada válida P: Θ(n+A(n,P)); o melhor caso válido é Θ(n) e O(n·n!) é limite superior de pior caso. Espaço auxiliar O(n).",
    6: "A série principal reúne 43 entradas de n=4 a 9: seis vazias, 30 parciais, seis completas e uma impossível. As quatro implementações usam os mesmos arquivos. O protocolo tem três aquecimentos e 15 tempos por combinação; leitura e impressão ficam fora do cronômetro.",
    7: "O gráfico mostra as médias de 15 execuções nos tabuleiros vazios n=4 a 9, em log10 de milissegundos. As quatro versões contam as mesmas soluções. A série de seis tamanhos ajuda a comparar o crescimento observado, mas não prova sozinha um limite assintótico.",
    8: "Para força bruta em tabuleiros vazios, o gráfico divide o tempo médio por n·n!. A razão fica aproximadamente estável no intervalo medido, compatível com Θ(n·n!), sem constituir prova assintótica.",
    9: "No tabuleiro vazio n=9, as médias ± desvios-padrão são: Python, força bruta 1.145,470±94,008 ms e backtracking 10,279±0,373 ms; C++, 65,845±4,074 ms e 0,551±0,033 ms. Todas contam 352 soluções. As razões entre médias são 111,4× e 119,5× neste ambiente.",
    10: "Esta série dobra n de 6 a 192 mantendo seis linhas livres. A força bruta visita 6! folhas e confere n linhas em cada uma, portanto Θ(n·6!)=Θ(n) neste parâmetro controlado. Ela é distinta dos tabuleiros vazios, em que m=n.",
    11: "O bônus mede alocações instrumentadas nas seis entradas geométricas: tracemalloc em Python e operator new em C++. As escalas são próprias de cada linguagem. Os contadores não representam a RAM total nem incluem integralmente a pilha recursiva.",
    12: "Decidir se um tabuleiro vazio de N-rainhas tem solução está em P. O experimento conta soluções. Decidir se uma entrada parcial pode ser completada é NP-completo; contar completações é #P-completo. São problemas relacionados, mas distintos.",
    13: "O backtracking evita expandir ramos que já violam coluna ou diagonal. No n=9 vazio, os ganhos observados foram 111,4× em Python e 119,5× em C++; esses tempos não mudam, por si, a classe assintótica do algoritmo. A versão publicada deve ser comparada ao commit correspondente.",
}


def qname(namespace: str, local: str) -> str:
    return f"{{{namespace}}}{local}"


def slide_parts(archive: zipfile.ZipFile) -> list[str]:
    rels = ET.fromstring(archive.read("ppt/_rels/presentation.xml.rels"))
    relationship_targets = {item.get("Id"): item.get("Target") for item in rels}
    presentation = ET.fromstring(archive.read("ppt/presentation.xml"))
    parts = []
    for item in presentation.findall(".//p:sldId", NS):
        target = relationship_targets[item.get(qname(R_NS, "id"))]
        parts.append(posixpath.normpath(posixpath.join("ppt", target)))
    return parts


def notes_for_slide(archive: zipfile.ZipFile, slide_part: str) -> str | None:
    rel_part = posixpath.join(posixpath.dirname(slide_part), "_rels",
                              posixpath.basename(slide_part) + ".rels")
    if rel_part not in archive.namelist():
        return None
    relationships = ET.fromstring(archive.read(rel_part))
    for item in relationships:
        if item.get("Type", "").endswith("/notesSlide"):
            return posixpath.normpath(posixpath.join(posixpath.dirname(slide_part),
                                                     item.get("Target")))
    return None


def set_note_text(xml_bytes: bytes, content: str) -> bytes:
    root = ET.fromstring(xml_bytes)
    body_shapes = []
    for shape in root.iter(qname(P_NS, "sp")):
        placeholder = shape.find(
            f"./{qname(P_NS, 'nvSpPr')}/{qname(P_NS, 'nvPr')}/{qname(P_NS, 'ph')}"
        )
        if placeholder is not None and placeholder.get("type") == "body":
            body_shapes.append(shape)
    if len(body_shapes) != 1:
        raise ValueError(f"esperava uma área de notas, encontrei {len(body_shapes)}")
    text_body = body_shapes[0].find(qname(P_NS, "txBody"))
    if text_body is None:
        raise ValueError("área de notas sem corpo de texto")
    paragraphs = text_body.findall(qname(A_NS, "p"))
    paragraph = paragraphs[0] if paragraphs else ET.SubElement(text_body, qname(A_NS, "p"))
    for child in list(paragraph):
        if child.tag != qname(A_NS, "pPr"):
            paragraph.remove(child)
    for extra in paragraphs[1:]:
        text_body.remove(extra)
    run = ET.SubElement(paragraph, qname(A_NS, "r"))
    run_properties = ET.SubElement(run, qname(A_NS, "rPr"))
    run_properties.set("lang", "pt-BR")
    text_node = ET.SubElement(run, qname(A_NS, "t"))
    text_node.text = content
    end_properties = ET.SubElement(paragraph, qname(A_NS, "endParaRPr"))
    end_properties.set("lang", "pt-BR")
    return ET.tostring(root, xml_declaration=True, encoding="UTF-8")


def update_notes(source_path: Path, output_path: Path) -> tuple[int, list[int], set[str]]:
    if not source_path.is_file():
        raise FileNotFoundError(source_path)
    if source_path.resolve() == output_path.resolve():
        raise ValueError("a saída não pode sobrescrever o PowerPoint de origem")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(suffix=".pptx", dir=output_path.parent)
    os.close(descriptor)
    temp_path = Path(temp_name)
    updated_parts: set[str] = set()
    updated_slides: list[int] = []
    try:
        with zipfile.ZipFile(source_path, "r") as source, zipfile.ZipFile(temp_path, "w") as dest:
            parts = slide_parts(source)
            if len(parts) != 13:
                raise ValueError(f"esperava 13 slides, encontrei {len(parts)}")
            for index, slide_part in enumerate(parts, 1):
                note_part = notes_for_slide(source, slide_part)
                if note_part is None:
                    continue
                if index not in NOTES:
                    raise ValueError(f"nota inesperada no slide {index}")
                updated_parts.add(note_part)
                updated_slides.append(index)
            if len(updated_slides) != 10:
                raise ValueError(f"esperava 10 notas existentes, encontrei {updated_slides}")

            for info in source.infolist():
                data = source.read(info.filename)
                if info.filename in updated_parts:
                    slide_index = next(
                        index for index, slide_part in enumerate(parts, 1)
                        if notes_for_slide(source, slide_part) == info.filename
                    )
                    data = set_note_text(data, NOTES[slide_index])
                dest.writestr(copy(info), data)

        with zipfile.ZipFile(source_path, "r") as source, zipfile.ZipFile(temp_path, "r") as dest:
            if source.namelist() != dest.namelist():
                raise ValueError("a lista de partes do PowerPoint mudou")
            for name in source.namelist():
                if name not in updated_parts and source.read(name) != dest.read(name):
                    raise ValueError(f"parte fora das notas foi modificada: {name}")
        os.replace(temp_path, output_path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise
    return len(updated_parts), updated_slides, updated_parts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("deck", nargs="?", type=Path, default=DEFAULT_DECK,
                        help="PPTX de 13 slides usado como origem")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help="PPTX intermediário de saída (padrão: build/generated/presentation)")
    args = parser.parse_args()
    count, slides, _ = update_notes(args.deck, args.output)
    print(f"notas atualizadas: {count}; slides com notas: {slides}")
    print("slides 4, 8 e 10 não têm notas no arquivo e permanecem sem notas")
    print(f"prévia intermediária: {args.output}")


if __name__ == "__main__":
    main()
