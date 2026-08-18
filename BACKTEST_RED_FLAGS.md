# BACKTEST_RED_FLAGS — os sinais estavam acesos antes do evento?

Executado por `scripts/18_backtest.py` em 18/08/2026. Resultados brutos em
`data/analytic/backtest_resumo.csv` e `backtest_detalhe.csv` (6.164 observações
veículo-mês).

## Desenho

- **Casos positivos**: veículos ligados a eventos confirmados por fonte oficial
  (`casos_regulatorios.csv`), vinculados por **CNPJ do prestador** ou do fundo.
- **Controles negativos com pareamento POR VEÍCULO**: para cada positivo, até 3
  controles do mesmo tipo (Fundo/Classe) com patrimônio entre 0,5x e 2x o do
  positivo, na mesma competência, amostragem determinística. Pareamento por
  variáveis de modelo de negócio (exclusivo, cotistas de interesse único) é
  **deliberadamente evitado**: são os próprios sinais S5/S6 — parear por elas
  absorveria o contraste que se quer medir.
- **Higiene do controle como invariante de código**: veículo positivo em
  QUALQUER evento da biblioteca fica fora de TODOS os pools de controle, e o
  script **aborta** (assertiva) se a regra for violada — a garantia vale para
  qualquer via futura de ingestão de eventos.
- **Anti-vazamento**: para um evento em T, só se lê competência ≤ T−1 mês.
  Janela observada: 12 meses.
- **Critério de disparo**: o veículo "acendeu" se o sinal apareceu em qualquer
  mês da janela. Ausência de dado ⇒ *não avaliável* (entra na cobertura),
  jamais "não disparou".
- **Lift** = taxa de disparo em positivos ÷ taxa em controles. Lift 1,0
  significa que o sinal não distingue nada.

## Resultado — CR023: liquidação extrajudicial do administrador (BCB, 15/01/2026)

151 veículos administrados pela entidade na competência anterior ao evento;
416 controles pareados por veículo (mesmo tipo, PL 0,5x–2x). Sob o pareamento
anterior — faixa única global de PL — as conclusões eram as mesmas: a troca de
desenho moveu os lifts em menos de 0,4 e não alterou quais sinais são
significativos, o que é evidência de robustez do resultado ao critério de
pareamento.

<!-- BACKTEST:TABELA:INICIO -->
| Sinal | Positivos | Controles | **Lift** | **Fisher (p)** | Não avaliáveis | Antecedência positivos | Antecedência controles |
|---|---:|---:|---:|---:|---:|---:|---:|
| S5 — estrutura fechada (cotistas de interesse único) | 95,4% | 21,4% | **4,46** | **< 0,0001** | 0 | 4 m | 11 m |
| S3 — subordinação abaixo de 5% | 83,3% | 21,7% | **3,85** | **< 0,0001** | 6 | 0 m | 0 m |
| S1 — inadimplência ≈ zero com cedente concentrado | 27,6% | 16,2% | **1,70** | **0,041** | 299 | 2 m | 10 m |
| S4 — variação abrupta de patrimônio | 42,3% | 37,3% | **1,13** | **0,166** | 21 | 8 m | 6 m |
| S6 — cedente único acima de 80% | 30,5% | 50,2% | **0,61** | **0,998** | 263 | 1 m | 8 m |
| S2 — rolagem (recompra + substituição) | 0,0% | 8,0% | **0,00** | **1,000** | 96 | — | 7 m |

Leitura obrigatória da antecedência: em 5 dos 6 sinais **os controles acendem mais cedo que os positivos** — a coluna mede em que ponto da janela de 12 meses o sinal costuma aparecer, **não** antecipação do evento. Nenhuma leitura preditiva é autorizada por ela.
<!-- BACKTEST:TABELA:FIM -->

A tabela acima é **regenerada automaticamente** por `scripts/18_backtest.py` a
partir de `backtest_resumo.csv` — o documento não pode divergir do CSV que o
sustenta. O p é de um teste exato de Fisher unilateral na direção esperada
(positivos disparam mais que controles). "Não avaliáveis" são veículos sem o
dado necessário — contados à parte, jamais somados aos que não dispararam.
As duas colunas de antecedência são publicadas juntas deliberadamente: em 5
dos 6 sinais os controles acendem **antes** dos positivos, o que demonstra que
a métrica descreve posição na janela de observação, não capacidade de
antecipar o evento.

Higiene do grupo de controle: veículos positivos em **qualquer** evento da
biblioteca são excluídos de **todos** os pools de controle — sem isso, um
positivo de um evento serviria de "controle sem evento conhecido" para outro.

## Leitura honesta destes números

**Dois sinais discriminam, dois não discriminam e dois funcionam ao contrário.**

- **S5 e S3 têm lift alto — e é aí que mora a maior armadilha do backtest.**
  "Cotistas de interesse único" e "subordinação baixa" descrevem o *modelo de
  negócio* dos veículos daquele administrador, que operava predominantemente
  estruturas fechadas. Um sinal pode ter lift alto por descrever a natureza do
  portfólio e não por antecipar o evento. **Não se pode afirmar poder preditivo
  a partir deste resultado.** O que se pode dizer é mais modesto e ainda útil:
  a carteira do administrador liquidado era estruturalmente mais fechada e menos
  capitalizada em subordinação que o mercado comparável — e isso era observável
  em dado público meses antes da liquidação.
- **S6 tem lift 0,61**: disparou *menos* nos casos positivos que nos controles.
  Como sinal isolado de risco, é contraproducente neste evento. Mantê-lo com
  peso positivo num score agregado degradaria o resultado.
- **S2 não disparou em nenhum positivo.** A rolagem de créditos, que é o
  mecanismo clássico de ocultação de atraso, não aparece neste caso — o que é
  coerente com o fato de o evento ter sido de natureza societária e de conduta
  do prestador, não de deterioração de carteira.
- **Significância**: apenas S5, S3 (p < 0,0001) e S1 (p = 0,041) rejeitam a
  hipótese de que positivos e controles disparam na mesma proporção. S4
  (p = 0,166), S6 (p = 0,998) e S2 (p = 1,000) não rejeitam — e S6 e S2 apontam
  na direção contrária. Publicar lift sem o p induziria a erro: um lift de 1,13
  sobre 149 veículos não é distinguível de ruído.
- **Cobertura desigual entre sinais**: S1 e S6 só foram avaliáveis para ~38% dos
  veículos (dependem de cedente declarado), enquanto S5 cobre 100%. Comparar
  taxas de disparo entre sinais com coberturas tão distintas é ilegítimo — cada
  taxa vale apenas contra o seu próprio grupo de controle.
- **S1 é o único sinal com lastro documental externo**: no PAS CVM
  19957.006858/2019-25, a própria defesa atribuiu ao "reduzidíssimo histórico de
  inadimplências" a demora na detecção. O lift de 1,70 é modesto, mas a
  cobertura é baixa (38%) — o sinal só é avaliável onde há cedente declarado.

## Falso negativo documentado — CR024: stop order (CVM, 20/05/2026)

Três veículos vinculados. Dos seis sinais, **quatro foram avaliáveis e nenhum
disparou**; dois (S1 e S6) ficaram **não avaliáveis** por ausência de cedente
declarado — e "não avaliável" não é "não disparou". O painel não teria
antecipado esse evento. Registrado deliberadamente: um backtest que só mostra
acertos não é backtest.

## Caso não testável — CR022: liquidação de banco (BCB, 18/11/2025)

Nenhum veículo foi vinculado por denominação. É uma falha do *método de vínculo*
(busca por nome), não do sinal — e confirma a decisão de migrar o casamento para
CNPJ de prestador e vínculo societário documentado.

## Limitações que impedem declarar a metodologia validada

1. **Um único evento com vínculo robusto.** Um caso não sustenta inferência
   estatística. Intervalos de confiança seriam largos a ponto de inúteis.
2. **Confusão entre característica estrutural e precursor**, descrita acima.
   O pareamento por **tipo de veículo + faixa de PL por positivo** foi
   implementado (e não mudou as conclusões); pareamento por **público-alvo e
   segmento econômico da carteira** segue pendente — essas dimensões não são
   diretamente observáveis no informe e exigiriam o registro ou classificação
   própria. E permanece a advertência central: parear pelas variáveis que SÃO
   os sinais (estrutura fechada, cedente único) eliminaria o contraste — parte
   do confundimento é irredutível com um único evento.
3. **Eventos históricos fora de alcance.** Os casos de 2012-2016 (Cruzeiro do
   Sul, Silverado) antecedem a existência de várias tabelas do informe: a de
   concentração de devedores começa em 2025, os campos de cedente em nov/2019.
   Não é possível reconstruir o conjunto completo de sinais para eles.
4. **Viés de sobrevivência e de reporte.** Veículos que param de informar sumem
   da série; a interrupção do reporte é, ela própria, informação — e passou a
   ser tratada como sinal separado depois deste exercício.
5. **Sem amostra fora do tempo.** Todos os eventos utilizáveis são recentes;
   não há partição temporal treino/teste.

## Conclusão

A metodologia permanece **EXPERIMENTAL**. O backtest não autoriza afirmar que os
sinais preveem eventos. Autoriza três coisas: (i) descartar S6, S2 e S4 como sinais
isolados de risco no score agregado, por não atingirem significância; (ii) manter S5, S3 e S1 como indicadores
descritivos de estrutura, com a advertência de que descrevem modelo de negócio;
(iii) exigir que qualquer publicação de score venha acompanhada de cobertura,
materialidade e força da evidência — nunca de um número único.

Próximo passo para validação real: ampliar a biblioteca de eventos com vínculo
por CNPJ (não por nome), incluir eventos de deterioração de carteira além dos de
conduta do prestador, e repetir com pareamento por segmento.
