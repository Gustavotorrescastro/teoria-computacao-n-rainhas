# N-rainhas: força bruta e backtracking em Python e C++

Projeto da disciplina **Teoria da Computação**, CESAR School. O programa conta todas as soluções para uma instância de N-rainhas com rainhas já fixadas ou sem posições prévias. São comparados dois algoritmos em Python e C++: força bruta por permutações e backtracking com poda.

## Estrutura

- `src/python/nqueens.py`: leitura de instâncias, força bruta, backtracking e interface de execução em Python.
- `src/cpp/nqueens.cpp`: as mesmas duas buscas em C++17.
- `src/cpp/memory_profile.cpp`: medição complementar de alocações dinâmicas em C++.
- `scripts/prepare_inputs.py`: 43 entradas principais: seis vazias, 30 parciais, seis completas e uma impossível.
- `scripts/prepare_memory_inputs.py`: seis instâncias geométricas com seis linhas livres.
- `scripts/benchmark.py`, `benchmark_geometric.py`, `benchmark_memory.py` e `find_60s_limit.py`: experimentos de tempo, memória e limite.
- `scripts/validate_results.py`: confere manifestos, entradas, amostras e estatísticas recalculadas dos CSVs.
- `scripts/update_presentation_notes.py`: produz uma cópia de prévia com notas corrigidas em `build/generated/presentation/`; não substitui o PowerPoint de origem.
- `tests/`: testes de referência, entradas inválidas, equivalência entre linguagens e perfil de memória.
- `data/inputs/`, `data/memory_inputs/` e `data/results/`: entradas, manifestos, medições brutas, agregados e metadados canônicos.
- `docs/entrega/`: relatório e apresentação final aprovados.
- `docs/apoio/`: guia de estudo editável.
- `build/generated/`: artefatos intermediários regeneráveis; não substituem os documentos em `docs/`.

## Requisitos

- Python 3.13 para reproduzir o ambiente registrado nos metadados de medição.
- `g++` com suporte a C++17.
- Para gerar gráficos e PDFs intermediários: `matplotlib`, `reportlab` e `Pillow`.
- Poppler (`pdftoppm`) apenas para renderizar PDFs durante uma inspeção visual.

Os CSVs existentes foram medidos em Windows 11, Python 3.13.7 e g++ 15.2.0 com `-O2 -std=c++17 -Wall -Wextra`. Validar os arquivos não altera esses resultados; repetir benchmarks grava novos resultados e substitui os arquivos correspondentes em `data/results/`.

## Compilar e executar as quatro versões

No PowerShell, a partir da raiz do repositório:

```powershell
New-Item -ItemType Directory -Force build | Out-Null
g++ -O2 -std=c++17 -Wall -Wextra -o build/nqueens.exe src/cpp/nqueens.cpp
g++ -O2 -std=c++17 -Wall -Wextra -o build/memory_profile.exe src/cpp/memory_profile.cpp
py -3.13 src/python/nqueens.py brute data/inputs/empty_n4.txt
py -3.13 src/python/nqueens.py backtracking data/inputs/empty_n4.txt
build/nqueens.exe brute data/inputs/empty_n4.txt
build/nqueens.exe backtracking data/inputs/empty_n4.txt
```

Cada saída de tempo contém contagem de soluções, operações e nanossegundos. A leitura do arquivo ocorre antes do cronômetro. Os executáveis aceitam uma entrada com `n k` e, em seguida, `k` pares de índices `linha coluna`, começando em zero.

## Testes e validação dos resultados existentes

```powershell
py -3.13 -m unittest discover -s tests -v
py -3.13 scripts/validate_results.py
```

Os testes esperam que ambos os executáveis de C++ acima estejam compilados. O validador não executa benchmarks: recalcula média, desvio-padrão, mediana e extremos a partir dos dados brutos e verifica 2.580 amostras principais, 360 geométricas e 360 de memória.

## Reproduzir os experimentos

Execute os comandos abaixo em um checkout descartável com o mesmo código. Os geradores de entradas e os benchmarks sobrescrevem arquivos; preserve os CSVs canônicos antes de iniciar uma nova rodada.

```powershell
py -3.13 scripts/prepare_inputs.py
py -3.13 scripts/benchmark.py --repetitions 15 --warmup 3
py -3.13 scripts/prepare_memory_inputs.py
py -3.13 scripts/benchmark_geometric.py
py -3.13 scripts/find_60s_limit.py
py -3.13 scripts/benchmark_memory.py --repetitions 15
py -3.13 scripts/validate_results.py
```

O experimento principal usa as mesmas 43 entradas para quatro combinações, três aquecimentos e 15 medições por combinação. A semente das entradas parciais é `20261116`. O experimento geométrico e o de memória usam separadamente `n=6,12,24,48,96,192`, com seis linhas livres. Como `m=6` permanece fixo nessa série, força bruta tem custo Θ(n·6!), distinto da série de tabuleiros vazios, cujo custo é Θ(n·n!). O limite de 60 segundos é uma sondagem pontual, não entra nas médias.

Os resultados de referência para `n=9` vazio são 1.145,470 ms para força bruta em Python, 10,279 ms para backtracking em Python, 65,845 ms para força bruta em C++ e 0,551 ms para backtracking em C++; cada combinação conta 352 soluções. Esses valores documentam a rodada aprovada e não devem ser substituídos por uma execução local sem revisão explícita.

## Artefatos e documentos finais

`python scripts/build_artifacts.py` cria somente materiais intermediários em `build/generated/figures/`, `build/generated/pdf/` e `build/generated/presentation/`. Esses PDFs e a apresentação sintética gerada pelo script não são os documentos aprovados e não substituem arquivos de `docs/`.

`py -3.13 scripts/update_presentation_notes.py` também grava uma prévia em `build/generated/presentation/`. Para atualizar outro arquivo, passe o caminho de origem e `--output`; a origem nunca pode ser usada como destino.

`python scripts/package.py` cria um ZIP técnico de código, dados, testes e scripts em `build/packages/`. O pacote não inclui nem sobrescreve documentos aprovados.

Documentos disponíveis no repositório:

- `docs/entrega/Relatorio_N_Rainhas.pdf` e `Relatorio_N_Rainhas.docx`.
- `docs/entrega/Apresentacao_N_Rainhas.pptx` e `Apresentacao_N_Rainhas.pdf`.
- `docs/apoio/Guia_Estudos_N_Rainhas.docx`.

O PDF definitivo do guia não estava disponível no ambiente usado para esta revisão; por isso ele não é listado como entregue. A matriz de conformidade e o histórico de revisão estão em `docs/MATRIZ_CONFORMIDADE.md` e `docs/HISTORICO_REVISAO_N_RAINHAS.md`.

## Declaração de uso de IA

O relatório declara o uso de IA generativa durante implementação, revisão técnica, preparação de experimentos, análise dos resultados e organização dos materiais. As contribuições individuais registradas no relatório permanecem propostas informadas anteriormente e não foram confirmadas nesta auditoria. Os integrantes devem compreender o código e os resultados apresentados.
