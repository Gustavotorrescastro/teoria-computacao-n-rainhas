# Matriz de conformidade — N-rainhas

## Escopo e critério de evidência

Esta matriz compara o código e os dados validados disponíveis com o relatório, o guia e a apresentação. “Validado localmente” significa que os arquivos passaram pelas verificações listadas aqui; não significa que a branch principal do GitHub já foi atualizada ou que as contribuições individuais foram confirmadas pela equipe.

Os benchmarks **não foram executados novamente nesta revisão**. As medições mantidas são as da rodada validada fornecida com o projeto. Os scripts de validação recalcularam os agregados a partir dos CSVs brutos sem sobrescrevê-los.

## Requisitos do enunciado

| Requisito | Evidência | Resultado |
|---|---|---|
| 1. Dois algoritmos em duas linguagens | `src/python/nqueens.py` e `src/cpp/nqueens.cpp`; sete testes em `tests/` | **Atendido localmente.** Força bruta por permutações e backtracking com poda estão implementados em Python e C++. Os testes incluem tabuleiros conhecidos, entradas parciais e inválidas e comparação C++/Python nas entradas geradas. |
| 2. O, Ω e Θ com justificativas | Relatório, seções 2 e 6; guia DOCX, seção de complexidade | **Atendido.** Para `m` linhas livres, força bruta enumera `m!` permutações e percorre `n` linhas em cada folha, dando Θ(n·m!) em entradas válidas. Em tabuleiro vazio, isso se torna Θ(n·n!). Para backtracking, o relatório expressa o custo em função de `A`, as tentativas efetivamente feitas, com Θ(n + A); não assume que poda implique tempo polinomial. |
| 3. Melhor, pior e caso médio | Relatório, seção 3; guia DOCX | **Atendido com ressalva correta.** Entrada completa e consistente tem custo Θ(n) após a leitura; o pior caso de backtracking é limitado por O(n·n!). O caso médio depende da distribuição das instâncias e é descrito a partir da amostra, não como uma garantia universal. |
| 4. Aplicabilidade prática | Relatório, seção 4; resultados de limite em `data/results/limit_60s.json` | **Atendido.** A discussão distingue entradas completas, parciais e vazias e comenta a utilidade da poda. A sondagem registrada concluiu `n=10` em 8,9308472 s e atingiu o limite de 60 s em `n=11`; são observações de uma execução, não médias. |
| 5. Metodologia experimental | Relatório, seção 5; `data/inputs/manifest.json`; metadados em `data/results/*environment.json` | **Atendido e reproduzível.** 43 entradas principais, semente 20261116, três aquecimentos e 15 medições por combinação. A leitura e a saída ficam fora do cronômetro. A série geométrica e a medição de memória usam manifestos próprios. |
| 6. Gráficos teóricos e experimentais | Relatório, seção 6; `scripts/build_artifacts.py`; CSVs em `data/results/` | **Atendido.** O relatório compara tempos, operações e medidas de memória. A razão `T(n)/(n·n!)` é calculada com médias do tabuleiro vazio. A série geométrica mantém seis linhas livres (`m=6`) e é identificada separadamente; ela não é apresentada como a série fatorial de tabuleiros vazios. |
| 7. Reflexão sobre P × NP | Relatório, seção 7 e referência a Gent, Jefferson e Nightingale (2017); slides finais | **Atendido.** O texto separa decisão de N-rainhas vazio, completamento com posições fixas e contagem de completamentos. Os tempos medidos não são usados como prova de classificação de complexidade. |

## Auditoria código ↔ dados ↔ documentos

### Código e dados

- A força bruta monta permutações das colunas livres e verifica conflitos diagonais somente nas folhas completas. O laço de verificação percorre todas as linhas, mesmo depois de achar um conflito.
- O backtracking consulta coluna e as duas diagonais antes de avançar; ao retornar da recursão, desfaz as marcações.
- As quatro combinações usam os mesmos arquivos de entrada. O teste de equivalência executa Python e C++ nas entradas geradas, e o validador confere contagens consistentes nos CSVs.
- O validador aprovado recalculou média, desvio-padrão, mediana e extremos a partir dos brutos: 2.580 amostras principais, 360 geométricas e 360 de memória; total 3.300. Foram conferidos 172, 24 e 24 agregados, respectivamente.
- Para `n=9` vazio, os CSVs registram 352 soluções em todas as variantes: Python força bruta 1.145,4704 ± 94,0081 ms; Python backtracking 10,27928 ± 0,37297 ms; C++ força bruta 65,84526 ± 4,07423 ms; C++ backtracking 0,551087 ± 0,033171 ms. Cada agregado usa 15 amostras.
- O metadado da rodada registra Windows 11 build 10.0.26200, Python 3.13.7, g++ 15.2.0, CPU Intel Core 7 150U e 34.029.125.632 bytes de RAM.
- Os testes foram executados em Python 3.13.7 e compilador g++ 15.2.0. A validação local passou; os benchmarks completos não foram repetidos.

### Relatório e guia

- O relatório PDF disponível tem nove páginas, sem folha de capa separada; a primeira página traz título, equipe e resumo. Foram conferidos os sete itens, a análise de complexidade, os gráficos, a discussão P × NP, referências e declaração de IA.
- O PDF disponível foi alinhado à cópia editável com uma ressalva no rodapé da página 8: as responsabilidades registradas são uma proposta e devem ser confirmadas. Nenhum nome ou atribuição foi alterado. As páginas 1–7 e 9 ficaram pixel a pixel iguais à cópia original do PDF na renderização a 96 dpi.
- O DOCX do relatório explicita que as atribuições não foram confirmadas. O PDF preserva a versão sem capa solicitada; os dois arquivos têm pequenas diferenças editoriais e de abertura, portanto não são cópias binárias nem palavra por palavra idênticas.
- O guia DOCX atual cobre representação do tabuleiro, as funções implementadas, força bruta, backtracking, complexidades, casos de execução, medições, estatísticas, séries geométrica e de 60 segundos, memória, P × NP, perguntas de defesa e mapa dos 13 slides.
- **Pendente:** o PDF atual do guia não estava disponível. O PDF antigo encontrado tem resultados desatualizados e foi excluído da entrega; não foi convertido nem apresentado como atual.

### Apresentação

- A apresentação final contém 13 slides. As notas foram inspecionadas nos 13: dez contêm texto e três não tinham notas. As notas remanescentes não incluem tempos antigos, o limite antigo de 29,43 s, a regra de sete minutos ou uma divisão obrigatória por apresentador.
- O PPTX foi renderizado novamente. A comparação com a cópia de 13 slides imediatamente anterior à edição das notas resultou em 13/13 slides pixel a pixel iguais. O PDF contém 13 páginas e corresponde visualmente aos slides.
- O PDF da apresentação é rasterizado, com uma imagem por página; o PowerPoint continua editável. A igualdade visual foi conferida, mas o PDF não preserva objetos de texto editáveis.
- Os scripts de geração de relatório, apresentação e notas salvam em `build/generated/`; `scripts/package.py` grava em `build/packages/`. Nenhum deles substitui os arquivos aprovados em `docs/`.
- O mandato nomeava `Apresentacao_N_Rainhas_Equipe_Revisada(1).pptx`; esse arquivo com sufixo `(1)` não foi localizado. Foi utilizada a cópia revisada de 13 slides já existente no projeto. A equivalência do nome ausente com essa cópia não pode ser confirmada apenas pelos arquivos disponíveis.

## Arquivos esperados que não estavam disponíveis

- `Guia_de_Estudos_N_Rainhas_Equipe_Atualizado.pdf`: somente o DOCX atual foi encontrado. A geração segura do PDF depende de um conversor de DOCX que não está instalado nem incluído no runtime disponível.
- `Relatorio_N_Rainhas_Sem_Capa_Responsabilidades.pdf`: o arquivo exato não foi encontrado; foi usada a versão disponível `Relatorio_N_Rainhas.pdf`, sem capa separada e com os requisitos descritos acima.
- `Apresentacao_N_Rainhas_Equipe_Revisada(1).pptx`: o nome exato não foi encontrado; foi usada a versão revisada de 13 slides disponível no projeto.

## Estado de publicação

A validação aqui registrada é local. A branch principal remota só poderá ser considerada sincronizada depois de o Pull Request ser revisado e integrado. Nenhum merge foi realizado nesta revisão. As atribuições de trabalho permanecem propostas até confirmação humana dos integrantes.
