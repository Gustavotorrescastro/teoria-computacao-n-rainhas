# Histórico de revisão — N-rainhas

Este registro separa correções de código, atualização de medições e melhorias de explicação. Ele descreve alterações verificáveis no repositório e nos documentos; não atribui autoria de algoritmos, experimentos ou resultados a integrantes específicos.

## Ponto de partida

A branch pública foi auditada no commit `9010902` (`Remove artefatos de entrega do repositorio`). O código já continha as quatro implementações de N-rainhas e os resultados experimentais anteriores. Não foi necessário reescrever força bruta nem backtracking.

Na versão publicada anterior, a tabela principal de `n=9` vazio registrava médias de 2.216,20116 ms e 20,05587 ms em Python, e 128,8204 ms e 1,07787 ms em C++, respectivamente para força bruta e backtracking. A sondagem antiga registrava 29,4344669 s para força bruta Python em `n=10`. Esses valores também apareciam em notas internas antigas da apresentação.

## Correções e acréscimos técnicos

- Foram mantidas as implementações existentes. A revisão do código confirmou que a força bruta testa diagonais nas folhas completas e que o backtracking poda conflitos e desfaz marcações ao retornar da recursão.
- O teste de corretude ganhou um oráculo independente por permutações para tabuleiros parciais pequenos e testes de rejeição de entradas inválidas em Python e C++. As verificações incluem contagens conhecidas e comparação entre linguagens.
- Foi incluído `scripts/validate_results.py` para conferir os manifestos, as amostras brutas e o recálculo de média, desvio-padrão, mediana e extremos.
- `scripts/benchmark.py` passou a registrar detalhes de hardware; `scripts/benchmark_geometric.py` passou a salvar metadados próprios para a série geométrica.
- Os geradores foram isolados em `build/generated/`, e o empacotador passou a gravar em `build/packages/`. Isso impede que uma geração automática confunda rascunhos com os documentos aprovados em `docs/`.
- O utilitário de notas do PowerPoint também foi ajustado: agora grava uma prévia em `build/generated/presentation/` e recusa usar o mesmo arquivo como origem e destino.
- O README agora documenta como compilar e executar as quatro versões, rodar os testes, validar dados existentes, reproduzir benchmarks em um checkout descartável e localizar os documentos.

## Atualização de medições

Os CSVs atuais correspondem à rodada validada fornecida com o pacote técnico do projeto. Os benchmarks **não foram executados novamente nesta revisão**. Por isso, os valores a seguir são registros da rodada fornecida, validados pelo recálculo dos agregados, e não novas medições do computador usado para esta auditoria.

| Tabuleiro vazio, `n=9` | Média ± desvio-padrão (ms) | Soluções |
|---|---:|---:|
| Python — força bruta | 1.145,4704 ± 94,0081 | 352 |
| Python — backtracking | 10,27928 ± 0,37297 | 352 |
| C++ — força bruta | 65,84526 ± 4,07423 | 352 |
| C++ — backtracking | 0,551087 ± 0,033171 | 352 |

Cada valor agregado usa 15 medições. O novo registro de limite informa 8,9308472 s para uma execução em `n=10` e timeout após 60 s em `n=11`; o valor antigo de 29,434 s não foi reaproveitado como medição atual.

A rodada contém 2.580 amostras principais, 360 da série geométrica e 360 da série de memória. A série geométrica mantém seis linhas livres em todos os tamanhos, portanto representa Θ(n·6!) para força bruta; ela permanece separada da série fatorial de tabuleiros vazios.

## Relatório e guia

- O relatório de nove páginas disponível foi organizado em `docs/entrega/` junto da cópia editável. Ele mantém os sete itens, a análise teórica, gráficos, resultados, referência acadêmica e declaração de IA.
- O DOCX explicita que a tabela de responsabilidades não foi confirmada por cada integrante. Para alinhar essa informação no PDF, foi acrescentada uma ressalva na página 8, sem mudar nomes ou atribuições. A comparação da renderização a 96 dpi mostrou que só a página 8 mudou; as páginas 1–7 e 9 permaneceram idênticas.
- A distribuição de responsabilidades permanece proposta e depende de confirmação humana. Esta revisão não declara contribuições individuais como fatos.
- O guia DOCX atual foi organizado em `docs/apoio/`. Ele amplia a explicação didática das implementações e inclui o mapa dos 13 slides e perguntas de defesa.
- O PDF atual do guia não estava disponível. Um PDF antigo encontrado contém números anteriores, então não foi incluído nem renomeado como se fosse a versão atual. Também não foi instalado um conversor de DOCX nesta revisão.

## Apresentação

- Foi mantida a apresentação revisada de 13 slides e a identidade visual existente. A única mudança no PPTX foi substituir notas internas antigas por explicações técnicas neutras; não foram atribuídos slides nem tempos a apresentadores nas notas.
- A inspeção programática cobriu os 13 slides. Dez têm notas; os slides 4, 8 e 10 não tinham notas. Nenhuma nota remanescente contém os valores antigos, o limite de sete minutos ou a divisão anterior entre quatro pessoas.
- O PPTX foi renderizado novamente e comparado com a cópia imediatamente anterior à edição das notas: 13 de 13 slides ficaram pixel a pixel iguais. O PDF associado tem 13 páginas correspondentes, geradas como imagens de cada slide.
- O PDF preserva a aparência, mas é rasterizado; o PowerPoint permanece editável. O arquivo com o nome exato `Apresentacao_N_Rainhas_Equipe_Revisada(1).pptx` não estava disponível; foi usada a versão revisada de 13 slides que já existia no projeto.

## Verificações executadas

```powershell
g++ -O2 -std=c++17 -Wall -Wextra -o build/nqueens.exe src/cpp/nqueens.cpp
g++ -O2 -std=c++17 -Wall -Wextra -o build/memory_profile.exe src/cpp/memory_profile.cpp
py -3.13 -m unittest discover -s tests -v
py -3.13 scripts/validate_results.py
```

Resultado: ambos os executáveis compilaram; os sete testes passaram; o validador conferiu 2.580, 360 e 360 amostras e 172, 24 e 24 agregados. O validador apenas leu os arquivos canônicos. Os benchmarks completos não foram repetidos.

## Pendências e limites

- O PDF atual do guia precisa ser fornecido pela equipe ou produzido com um conversor compatível e verificado visualmente.
- O nome exato do PowerPoint solicitado não foi localizado; a auditoria usou a apresentação revisada de 13 slides disponível no projeto.
- As responsabilidades da equipe precisam de confirmação humana antes de serem apresentadas como contribuições efetivamente realizadas.
- A principal remota só estará sincronizada após revisão e merge do Pull Request. Esta revisão não executou merge.
