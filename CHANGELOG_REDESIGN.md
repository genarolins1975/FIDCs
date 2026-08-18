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
