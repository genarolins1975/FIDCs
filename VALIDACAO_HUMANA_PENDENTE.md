# O que depende de validação humana antes de uso externo

Lista objetiva, em ordem de prioridade. Nada aqui impede o uso interno do painel;
tudo aqui impede afirmações públicas categóricas sobre entidades nominadas.

## 1. Jurídico — bloqueante para publicação externa

| # | Item | Por quê | Quem decide |
|---|---|---|---|
| 1.1 | Publicação de **rankings de risco com entidades nominadas** (tela 4) | Score alto não é imputação, mas a leitura de terceiros pode ser difamatória. `docs/LIMITACOES_E_RISCOS_JURIDICOS.md` recomendou manter fora do produto público | Jurídico |
| 1.2 | Menção a **grupo sob investigação penal** (Operação Carbono Oculto) mesmo com status declarado | Persecução em curso; caracterização vem de reportagem, não de fonte primária | Jurídico |
| 1.3 | Lista de **empresas em recuperação judicial** ligadas a FIDCs | O vínculo é de originação, não de inadimplência; risco de leitura como "empresa problemática" | Jurídico + Compliance |
| 1.4 | Tratamento de **pessoas naturais** condenadas em PAS | Optou-se por descritor funcional sem nome; confirmar se a política se mantém | Jurídico |

## 2. Metodológico — bloqueante para afirmar poder preditivo

| # | Item | Estado atual | O que falta |
|---|---|---|---|
| 2.1 | **Pesos por severidade** dos 46 sinais | Arbitrados por julgamento especializado | Validação por backtest com N suficiente |
| 2.2 | **Conclusão do backtest** | 1 evento com vínculo robusto; 2 sinais descartados | Ampliar biblioteca de eventos com vínculo por CNPJ; pareamento por segmento |
| 2.3 | Distinção entre **característica estrutural e precursor** | Identificada e declarada, não resolvida | Pareamento por tipo de veículo e público-alvo |
| 2.4 | Limiar de **concentração por devedor** | Calculado sobre a distribuição do mercado | Checar contra as exceções do art. 45 do Anexo II (§§ 3º, 7º e 8º dispensam o limite para investidor profissional, grupo econômico único e receitas públicas) — **alerta sem essa checagem gera falso positivo em escala** |

## 3. Dados — verificação de campo

| # | Item | Situação |
|---|---|---|
| 3.1 | **7 casos corporativos indiciários** (cotas de FIDC em balanço) | Só Banco Honda confirmado em nota explicativa; os demais aguardam leitura do documento original |
| 3.2 | **10 casos de RJ sem CNPJ** | Marcados "correspondência por nome, requer validação humana"; vínculo não afirmado |
| 3.3 | **307 veículos** com soma dos 25 maiores devedores acima da carteira informada | Inconsistência entre tabelas VIII e I; publicada como tal, sem correção arbitrária |
| 3.4 | **Erros de unidade na tab IX** (taxas na casa dos milhões) | Detectados e não corrigidos; entram como sinal de integridade de dados |
| 3.5 | Classificação **concursal vs. extraconcursal** | Deliberadamente não feita: depende do contrato e da data do fato gerador, não do nome do credor |

## 4. Lacunas de fonte que nenhuma decisão interna resolve

| # | Lacuna | Consequência |
|---|---|---|
| 4.1 | **Demonstrativo trimestral não é publicado em dados abertos** (Anexo II, art. 27, V) | O campo que mede diretamente créditos inexistentes na verificação de lastro — a medida mais próxima de fraude documental — é inacessível a qualquer painel construído sobre dados abertos |
| 4.2 | **Identidade do sacado ausente na tab VIII** | Impossível somar exposição de um devedor entre fundos ou montar ranking nominal |
| 4.3 | **DataJud não retorna as partes** | Impossível casar processo judicial com CNPJ pela API; contornado pelo marcador cadastral do art. 69, que só cobre quem já teve o nome alterado |
| 4.4 | **Cedentes limitados aos 9 maiores por veículo** | Cobertura de 29,4% do estoque; ranking é piso |
| 4.5 | **Valor por cotista não é público** | Quem detém a subordinação em valor permanece não observável |
| 4.6 | **Mapa de gravames e ônus (encumbrance) não existe em fonte pública** | A cadeia credor → instrumento → garantia — quem tem penhor ou cessão fiduciária sobre quais recebíveis, e se o mesmo lastro suporta mais de uma operação — não é reconstituível com dados abertos. A tab X_7 traz o VALOR agregado de garantias declarado pelo próprio veículo, sem identificar beneficiário nem instrumento; os registros de ônus ficam em cartórios de títulos e nas centrais registradoras (B3/CERC), sem acesso público estruturado. O duplo comprometimento do mesmo recebível — mecanismo central em fraudes documentadas — só é detectável por auditoria com acesso às centrais |

## 5. Recomendações regulatórias derivadas

Decorrem das lacunas acima e são a contribuição do trabalho para a agenda de
transparência: estruturar o demonstrativo trimestral em dados abertos; publicar
identificador pseudonimizado de sacado na tab VIII; ampliar a lista de cedentes
além dos 9 maiores; publicar valor (não apenas contagem) de cotistas por
categoria; e incluir as partes na API pública do DataJud, ainda que apenas por
CNPJ das pessoas jurídicas.
