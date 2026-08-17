# Uso indevido de FIDCs — casos documentados, tipologia e conexão com a base

**Advertências obrigatórias.** (i) Vários casos abaixo são investigações ou
processos em curso: alegações ≠ condenação. (ii) A liquidação de um
prestador de serviços pelo BCB não implica ilicitude de cada fundo por ele
servido; o patrimônio dos fundos é segregado do patrimônio do prestador.
(iii) Red flags são sinais estatísticos de atenção supervisória, não
imputação de irregularidade. Este dossiê usa apenas fontes públicas, citadas
caso a caso.

## 1. Casos documentados

### 1.1 Reag / FIDC Gold Style — Operação Carbono Oculto (2025-2026)
- Em 28/08/2025, a Operação Carbono Oculto (PF/MPSP/Receita) cumpriu mandados
  contra ~350 alvos, incluindo 42 gestoras/instituições na Faria Lima, entre
  elas o grupo Reag. Segundo o COAF/PF, o **FIDC Gold Style** recebeu cerca de
  **R$ 1 bi** de empresas apontadas como ligadas ao esquema de lavagem do PCC
  (Aster Petróleo R$ 759,5 mi; BK Bank R$ 158 mi; Inovanti IP R$ 175 mi).
  O MP atribui ao fundador da Reag "dinâmica fraudulenta envolvendo fundos".
- O BCB decretou a liquidação extrajudicial da **Reag Trust DTVM — renomeada
  CBSF DTVM (CNPJ 34.829.992/0001-86)** em **15/01/2026**, por "graves
  violações às normas do SFN" (termo legal: 17/11/2025).
- Mecanismo alegado: "carrossel" de fundos movimentando recursos de forma
  atípica, inflando resultados e ocultando riscos; FIDC como porta de entrada
  de recursos sem origem demonstrada (integralização/aquisição de recebíveis
  de empresas de fachada).
- Status: investigação/persecução em curso. **[Fortemente suportado para os
  fatos regulatórios (liquidação, operação); Indiciário para as imputações]**

### 1.2 Banco Master (2025-2026)
- Liquidação extrajudicial do Banco Master em nov/2025 ("grave crise de
  liquidez" e "graves violações"); prisão do controlador; até fev/2026, dez
  entidades ligadas liquidadas; impacto estimado de R$ 51,8 bi no FGC.
- Vínculo com FIDCs: **52-58 FIDCs** com R$ 3,1-3,9 bi de PL ficaram "à
  deriva" com a liquidação de prestadores do conglomerado; fundos
  administrados pela Reag teriam estruturado operações fraudulentas com o
  Master entre jul/2023 e jul/2024 (apuração em curso).
- Mecanismo: interconexão banco-fundos (carteiras cedidas, cotas e funding
  cruzado) que transmite o colapso do banco à cadeia de fundos.

### 1.3 Banco Cruzeiro do Sul (2007-2012) — o precedente clássico
- ~320 mil contratos de consignado **fictícios** usados para inflar ativos
  (R$ 2,5 bi em ativos falsos; rombo ~R$ 1,3 bi). A CVM determinou refazimento
  das DFs para eliminar efeitos da suposta cessão de R$ 233,1 mi a FIDCs do
  próprio banco. Intervenção (jun/2012), liquidação e falência; denúncia do
  MPF contra 17 pessoas.
- Mecanismo: **lastro inexistente** cedido a FIDC cativo — o fundo compra
  "crédito" que não existe e devolve caixa ao originador.

### 1.4 Silverado / FIDCs Maximum, Maximum II e Petro (2010s; julgado 2024)
- Rombo estimado de R$ 560 mi; CVM multou a gestora (Florim, ex-Silverado) e
  seu ex-diretor em **R$ 244,9 mi cada** (2024) por operação fraudulenta;
  área técnica apontou "relação estreita entre cedentes e gestora" (vedada).
- Mecanismo: duplicatas sem lastro/"frias" e cedentes ligados ao gestor;
  reprecificação abrupta após anos de cotas estáveis.

### 1.5 Trendbank / FIDC Multisetorial (2010s)
- Força-tarefa Greenfield denunciou 13 pessoas (gestão temerária/fraudulenta,
  notas fiscais simuladas); CVM: "operações de crédito simuladas" para
  transferir valores de cotistas ao próprio grupo; multas ao gestor.

### 1.6 Union National FIDC Financeiros e Mercantis / FIDC Agro (2010s)
- Insolvência ocultada; CVM multou o auditor (KPMG, R$ 1 mi) por parecer sem
  ressalvas apesar de sinais de alerta, e o administrador (Oliveira Trust,
  R$ 1 mi) por falha de diligência.
- Mecanismo: cadeia de gatekeepers falhando em conjunto (auditor,
  administrador, custodiante) — precedente de responsabilização de prestadores.

## 2. Tipologia (o que os casos têm em comum)

| # | Padrão | Casos | Red flag na base |
|---|---|---|---|
| 1 | Lastro fictício / duplicata fria | Cruzeiro do Sul, Silverado, Trendbank | RF1 (inadimplência ~0 + cedente concentrado) |
| 2 | Cedente/gestor/cotista ligados (circuito fechado) | Silverado, Cruzeiro do Sul, Reag | RF3 (1-2 cotistas, interesse único, sub <5%) |
| 3 | Rolagem para esconder atraso (recompra/substituição) | Cruzeiro do Sul, casos CVM 2022 | RF2 (>15% da carteira/12m) |
| 4 | Crescimento explosivo sem verificação de mercado | Reag/Gold Style, Master | RF5 (>150%/12m + cedente ≥80%) |
| 5 | Colapso abrupto pós-evento | Master, Silverado | RF4 (queda >50% m/m) |
| 6 | Contágio por prestador comum | Master, Reag/CBSF | RF6 (exposição nominal a liquidações BCB) |
| 7 | Falha de gatekeepers | Union National | pareceres/eventos (agenda: DFs dos fundos) |

## 3. Conexão com a base (dados próprios, corte 30/06/2026) **[C]**

- O **FIDC Gold Style está no universo**: R$ 1,87 bi de PL no corte, gestora
  REAG JUS Gestão de Ativos Judiciais, administradora CBSF DTVM.
- **71 CNPJs** de veículos com REAG/Gold Style/Master na denominação ou nos
  prestadores somavam **R$ 19,3 bi** no corte
  (`red_flags_liquidacoes_bcb.csv`).
- A **CBSF DTVM (ex-Reag Trust, em liquidação extrajudicial desde 15/01/2026)
  ainda era a 7ª maior administradora do mercado no corte**: R$ 51,9 bi em 84
  veículos — vinha de R$ 77,8 bi/235 veículos em jun/2025; a migração de
  administração acelera (jul/2026 parcial: ~zero). Dois dos oito maiores
  veículos do mercado (Alepo, R$ 8,8 bi; Esperanza, R$ 8,5 bi) e a 5ª maior
  gestora (CBSF Trust, R$ 29,8 bi) pertencem ao ecossistema.
- Triagem completa (`red_flags_regulatorios.csv`): RF1 62 veículos ·
  RF2 124 · RF3 64 · RF4 62 · RF5 6.

## 4. Fontes

- CNN Brasil (liquidação Reag/CBSF; caso Master); Bloomberg Línea (liquidação
  Reag Trust DTVM); Transparência Internacional e Wikipédia (Operação Carbono
  Oculto); RDNews/COAF (fluxos ao FIDC Gold Style); NeoFeed (52 FIDCs à
  deriva no caso Master); Times Brasil/CNBC (FIDCs afetados).
- MPF/EBC/Exame (denúncias Cruzeiro do Sul); gov.br/CVM (multas Silverado
  2024, Trendbank, Union National/KPMG/Oliveira Trust, caso 2022 de
  admin/gestor/custodiante).
- URLs completas na conversa de produção e nos claims C029-C031 do livro de
  evidências.
