# Análise comparativa — relatório externo (ChatGPT, data-base 31/07/2026)

Documento avaliado: "Panorama auditável do mercado brasileiro de FIDCs",
versão de trabalho, 34 páginas, data-base 31/07/2026, extração 17/08/2026
(mesma data da nossa). Guardado fora do repositório (upload do usuário).

## 1. Validação cruzada entre pipelines independentes

Os agregados centrais **coincidem** entre os dois trabalhos, o que constitui
validação mútua de duas implementações independentes sobre a mesma fonte:

| Métrica | Externo (jul/26) | Nosso (jul/26 parcial) | Nosso (jun/26, corte) |
|---|---|---|---|
| Unidades reportantes | 4.208 | 4.208 | 4.327 |
| PL bruto | R$ 950,5 bi | R$ 950,5 bi | R$ 999,5 bi |
| PL dez/2013 | R$ 84,5 bi (430 unid.) | — | R$ 84,5 bi (430 unid.) |
| PL dez/2025 | R$ 918,6 bi (4.013) | — | R$ 919,3 bi (4.013) |
| Inadimplência | 9,2% | — | 9,13% |
| Top-5 administradores | 54,4% | — | 52,6% |
| Anomalias de cedentes excluídas | 446 (jul) | — | 462 (jun) |

A pequena diferença em dez/2025 (918,6 × 919,3) decorre de regras de dedup
ligeiramente distintas; ambas dentro de 0,1%.

## 2. Diferença central: data-base

O trabalho externo usou **31/07/2026**, competência ainda em janela de
entrega (nosso teste de completude mostra ~120 informantes a menos e PL 4,9%
menor que jun/2026 na mesma extração). Mantivemos **30/06/2026** como corte e
usamos jul/2026 apenas como observação parcial. **Nossa escolha é a correta
para totalização**; a dele subestima o mercado e será revisada pela CVM à
medida que informes atrasados entrem.

## 3. O que o trabalho externo tem de melhor (incorporado nesta versão)

1. **Medidas CVM/FIE como segunda fonte primária interna** — incorporado:
   reconciliação exata (diferença 0,0) em 4.314 CNPJs = 99,0% do PL do corte
   (`reconciliacao_medidas_fie.csv`, teste T16).
2. **Par 6 (cotas de FIDC em balanços corporativos) executado parcialmente** —
   ele confirmou 5 saldos em demonstrações financeiras. Incorporado com
   verificação própria: confirmamos na fonte primária o caso Banco Honda
   (DF 30/06/2025, nota 04: R$ 243,173 mi em cotas subordinadas, VJR nível 1);
   os demais entram como pistas com confiança rotulada
   (`investidores_corporativos.csv`).
3. **Cobertura explícita de cada bloco** (CDA 8,8%; Medidas 85,9%; controlador
   não identificado 92,9%) — incorporado: `prestadores_cobertura.csv` mostra
   custodiantes 99,1%, auditores 97,3% e **controladores 7,0%** (ranking de
   controladores rebaixado a ilustrativo no relatório).
4. **Provisões/redução de valor como indicador** — incorporado: R$ 63,3 bi,
   97,9% da inadimplência (`provisoes_reducao.csv`).
5. **Arquivo de anomalias de cedentes** — incorporado:
   `cedentes_anomalias_excluidas.csv` (462 registros no corte).
6. Rótulo "estoque atribuído ≠ fluxo cedido" nos cedentes — linguagem adotada.

## 4. Onde o nosso trabalho está mais forte

1. **Auditoria executada**: o externo declara "bateria mínima não executada;
   nenhum núcleo certificado; opinião NÃO APROVADO". O nosso rodou 18 testes
   (0 FAIL), dois espelhos independentes que reproduziram rankings ao centavo
   e acharam (e corrigimos) um erro real de dupla contagem, e parecer de
   auditor-chefe (APROVADO COM RESSALVAS).
2. **Resolução de entidades**: cedentes com razão social/CNAE resolvidos na
   base pública do CNPJ (o externo publica só CNPJs).
3. **Circularidade**: medimos R$ 161,6 bi via campos I2H/I2I (autodeclarados,
   universo completo); o externo captura R$ 71,9 bi via CDA com 8,8% de
   cobertura — a nossa medida domina a dele.
4. **Cedentes**: mesmo ranking, porém com cobertura publicada (29,4%) e nomes;
   e nosso corte (jun) tem denominadores completos.
5. **Série real, captação com filtro de sanidade documentado, subordinação
   por série (X_2), cotistas por categoria, SCR com cobertura medida (51%),
   painel interativo e manifesto SHA-256 por arquivo.**

## 5. Divergências a monitorar (não incorporadas)

- Os saldos corporativos de Casas Bahia (R$ 1,09 bi), Guararapes, Direcional,
  Heringer, C&A, Quero-Quero e Dotz seguem **Indiciários** até leitura das
  notas explicativas originais — agenda prioritária.
- O externo preserva o outlier de mai/2016 na série ("nenhuma retificação
  autorizava correção"); nós o excluímos com regra documentada e log — as duas
  posturas são defensáveis; a nossa evita um salto espúrio de +120% m/m.
