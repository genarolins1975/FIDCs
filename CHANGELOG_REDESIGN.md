# CHANGELOG_REDESIGN — reconstrução do Panorama FIDC Brasil

Ciclo executado em 18/08/2026, a partir do diagnóstico de `AUDITORIA_PAINEL_FIDC.md`
(6 achados críticos, 8 altos, 4 médios, 1 baixo). Cada item abaixo indica o achado
que resolve e o teste que comprova a correção.

## Camada de dados

| Mudança | Achado | Teste de validação |
|---|---|---|
| Carga das 4 tabelas do informe que nunca haviam sido processadas: **VIII** (25 maiores devedores), **IX** (taxas de desconto e juros), **X_6** (desempenho esperado × realizado), **X_7** (garantias) | Crítico 1 | `MATRIZ_FONTES_COBERTURA.csv`: 18 de 18 tabelas carregadas |
| Carga da tab **III** (passivo), habilitando a identidade contábil | Crítico 1 | Ativo − Passivo = PL: **0 divergências** em 4.327 veículos |
| Ausência deixa de virar zero em circularidade, HHI e ligação de emissor | Crítico 3 | `auditoria/trilha_dados_nulos.md`: 15 ocorrências classificadas; ilegítimos corrigidos |
| Dedup de gestor aplicado **depois** da união dos regimes | novo (encontrado na reconstrução) | cobertura da lente 1 caiu de 199% para **100,0%** |
| `SCHEMA_CHANGELOG.md` gerado por comparação de cabeçalhos 2013-2026 | Alto (schema) | 17 mudanças de layout detectadas + 4 quebras regulatórias documentadas |
| Diagnóstico da competência incompleta | Médio (data-base) | 232 veículos e R$ 73,3 bi ausentes em jul/2026; *same-store* cresce 2,0% |

## Camada analítica

| Mudança | Achado | Teste de validação |
|---|---|---|
| **Nove lentes de exposição** substituem o ranking único, cada uma com definição, numerador, denominador, unidade, cobertura e "o que **não** significa" | Crítico 5 | `lentes_catalogo.csv`; lentes 1 e 2 cobrem 100% do PL, lente 4 declara 29,4%, lente 5 declara 69,3% |
| Concentração por devedor passa a existir (antes declarada impossível) | Crítico 1 | tab VIII cobre **79,7% do estoque**; mediana do maior devedor 17,9%; 877 veículos com maior devedor acima de 50% |
| **46 sinais em 8 pilares** substituem os 5 sinais anteriores, com limiar percentílico calculado sobre o próprio mercado | Alto (score) | `rf2_catalogo.csv` registra percentil, n e mediana de cada limiar |
| Score decomposto em 6 dimensões; cobertura < 50% ⇒ **não classificável** | Alto (score) | 1.099 veículos não classificáveis; nenhum rotulado baixo risco |
| **Backtest** com anti-vazamento e controles negativos | Alto (sem backtest) | 2 sinais descartados (lift 0,68 e 0,00); 1 falso negativo documentado |
| **Monitor de recuperação judicial** por CNPJ | ausente | 107 vínculos; DataJud **não retorna partes** — estado processual lido do marcador do art. 69 da Lei 11.101/2005 |
| Casamento por CNPJ substitui busca por substring de nome | Alto (RF6) | caso CR022 do backtest documenta a falha do método antigo |

## Camada de apresentação

| Mudança | Achado | Teste de validação |
|---|---|---|
| **Zero literal numérico** no gerador: todo valor vem de `painel_dados.json` | Crítico 4 | 36 indicadores com fórmula, fonte, campo, cobertura, status e confiança |
| **Gaveta de evidências** clicável em cada número | Alto (auditabilidade) | modal com valor exato, fórmula, tabela/campo, data-base, extração, cobertura e claim |
| Seis telas navegáveis com filtro e busca | Alto (navegação) | abas 1-6, busca por nome/CNPJ, exportação por cópia de CSV |
| "Cotistas" renomeado para **posições de cotistas** | Crítico 2 | rótulo e observação na gaveta declaram que não mede pessoas únicas |
| Cartão de grupo sob investigação substituído por descrição factual do vínculo, com status processual | Crítico 6 | tela 5 traz status processual por caso e advertência fixa |
| Blocos didáticos por tela ("como ler estes números") | Médio (didática) | 3 blocos expansíveis + notas por métrica |

## O que foi preservado

Painel canônico deduplicado, reconciliação com Medidas CVM/FIE (diferença zero em
99,0% do PL), saneamento de outlier documentado, manifesto com SHA-256, livro de
evidências, medida de circularidade por campo declarado e separação rigorosa de
papéis. Nada disso foi reescrito: resistiu à auditoria e continua sob teste.

## Correções factuais em material já publicado

- Caso **Union National**: eram **dois** processos, não um; administrador condenado
  a R$ 3 mi (três multas de R$ 1 mi) e custodiante a R$ 1,5 mi — valores antes
  subestimados.
- Caso **Silverado** identificado como o **PAS CVM 19957.006858/2019-25**, com a
  ressalva de que os prestadores foram condenados em algumas imputações e
  **absolvidos em outras**.
- Circularidade: o campo de cotas de FIDC-NP está **100% em branco** desde 2024;
  a medida usa apenas o campo de cotas de FIDC, e a lacuna passou a ser publicada.

## Rodada 3 — resposta à revalidação do auditor-espelho (18/08/2026, noite)

Veredito da revalidação: REPROVADO por margem estreita (média 7,5). Três
bloqueantes, todos corrigidos nesta rodada, com o teste que impede reincidência:

1. **Regra-mãe na Ficha do veículo.** 14 veículos não classificáveis (R$ 16 bi de
   PL) exibiam chip verde "nenhum disparado". A ficha agora publica linha fixa
   "Cobertura de dados" e, abaixo de 50%, chip neutro "cobertura insuficiente para
   concluir" — nunca o vocabulário de conformidade. Teste: `regra_mae_fichas` em
   `20_teste_formulas.py` (falha o build se ficha com cobertura < 50% não estiver
   rotulada "não classificável").
2. **Teste automático de fórmulas (a correção de classe).** `20_teste_formulas.py`
   recomputa CADA indicador do painel a partir dos arquivos de origem; divergência
   > 0,1% ou indicador sem verificador reprova o build. As fórmulas de
   `rf_atencao_alta` (faltava "score > 0") e `rf_sem_sinal` (faltava
   "cobertura ≥ 50%") foram corrigidas e agora reproduzem. 49/49 verificações OK.
   O gate está no orquestrador `00_atualizar.py`: painel não é gerado com falha.
3. **Regressão jurídica desfeita.** `descricao_irregularidade` voltou às colunas
   publicadas (conduta + número do processo qualificam cada imputação); a linha do
   termo de compromisso do PAS 19957.006858/2019-25 foi reescrita no padrão
   agregado (sem "seu diretor"); o linter jurídico embutido na etapa 20 falha o
   build se condenação aparecer sem processo visível ou se houver reidentificação
   cargo+entidade. O linter pegou ainda dois casos que o espelho não listou
   (Finaxis e Planner, "seu diretor responsável foi multado") — sanitizados.

Não bloqueantes da mesma rodada, também fechados:

- **Backtest**: tabela do `BACKTEST_RED_FLAGS.md` agora é regenerada pelo próprio
  script entre marcadores (staleness CSV×MD eliminada como classe); publicadas as
  DUAS colunas de antecedência (em 5 de 6 sinais os controles acendem antes — a
  métrica mede posição na janela, não antecipação); pool de controle
  descontaminado (positivos de qualquer evento excluídos de todos os controles —
  0 positivos reutilizados).
- **Lente 1 × lente 8**: cobertura da lente 1 publicada com 2 casas (99,99%), sem
  arredondar para 100%.
- **Lente 5**: as três coberturas nomeadas na ficha da lente (69,3% dos veículos;
  79,7% do estoque de DC; 45,7% do estoque explicado pelas posições top-25).
- **Subtítulo da capa** corrigido: não afirma mais que "todo número é clicável" —
  descreve o que de fato existe (gaveta nos indicadores, unidade declarada por
  coluna, verificação automática de fórmulas).

Novos entregáveis do mandato nesta rodada: bloco "O que mudou no mês" (variações
1/3/6m, aquisições/captações/resgates do mês, entrantes/saíntes, sinais novos ×
persistentes; "encerrados" declarado não computável até existir snapshot
anterior); aba "Raio-X da empresa" (cedente: exposição, recorrência, RJ, papel de
cotista corporativo, veículos); orquestrador `00_atualizar.py` com manifesto de
execução, gates de publicação e snapshot versionado de sinais; limitação do mapa
de gravames documentada em `VALIDACAO_HUMANA_PENDENTE.md` (item 4.6).
