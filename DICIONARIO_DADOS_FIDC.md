# DICIONÁRIO DE DADOS — Panorama FIDC Brasil

Gerado por `scripts/19_dicionario_dados.py` cruzando os dicionários oficiais da CVM
(`meta_inf_mensal_fidc_txt.zip`) com o schema efetivo das tabelas materializadas.
Cobertura medida na competência 2026-06-30.

Convenção de leitura: **cobertura** é a fração de veículos do universo com o campo
preenchido (não nulo). Campo ausente permanece nulo e reduz a cobertura do indicador
que dependa dele — nunca é convertido em zero.

## Tabela I → `ativo`

| Campo | Descrição oficial | Cobertura | Observação |
|---|---|---:|---|
| `CNPJ_ADMIN` | CNPJ do Administrador | 100% |  |
| `ADMIN` | Nome do Administrador | 100% |  |
| `CONDOM` | Forma de condomínio | 100% |  |
| `FUNDO_EXCLUSIVO` | Indica se é fundo exclusivo | 100% |  |
| `COTST_INTERESSE` | Indica se todos os cotistas são vinculados por interesse único e indissociável | 100% |  |
| `TAB_I_VL_ATIVO` | (Tabela I) Ativo | 100% |  |
| `TAB_I2_VL_CARTEIRA` | (I.2) Carteira | 100% |  |
| `TAB_I2A_VL_DIRCRED_RISCO` | (I.2.a) Direitos Creditórios com Aquisição Substancial dos Riscos e Benefícios | 100% |  |
| `TAB_I2B_VL_DIRCRED_SEM_RISCO` | (I.2.b) Direitos Creditórios sem Aquisição Substancial dos Riscos e Benefícios | 100% |  |
| `TAB_I2A2_VL_CRED_VENC_INAD` | (I.2.a.2) Créditos Existentes a Vencer com Parcelas Inadimplentes | 100% |  |
| `TAB_I2A21_VL_TOTAL_PARCELA_INAD` | (I.2.a.2.1) Valor Total das Parcelas Inadimplentes | 100% |  |
| `TAB_I2A3_VL_CRED_INAD` | (I.2.a.3) Créditos Existentes Inadimplentes | 100% |  |
| `TAB_I2A4_VL_CRED_DIRCRED_PERFM` | (I.2.a.4) Créditos Referentes a Direitos Creditórios a Performar | 100% | Descontinuado: cobertura zero desde 2023. Mantido no catálogo para documentar a lacuna, não usado em indicador. |
| `TAB_I2A8_VL_CRED_ACAO_JUDIC` | (I.2.a.8) Créditos que resultem de ações judiciais em curso, constituam seu objeto de litígio ou tenham sido judicialmente penhorados ou dados em garantia | 100% |  |
| `TAB_I2A11_VL_REDUCAO_RECUP` | (I.2.a.11) Provisão para Redução no Valor de Recuperação (-) | 100% |  |
| `TAB_I2B2_VL_CRED_VENC_INAD` | (I.2.b.2) Créditos Existentes a Vencer com Parcelas Inadimplentes | 100% |  |
| `TAB_I2B21_VL_TOTAL_PARCELA_INAD` | (I.2.b.2.1) Valor Total das Parcelas Inadimplentes | 100% |  |
| `TAB_I2B3_VL_CRED_INAD` | (I.2.b.3) Créditos Existentes Inadimplentes | 100% |  |
| `TAB_I2B11_VL_REDUCAO_RECUP` | (I.2.b.11) Provisão para Redução no Valor de Recuperação (-) | 100% |  |
| `TAB_I2H_VL_COTA_FIDC` | (I.2.h) Cotas de Fundos de Investimento em Direitos Creditórios | 100% |  |
| `TAB_I2I_VL_COTA_FIDC_NP` | (I.2.i) Cotas de Fundos de Investimento em Direitos Creditórios Não Padronizados | 0% | **Campo em branco em 100% das linhas desde 2024.** A medida de circularidade usa apenas TAB_I2H. Somar como zero afirmaria ausência. |
| `TAB_I2C_VL_VLMOB` | (I.2.c) Valores Mobiliários | 100% |  |
| `TAB_I2D_VL_TITPUB_FED` | (I.2.d) Títulos Públicos Federais | 100% |  |
| `TAB_I2E_VL_CDB` | (I.2.e) Certificados de Depósitos Bancários | 100% |  |

## Tabela II → `carteira_segmento`

| Campo | Descrição oficial | Cobertura | Observação |
|---|---|---:|---|
| `TAB_II_VL_CARTEIRA` | (Tabela II) Carteira por Segmento | 100% |  |
| `TAB_II_A_VL_INDUST` | (II.a) Industrial | 100% |  |
| `TAB_II_B_VL_IMOBIL` | (II.b) Mercado Imobiliário (não financeiro - ver itens f6 e f7) | 100% |  |
| `TAB_II_C_VL_COMERC` | (II.c) Comercial | 100% |  |
| `TAB_II_C1_VL_COMERC` | (II.c.1) Comercial | 100% |  |
| `TAB_II_C2_VL_VAREJO` | (II.c.2) Comercial - Varejo | 100% |  |
| `TAB_II_C3_VL_ARREND` | (II.c.3) Arrendamento Mercantil | 100% |  |
| `TAB_II_D_VL_SERV` | (II.d) Serviços | 100% |  |
| `TAB_II_D1_VL_SERV` | (II.d.1) Serviços | 100% |  |
| `TAB_II_D2_VL_SERV_PUBLICO` | (II.d.2) Serviços Públicos (eletricidade, telefonia, transporte, saneamento, etc) | 100% |  |
| `TAB_II_D3_VL_SERV_EDUC` | (II.d.3) Serviços Educacionais | 100% |  |
| `TAB_II_D4_VL_ENTRET` | (II.d.4) Entretenimento | 100% |  |
| `TAB_II_E_VL_AGRONEG` | (II.e) Agronegócio | 100% |  |
| `TAB_II_F_VL_FINANC` | (II.f) Financeiro | 100% |  |
| `TAB_II_F1_VL_CRED_PESSOA` | (II.f.1) Crédito Pessoal | 100% |  |
| `TAB_II_F2_VL_CRED_PESSOA_CONSIG` | (II.f.2) Crédito Pessoal Consignado | 100% |  |
| `TAB_II_F3_VL_CRED_CORP` | (II.f.3) Direitos Crédito Corporativo | 100% |  |
| `TAB_II_F4_VL_MIDMARKET` | (II.f.4) Middle Market | 100% |  |
| `TAB_II_F5_VL_VEICULO` | (II.f.5) Veículos | 100% |  |
| `TAB_II_F6_VL_IMOBIL_EMPRESA` | (II.f.6) Carteira Imobiliária - Empresarial | 100% |  |
| `TAB_II_F7_VL_IMOBIL_RESID` | (II.f.7) Carteira Imobiliária - Residencial | 100% |  |
| `TAB_II_F8_VL_OUTRO` | (II.f.8) Outros | 100% |  |
| `TAB_II_G_VL_CREDITO` | (II.g) Cartão de Crédito | 100% |  |
| `TAB_II_H_VL_FACTOR` | (II.h) Factoring | 100% |  |
| `TAB_II_H1_VL_PESSOA` | (II.h.1) Factoring - Pessoal (Perfil do Sacado) | 100% |  |
| `TAB_II_H2_VL_CORP` | (II.h.2) Factoring - Corporativo (Perfil do Sacado) | 100% |  |
| `TAB_II_I_VL_SETOR_PUBLICO` | (II.i) Setor Público (art. 1º, §1º, II, ICVM 444) | 100% |  |
| `TAB_II_I1_VL_PRECAT` | (II.i.1) Precatórios | 100% |  |
| `TAB_II_I2_VL_TRIBUT` | (II.i.2) Créditos Tributários | 100% |  |
| `TAB_II_I3_VL_ROYALTIES` | (II.i.3) Royalties | 100% |  |
| `TAB_II_I4_VL_OUTRO` | (II.i.4) Outros | 100% |  |
| `TAB_II_J_VL_JUDICIAL` | (II.j) Ações Judiciais (art. 1º, §1º, III, ICVM 444) | 100% |  |
| `TAB_II_K_VL_MARCA` | (II.k) Propriedade Intelectual e Marcas & Patentes | 100% |  |

## Tabela III → `passivo`

| Campo | Descrição oficial | Cobertura | Observação |
|---|---|---:|---|
| `TAB_III_VL_PASSIVO` | (Tabela III) Passivo | 100% | Habilita o teste de identidade contábil Ativo − Passivo = PL. |
| `TAB_III_A_VL_PAGAR` | (III.a) Valores a pagar | 100% |  |
| `TAB_III_A1_VL_CPRAZO` | (III.a.1) Curto Prazo | 100% |  |
| `TAB_III_A2_VL_LPRAZO` | (III.a.2) Longo Prazo | 100% |  |
| `TAB_III_B_VL_POSICAO_DERIV` | (III.b) Posições Mantidas em Mercado de Derivativos | 100% |  |
| `TAB_III_B1_VL_TERMO` | (III.b.1) Mercado a termo (Posições vendidas) | 100% |  |
| `TAB_III_B2_VL_OPCAO` | (III.b.2) Mercado de Opções (Posições Lançadas) | 100% |  |
| `TAB_III_B3_VL_FUTURO` | (III.b.3) Mercado Futuro (Ajustes Negativos) | 100% |  |
| `TAB_III_B4_VL_SWAP_PAGAR` | (III.b.4) Diferencial de Swap a Pagar | 100% |  |

## Tabela IV → `pl`

| Campo | Descrição oficial | Cobertura | Observação |
|---|---|---:|---|
| `VL_PL` | — | 100% |  |

## Tabela V → `dc_risco_prazos`

| Campo | Descrição oficial | Cobertura | Observação |
|---|---|---:|---|
| `TAB_V_A_VL_DIRCRED_PRAZO` | (V.a) Por Prazo de Vencimento (R$) | 100% |  |
| `TAB_V_A1_VL_PRAZO_VENC_30` | (V.a.1) Até 30 dias | 100% |  |
| `TAB_V_A2_VL_PRAZO_VENC_60` | (V.a.2) De 31 a 60 dias | 100% |  |
| `TAB_V_A3_VL_PRAZO_VENC_90` | (V.a.3)  De 61 a 90 dias | 100% |  |
| `TAB_V_A4_VL_PRAZO_VENC_120` | (V.a.4) De 91 a 120 dias | 100% |  |
| `TAB_V_A5_VL_PRAZO_VENC_150` | (V.a.5) De 121 a 150 dias | 100% |  |
| `TAB_V_A6_VL_PRAZO_VENC_180` | (V.a.6) De 151 a 180 dias | 100% |  |
| `TAB_V_A7_VL_PRAZO_VENC_360` | (V.a.7) De 181 a 360 dias | 100% |  |
| `TAB_V_A8_VL_PRAZO_VENC_720` | (V.a.8) De 361 a 720 dias | 100% |  |
| `TAB_V_A9_VL_PRAZO_VENC_1080` | (V.a.9) De 721 a 1080 dias | 100% |  |
| `TAB_V_A10_VL_PRAZO_VENC_MAIOR_1080` | (V.a.10) Acima de 1080 dias | 100% |  |
| `TAB_V_B_VL_DIRCRED_INAD` | (V.b) Inadimplentes (Valor das Parcelas Inadimplentes, em R$) | 100% |  |
| `TAB_V_B1_VL_INAD_30` | (V.b.1) Vencidos e não Pagos entre 1 e 30 dias | 100% |  |
| `TAB_V_B2_VL_INAD_60` | (V.b.2) Vencidos e não Pagos entre 31 e 60 dias | 100% |  |
| `TAB_V_B3_VL_INAD_90` | (V.b.3) Vencidos e não Pagos entre 61 e 90 dias | 100% |  |
| `TAB_V_B4_VL_INAD_120` | (V.b.4) Vencidos e não Pagos entre 91 e 120 dias | 100% |  |
| `TAB_V_B5_VL_INAD_150` | (V.b.5) Vencidos e não Pagos entre 121 e 150 dias | 100% |  |
| `TAB_V_B6_VL_INAD_180` | (V.b.6) Vencidos e não Pagos entre 151 e 180 dias | 100% |  |
| `TAB_V_B7_VL_INAD_360` | (V.b.7) Vencidos e não Pagos entre 181 e 360 dias | 100% |  |
| `TAB_V_B8_VL_INAD_720` | (V.b.8) Vencidos e não Pagos entre 361 e 720 dias | 100% |  |
| `TAB_V_B9_VL_INAD_1080` | (V.b.9) Vencidos e não Pagos entre 721 e 1080 dias | 100% |  |
| `TAB_V_B10_VL_INAD_MAIOR_1080` | (V.b.10) Vencidos e não Pagos acima de 1080 dias | 100% |  |
| `TAB_V_C_VL_DIRCRED_ANTECIPADO` | (V.c) Pagos Antecipadamente (R$) | 100% |  |
| `TAB_V_C1_VL_ANTECIPADO_30` | (V.c.1) Pagos Antecipadamente entre 1 e 30 dias do vencimento | 100% |  |
| `TAB_V_C2_VL_ANTECIPADO_60` | (V.c.2) Pagos Antecipadamente entre 31 e 60 dias do vencimento | 100% |  |
| `TAB_V_C3_VL_ANTECIPADO_90` | (V.c.3) Pagos Antecipadamente entre 61 e 90 dias do vencimento | 100% |  |
| `TAB_V_C4_VL_ANTECIPADO_120` | (V.c.4) Pagos Antecipadamente entre 91 e 120 dias do vencimento | 100% |  |
| `TAB_V_C5_VL_ANTECIPADO_150` | (V.c.5) Pagos Antecipadamente entre 121 e 150 dias do vencimento | 100% |  |
| `TAB_V_C6_VL_ANTECIPADO_180` | (V.c.6) Pagos Antecipadamente entre 151 e 180 dias do vencimento | 100% |  |
| `TAB_V_C7_VL_ANTECIPADO_360` | (V.c.7) Pagos Antecipadamente entre 181 e 360 dias do vencimento | 100% |  |
| `TAB_V_C8_VL_ANTECIPADO_720` | (V.c.8) Pagos Antecipadamente entre 361 e 720 dias do vencimento | 100% |  |
| `TAB_V_C9_VL_ANTECIPADO_1080` | (V.c.9) Pagos Antecipadamente entre 721 e 1080 dias do vencimento | 100% |  |
| `TAB_V_C10_VL_ANTECIPADO_MAIOR_1080` | (V.c.10) Pagos Antecipadamente acima de 1080 dias do vencimento | 100% |  |

## Tabela VI → `dc_semrisco_prazos`

| Campo | Descrição oficial | Cobertura | Observação |
|---|---|---:|---|
| `TAB_VI_A_VL_DIRCRED_PRAZO` | (VI.a) Por Prazo de Vencimento (R$) | 100% |  |
| `TAB_VI_A1_VL_PRAZO_VENC_30` | (VI.a.1) Até 30 dias | 100% |  |
| `TAB_VI_A2_VL_PRAZO_VENC_60` | (VI.a.2) De 31 a 60 dias | 100% |  |
| `TAB_VI_A3_VL_PRAZO_VENC_90` | (VI.a.3)  De 61 a 90 dias | 100% |  |
| `TAB_VI_A4_VL_PRAZO_VENC_120` | (VI.a.4) De 91 a 120 dias | 100% |  |
| `TAB_VI_A5_VL_PRAZO_VENC_150` | (VI.a.5) De 121 a 150 dias | 100% |  |
| `TAB_VI_A6_VL_PRAZO_VENC_180` | (VI.a.6) De 151 a 180 dias | 100% |  |
| `TAB_VI_A7_VL_PRAZO_VENC_360` | (VI.a.7) De 181 a 360 dias | 100% |  |
| `TAB_VI_A8_VL_PRAZO_VENC_720` | (VI.a.8) De 361 a 720 dias | 100% |  |
| `TAB_VI_A9_VL_PRAZO_VENC_1080` | (VI.a.9) De 721 a 1080 dias | 100% |  |
| `TAB_VI_A10_VL_PRAZO_VENC_MAIOR_1080` | (VI.a.10) Acima de 1080 dias | 100% |  |
| `TAB_VI_B_VL_DIRCRED_INAD` | (VI.b) Inadimplentes (Valor das Parcelas Inadimplentes, em R$) | 100% |  |
| `TAB_VI_B1_VL_INAD_30` | (VI.b.1) Vencidos e não Pagos entre 1 e 30 dias | 100% |  |
| `TAB_VI_B2_VL_INAD_60` | (VI.b.2) Vencidos e não Pagos entre 31 e 60 dias | 100% |  |
| `TAB_VI_B3_VL_INAD_90` | (VI.b.3) Vencidos e não Pagos entre 61 e 90 dias | 100% |  |
| `TAB_VI_B4_VL_INAD_120` | (VI.b.4) Vencidos e não Pagos entre 91 e 120 dias | 100% |  |
| `TAB_VI_B5_VL_INAD_150` | (VI.b.5) Vencidos e não Pagos entre 121 e 150 dias | 100% |  |
| `TAB_VI_B6_VL_INAD_180` | (VI.b.6) Vencidos e não Pagos entre 151 e 180 dias | 100% |  |
| `TAB_VI_B7_VL_INAD_360` | (VI.b.7) Vencidos e não Pagos entre 181 e 360 dias | 100% |  |
| `TAB_VI_B8_VL_INAD_720` | (VI.b.8) Vencidos e não Pagos entre 361 e 720 dias | 100% |  |
| `TAB_VI_B9_VL_INAD_1080` | (VI.b.9) Vencidos e não Pagos entre 721 e 1080 dias | 100% |  |
| `TAB_VI_B10_VL_INAD_MAIOR_1080` | (VI.b.10) Vencidos e não Pagos acima de 1080 dias | 100% |  |
| `TAB_VI_C_VL_DIRCRED_ANTECIPADO` | (VI.c) Pagos Antecipadamente (R$) | 100% |  |
| `TAB_VI_C1_VL_ANTECIPADO_30` | (VI.c.1) Pagos Antecipadamente entre 1 e 30 dias do vencimento | 100% |  |
| `TAB_VI_C2_VL_ANTECIPADO_60` | (VI.c.2) Pagos Antecipadamente entre 31 e 60 dias do vencimento | 100% |  |
| `TAB_VI_C3_VL_ANTECIPADO_90` | (VI.c.3) Pagos Antecipadamente entre 61 e 90 dias do vencimento | 100% |  |
| `TAB_VI_C4_VL_ANTECIPADO_120` | (VI.c.4) Pagos Antecipadamente entre 91 e 120 dias do vencimento | 100% |  |
| `TAB_VI_C5_VL_ANTECIPADO_150` | (VI.c.5) Pagos Antecipadamente entre 121 e 150 dias do vencimento | 100% |  |
| `TAB_VI_C6_VL_ANTECIPADO_180` | (VI.c.6) Pagos Antecipadamente entre 151 e 180 dias do vencimento | 100% |  |
| `TAB_VI_C7_VL_ANTECIPADO_360` | (VI.c.7) Pagos Antecipadamente entre 181 e 360 dias do vencimento | 100% |  |
| `TAB_VI_C8_VL_ANTECIPADO_720` | (VI.c.8) Pagos Antecipadamente entre 361 e 720 dias do vencimento | 100% |  |
| `TAB_VI_C9_VL_ANTECIPADO_1080` | (VI.c.9) Pagos Antecipadamente entre 721 e 1080 dias do vencimento | 100% |  |
| `TAB_VI_C10_VL_ANTECIPADO_MAIOR_1080` | (VI.c.10) Pagos Antecipadamente acima de 1080 dias do vencimento | 100% |  |

## Tabela VII → `negocios`

| Campo | Descrição oficial | Cobertura | Observação |
|---|---|---:|---|
| `TAB_VII_A1_1_QT_DIRCRED_RISCO` | (VII.a.1.1) Aquisições | Direitos Creditórios com Aquisição Substancial dos Riscos e Benefícios | Quantidade | 100% |  |
| `TAB_VII_A1_2_VL_DIRCRED_RISCO` | (VII.a.1.2) Aquisições | Direitos Creditórios com Aquisição Substancial dos Riscos e Benefícios | Valor | 100% |  |
| `TAB_VII_A2_1_QT_DIRCRED_SEM_RISCO` | (VII.a.2.1) Aquisições | Direitos Creditórios sem Aquisição Substancial dos Riscos e Benefícios | Quantidade | 100% |  |
| `TAB_VII_A2_2_VL_DIRCRED_SEM_RISCO` | (VII.a.2.2) Aquisições | Direitos Creditórios sem Aquisição Substancial dos Riscos e Benefícios | Valor | 100% |  |
| `TAB_VII_A3_1_QT_DIRCRED_VENC_AD` | (VII.a.3.1) Aquisições | Direitos Creditórios a Vencer e com parcela(s) Adimplentes | Quantidade | 100% |  |
| `TAB_VII_A3_2_VL_DIRCRED_VENC_AD` | (VII.a.3.2) Aquisições | Direitos Creditórios a Vencer e com parcela(s) Adimplentes | Valor | 100% |  |
| `TAB_VII_A4_1_QT_DIRCRED_VENC_INAD` | (VII.a.4.1) Aquisições | Direitos Creditórios a Vencer com Parcelas Inadimplentes | Quantidade | 100% |  |
| `TAB_VII_A4_2_VL_DIRCRED_VENC_INAD` | (VII.a.4.2) Aquisições | Direitos Creditórios a Vencer com Parcelas Inadimplentes | Valor | 100% |  |
| `TAB_VII_A5_1_QT_DIRCRED_INAD` | (VII.a.5.1) Aquisições | Direitos Creditórios Inadimplentes | Quantidade | 100% |  |
| `TAB_VII_A5_2_VL_DIRCRED_INAD` | (VII.a.5.2) Aquisições | Direitos Creditórios Inadimplentes | Valor | 100% |  |
| `TAB_VII_B1_1_QT_CEDENTE` | (VII.b.1.1) Alienações | Para o Cedente e Partes Relacionadas aos Cedentes | Quantidade | 100% |  |
| `TAB_VII_B1_2_VL_CEDENTE` | (VII.b.1.2) Alienações | Para o Cedente e Partes Relacionadas aos Cedentes | Valor | 100% |  |
| `TAB_VII_B1_3_VL_CONTAB_CEDENTE` | (VII.b.1.3) Alienações | Para o Cedente e Partes Relacionadas aos Cedentes | Valor Contábil | 100% |  |
| `TAB_VII_B2_1_QT_PREST` | (VII.b.2.1) Alienações | Para os Prestadores de Serviços e Partes Relacionadas aos Prestadores de Serviços | Quantidade | 100% |  |
| `TAB_VII_B2_2_VL_PREST` | (VII.b.2.2) Alienações | Para os Prestadores de Serviços e Partes Relacionadas aos Prestadores de Serviços | Valor | 100% |  |
| `TAB_VII_B2_3_VL_CONTAB_PREST` | (VII.b.2.3) Alienações | Para os Prestadores de Serviços e Partes Relacionadas aos Prestadores de Serviços | Valor Contábil | 100% |  |
| `TAB_VII_B3_1_QT_TERCEIRO` | (VII.b.3.1) Alienações | Para Terceiros | Quantidade | 100% |  |
| `TAB_VII_B3_2_VL_TERCEIRO` | (VII.b.3.2) Alienações | Para Terceiros | Valor | 100% |  |
| `TAB_VII_B3_3_VL_CONTAB_TERCEIRO` | (VII.b.3.3) Alienações | Para Terceiros | Valor Contábil | 100% |  |
| `TAB_VII_C_1_QT_SUBST` | (VII.c.1) Substituições | Quantidade | 100% |  |
| `TAB_VII_C_2_VL_SUBST` | (VII.c.2) Substituições | Valor | 100% |  |
| `TAB_VII_C_3_VL_CONTAB_SUBST` | (VII.c.3) Substituições | Valor Contábil | 100% |  |
| `TAB_VII_D_1_QT_RECOMPRA` | (VII.d.1) Recompras | Quantidade | 100% |  |
| `TAB_VII_D_2_VL_RECOMPRA` | (VII.d.2) Recompras | Valor | 100% |  |
| `TAB_VII_D_3_VL_CONTAB_RECOMPRA` | (VII.d.3) Recompras | Valor Contábil | 100% |  |

## Tabela VIII → `sacados_conc`

| Campo | Descrição oficial | Cobertura | Observação |
|---|---|---:|---|
| `SEQUENCIAL` | — | 100% | Posição no ranking interno de devedores do veículo (1 a 25). **Não há identificador do sacado** — é impossível somar a exposição de um devedor entre fundos. |
| `VALOR` | — | 100% |  |

## Tabela IX → `taxas`

| Campo | Descrição oficial | Cobertura | Observação |
|---|---|---:|---|
| `TAB_IX_A1_1_1_COMPRA_MIN` | (IX.a.1.1.1) Direitos Creditórios com Aquisição Substancial dos Riscos e Benefícios | Taxa desconto (da aquisição) | Compra | Mínina | 100% |  |
| `TAB_IX_A1_1_2_COMPRA_MEDIA` | (IX.a.1.1.2) Direitos Creditórios com Aquisição Substancial dos Riscos e Benefícios | Taxa desconto (da aquisição) | Compra | Média (Ponderada) | 100% | Taxa média ponderada de desconto na aquisição. Apenas ~26% dos veículos operam no mês; os demais reportam zero. Há erros de unidade na cauda. |
| `TAB_IX_A1_1_3_COMPRA_MAX` | (IX.a.1.1.3) Direitos Creditórios com Aquisição Substancial dos Riscos e Benefícios | Taxa desconto (da aquisição) | Compra | Máxima | 100% |  |
| `TAB_IX_A1_2_1_VENDA_MIN` | (IX.a.1.2.1) Direitos Creditórios com Aquisição Substancial dos Riscos e Benefícios | Taxa desconto (da aquisição) | Venda | Mínina | 100% |  |
| `TAB_IX_A1_2_2_VENDA_MEDIA` | (IX.a.1.2.2) Direitos Creditórios com Aquisição Substancial dos Riscos e Benefícios | Taxa desconto (da aquisição) | Venda | Média (Ponderada) | 100% |  |
| `TAB_IX_A1_2_3_VENDA_MAX` | (IX.a.1.2.3) Direitos Creditórios com Aquisição Substancial dos Riscos e Benefícios | Taxa desconto (da aquisição) | Venda | Máxima | 100% |  |
| `TAB_IX_A2_1_1_COMPRA_MIN` | (IX.a.2.1.1) Direitos Creditórios com Aquisição Substancial dos Riscos e Benefícios | Taxa de Juros(dos direitos creditórios) | Compra | Mínina | 100% |  |
| `TAB_IX_A2_1_2_COMPRA_MEDIA` | (IX.a.2.1.2) Direitos Creditórios com Aquisição Substancial dos Riscos e Benefícios | Taxa de Juros(dos direitos creditórios) | Compra | Média (Ponderada) | 100% |  |
| `TAB_IX_A2_1_3_COMPRA_MAX` | (IX.a.2.1.3) Direitos Creditórios com Aquisição Substancial dos Riscos e Benefícios | Taxa de Juros(dos direitos creditórios) | Compra | Máxima | 100% |  |
| `TAB_IX_A2_2_1_VENDA_MIN` | (IX.a.2.2.1) Direitos Creditórios com Aquisição Substancial dos Riscos e Benefícios | Taxa de Juros(dos direitos creditórios) | Venda | Mínina | 100% |  |
| `TAB_IX_A2_2_2_VENDA_MEDIA` | (IX.a.2.2.2) Direitos Creditórios com Aquisição Substancial dos Riscos e Benefícios | Taxa de Juros(dos direitos creditórios) | Venda | Média (Ponderada) | 100% |  |
| `TAB_IX_A2_2_3_VENDA_MAX` | (IX.a.2.2.3) Direitos Creditórios com Aquisição Substancial dos Riscos e Benefícios | Taxa de Juros(dos direitos creditórios) | Venda | Máxima | 100% |  |
| `TAB_IX_B1_1_1_COMPRA_MIN` | (IX.b.1.1.1) Direitos Creditórios sem Aquisição Substancial dos Riscos e Benefícios | Taxa desconto (da aquisição) | Compra | Mínina | 100% |  |
| `TAB_IX_B1_1_2_COMPRA_MEDIA` | (IX.b.1.1.2) Direitos Creditórios sem Aquisição Substancial dos Riscos e Benefícios | Taxa desconto (da aquisição) | Compra | Média (Ponderada) | 100% |  |
| `TAB_IX_B1_1_3_COMPRA_MAX` | (IX.b.1.1.3) Direitos Creditórios sem Aquisição Substancial dos Riscos e Benefícios | Taxa desconto (da aquisição) | Compra | Máxima | 100% |  |
| `TAB_IX_B1_2_1_VENDA_MIN` | (IX.b.1.2.1) Direitos Creditórios sem Aquisição Substancial dos Riscos e Benefícios | Taxa desconto (da aquisição) | Venda | Mínina | 100% |  |
| `TAB_IX_B1_2_2_VENDA_MEDIA` | (IX.b.1.2.2) Direitos Creditórios sem Aquisição Substancial dos Riscos e Benefícios | Taxa desconto (da aquisição) | Venda | Média (Ponderada) | 100% |  |
| `TAB_IX_B1_2_3_VENDA_MAX` | (IX.b.1.2.3) Direitos Creditórios sem Aquisição Substancial dos Riscos e Benefícios | Taxa desconto (da aquisição) | Venda | Máxima | 100% |  |
| `TAB_IX_B2_1_1_COMPRA_MIN` | (IX.b.2.1.1) Direitos Creditórios sem Aquisição Substancial dos Riscos e Benefícios | Taxa de Juros(dos direitos creditórios) | Compra | Mínina | 100% |  |
| `TAB_IX_B2_1_2_COMPRA_MEDIA` | (IX.b.2.1.2) Direitos Creditórios sem Aquisição Substancial dos Riscos e Benefícios | Taxa de Juros(dos direitos creditórios) | Compra | Média (Ponderada) | 100% |  |
| `TAB_IX_B2_1_3_COMPRA_MAX` | (IX.b.2.1.3) Direitos Creditórios sem Aquisição Substancial dos Riscos e Benefícios | Taxa de Juros(dos direitos creditórios) | Compra | Máxima | 100% |  |
| `TAB_IX_B2_2_1_VENDA_MIN` | (IX.b.2.2.1) Direitos Creditórios sem Aquisição Substancial dos Riscos e Benefícios | Taxa de Juros(dos direitos creditórios) | Venda | Mínina | 100% |  |
| `TAB_IX_B2_2_2_VENDA_MEDIA` | (IX.b.2.2.2) Direitos Creditórios sem Aquisição Substancial dos Riscos e Benefícios | Taxa de Juros(dos direitos creditórios) | Venda | Média (Ponderada) | 100% |  |
| `TAB_IX_B2_2_3_VENDA_MAX` | (IX.b.2.2.3) Direitos Creditórios sem Aquisição Substancial dos Riscos e Benefícios | Taxa de Juros(dos direitos creditórios) | Venda | Máxima | 100% |  |
| `TAB_IX_C1_1_1_COMPRA_MIN` | (IX.c.1.1.1) Valores Mobiliários | Taxa desconto (da aquisição) | Compra | Mínina | 100% |  |
| `TAB_IX_C1_1_2_COMPRA_MEDIA` | (IX.c.1.1.2) Valores Mobiliários | Taxa desconto (da aquisição) | Compra | Média (Ponderada) | 100% |  |
| `TAB_IX_C1_1_3_COMPRA_MAX` | (IX.c.1.1.3) Valores Mobiliários | Taxa desconto (da aquisição) | Compra | Máxima | 100% |  |
| `TAB_IX_C1_2_1_VENDA_MIN` | (IX.c.1.2.1) Valores Mobiliários | Taxa desconto (da aquisição) | Venda | Mínina | 100% |  |
| `TAB_IX_C1_2_2_VENDA_MEDIA` | (IX.c.1.2.2) Valores Mobiliários | Taxa desconto (da aquisição) | Venda | Média (Ponderada) | 100% |  |
| `TAB_IX_C1_2_3_VENDA_MAX` | (IX.c.1.2.3) Valores Mobiliários | Taxa desconto (da aquisição) | Venda | Máxima | 100% |  |
| `TAB_IX_C2_1_1_COMPRA_MIN` | (IX.c.2.1.1) Valores Mobiliários | Taxa de Juros | Compra | Mínina | 100% |  |
| `TAB_IX_C2_1_2_COMPRA_MEDIA` | (IX.c.2.1.2) Valores Mobiliários | Taxa de Juros | Compra | Média (Ponderada) | 100% |  |
| `TAB_IX_C2_1_3_COMPRA_MAX` | (IX.c.2.1.3) Valores Mobiliários | Taxa de Juros | Compra | Máxima | 100% |  |
| `TAB_IX_C2_2_1_VENDA_MIN` | (IX.c.2.2.1) Valores Mobiliários | Taxa de Juros | Venda | Mínina | 100% |  |
| `TAB_IX_C2_2_2_VENDA_MEDIA` | (IX.c.2.2.2) Valores Mobiliários | Taxa de Juros | Venda | Média (Ponderada) | 100% |  |
| `TAB_IX_C2_2_3_VENDA_MAX` | (IX.c.2.2.3) Valores Mobiliários | Taxa de Juros | Venda | Máxima | 100% |  |
| `TAB_IX_D1_1_1_COMPRA_MIN` | (IX.d.1.1.1) Títulos Públicos Federais | Taxa desconto (da aquisição) | Compra | Mínina | 100% |  |
| `TAB_IX_D1_1_2_COMPRA_MEDIA` | (IX.d.1.1.2) Títulos Públicos Federais | Taxa desconto (da aquisição) | Compra | Média (Ponderada) | 100% |  |
| `TAB_IX_D1_1_3_COMPRA_MAX` | (IX.d.1.1.3) Títulos Públicos Federais | Taxa desconto (da aquisição) | Compra | Máxima | 100% |  |
| `TAB_IX_D1_2_1_VENDA_MIN` | (IX.d.1.2.1) Títulos Públicos Federais | Taxa desconto (da aquisição) | Venda | Mínina | 100% |  |
| `TAB_IX_D1_2_2_VENDA_MEDIA` | (IX.d.1.2.2) Títulos Públicos Federais | Taxa desconto (da aquisição) | Venda | Média (Ponderada) | 100% |  |
| `TAB_IX_D1_2_3_VENDA_MAX` | (IX.d.1.2.3) Títulos Públicos Federais | Taxa desconto (da aquisição) | Venda | Máxima | 100% |  |
| `TAB_IX_D2_1_1_COMPRA_MIN` | (IX.d.2.1.1) Títulos Públicos Federais | Taxa de Juros | Compra | Mínina | 100% |  |
| `TAB_IX_D2_1_2_COMPRA_MEDIA` | (IX.d.2.1.2) Títulos Públicos Federais | Taxa de Juros | Compra | Média (Ponderada) | 100% |  |
| `TAB_IX_D2_1_3_COMPRA_MAX` | (IX.d.2.1.3) Títulos Públicos Federais | Taxa de Juros | Compra | Máxima | 100% |  |
| `TAB_IX_D2_2_1_VENDA_MIN` | (IX.d.2.2.1) Títulos Públicos Federais | Taxa de Juros | Venda | Mínina | 100% |  |
| `TAB_IX_D2_2_2_VENDA_MEDIA` | (IX.d.2.2.2) Títulos Públicos Federais | Taxa de Juros | Venda | Média (Ponderada) | 100% |  |
| `TAB_IX_D2_2_3_VENDA_MAX` | (IX.d.2.2.3) Títulos Públicos Federais | Taxa de Juros | Venda | Máxima | 100% |  |
| `TAB_IX_E1_1_1_COMPRA_MIN` | (IX.e.1.1.1) Certificados de Depósitos Bancários | Taxa desconto (da aquisição) | Compra | Mínina | 100% |  |
| `TAB_IX_E1_1_2_COMPRA_MEDIA` | (IX.e.1.1.2) Certificados de Depósitos Bancários | Taxa desconto (da aquisição) | Compra | Média (Ponderada) | 100% |  |
| `TAB_IX_E1_1_3_COMPRA_MAX` | (IX.e.1.1.3) Certificados de Depósitos Bancários | Taxa desconto (da aquisição) | Compra | Máxima | 100% |  |
| `TAB_IX_E1_2_1_VENDA_MIN` | (IX.e.1.2.1) Certificados de Depósitos Bancários | Taxa desconto (da aquisição) | Venda | Mínina | 100% |  |
| `TAB_IX_E1_2_2_VENDA_MEDIA` | (IX.e.1.2.2) Certificados de Depósitos Bancários | Taxa desconto (da aquisição) | Venda | Média (Ponderada) | 100% |  |
| `TAB_IX_E1_2_3_VENDA_MAX` | (IX.e.1.2.3) Certificados de Depósitos Bancários | Taxa desconto (da aquisição) | Venda | Máxima | 100% |  |
| `TAB_IX_E2_1_1_COMPRA_MIN` | (IX.e.2.1.1) Certificados de Depósitos Bancários | Taxa de Juros | Compra | Mínina | 100% |  |
| `TAB_IX_E2_1_2_COMPRA_MEDIA` | (IX.e.2.1.2) Certificados de Depósitos Bancários | Taxa de Juros | Compra | Média (Ponderada) | 100% |  |
| `TAB_IX_E2_1_3_COMPRA_MAX` | (IX.e.2.1.3) Certificados de Depósitos Bancários | Taxa de Juros | Compra | Máxima | 100% |  |
| `TAB_IX_E2_2_1_VENDA_MIN` | (IX.e.2.2.1) Certificados de Depósitos Bancários | Taxa de Juros | Venda | Mínina | 100% |  |
| `TAB_IX_E2_2_2_VENDA_MEDIA` | (IX.e.2.2.2) Certificados de Depósitos Bancários | Taxa de Juros | Venda | Média (Ponderada) | 100% |  |
| `TAB_IX_E2_2_3_VENDA_MAX` | (IX.e.2.2.3) Certificados de Depósitos Bancários | Taxa de Juros | Venda | Máxima | 100% |  |
| `TAB_IX_F1_1_1_COMPRA_MIN` | (IX.f.1.1.1) Outros Ativos Financeiros de Renda Fixa | Taxa desconto (da aquisição) | Compra | Mínina | 100% |  |
| `TAB_IX_F1_1_2_COMPRA_MEDIA` | (IX.f.1.1.2) Outros Ativos Financeiros de Renda Fixa | Taxa desconto (da aquisição) | Compra | Média (Ponderada) | 100% |  |
| `TAB_IX_F1_1_3_COMPRA_MAX` | (IX.f.1.1.3) Outros Ativos Financeiros de Renda Fixa | Taxa desconto (da aquisição) | Compra | Máxima | 100% |  |
| `TAB_IX_F1_2_1_VENDA_MIN` | (IX.f.1.2.1) Outros Ativos Financeiros de Renda Fixa | Taxa desconto (da aquisição) | Venda | Mínina | 100% |  |
| `TAB_IX_F1_2_2_VENDA_MEDIA` | (IX.f.1.2.2) Outros Ativos Financeiros de Renda Fixa | Taxa desconto (da aquisição) | Venda | Média (Ponderada) | 100% |  |
| `TAB_IX_F1_2_3_VENDA_MAX` | (IX.f.1.2.3) Outros Ativos Financeiros de Renda Fixa | Taxa desconto (da aquisição) | Venda | Máxima | 100% |  |
| `TAB_IX_F2_1_1_COMPRA_MIN` | (IX.f.2.1.1) Outros Ativos Financeiros de Renda Fixa | Taxa de Juros | Compra | Mínina | 100% |  |
| `TAB_IX_F2_1_2_COMPRA_MEDIA` | (IX.f.2.1.2) Outros Ativos Financeiros de Renda Fixa | Taxa de Juros | Compra | Média (Ponderada) | 100% |  |
| `TAB_IX_F2_1_3_COMPRA_MAX` | (IX.f.2.1.3) Outros Ativos Financeiros de Renda Fixa | Taxa de Juros | Compra | Máxima | 100% |  |
| `TAB_IX_F2_2_1_VENDA_MIN` | (IX.f.2.2.1) Outros Ativos Financeiros de Renda Fixa | Taxa de Juros | Venda | Mínina | 100% |  |
| `TAB_IX_F2_2_2_VENDA_MEDIA` | (IX.f.2.2.2) Outros Ativos Financeiros de Renda Fixa | Taxa de Juros | Venda | Média (Ponderada) | 100% |  |
| `TAB_IX_F2_2_3_VENDA_MAX` | (IX.f.2.2.3) Outros Ativos Financeiros de Renda Fixa | Taxa de Juros | Venda | Máxima | 100% |  |

## Tabela X → `scr`

| Campo | Descrição oficial | Cobertura | Observação |
|---|---|---:|---|
| `TAB_X_SCR_RISCO_DEVEDOR_AA` | (X.8.1) Valor Total dos direitos creditórios reportados ao SCR com base nas classificações de riscos dos devedores - AA | 100% |  |
| `TAB_X_SCR_RISCO_DEVEDOR_A` | (X.8.1) Valor Total dos direitos creditórios reportados ao SCR com base nas classificações de riscos dos devedores - A | 100% |  |
| `TAB_X_SCR_RISCO_DEVEDOR_B` | (X.8.1) Valor Total dos direitos creditórios reportados ao SCR com base nas classificações de riscos dos devedores - B | 100% |  |
| `TAB_X_SCR_RISCO_DEVEDOR_C` | (X.8.1) Valor Total dos direitos creditórios reportados ao SCR com base nas classificações de riscos dos devedores - C | 100% |  |
| `TAB_X_SCR_RISCO_DEVEDOR_D` | (X.8.1) Valor Total dos direitos creditórios reportados ao SCR com base nas classificações de riscos dos devedores - D | 100% |  |
| `TAB_X_SCR_RISCO_DEVEDOR_E` | (X.8.1) Valor Total dos direitos creditórios reportados ao SCR com base nas classificações de riscos dos devedores - E | 100% |  |
| `TAB_X_SCR_RISCO_DEVEDOR_F` | (X.8.1) Valor Total dos direitos creditórios reportados ao SCR com base nas classificações de riscos dos devedores - F | 100% |  |
| `TAB_X_SCR_RISCO_DEVEDOR_G` | (X.8.1) Valor Total dos direitos creditórios reportados ao SCR com base nas classificações de riscos dos devedores - G | 100% |  |
| `TAB_X_SCR_RISCO_DEVEDOR_H` | (X.8.1) Valor Total dos direitos creditórios reportados ao SCR com base nas classificações de riscos dos devedores - H | 100% |  |
| `TAB_X_SCR_RISCO_OPER_AA` | (X.8.2) Valor total dos direitos creditórios reportados ao SCR com base nas classificações de risco das operações - AA | 100% |  |
| `TAB_X_SCR_RISCO_OPER_A` | (X.8.2) Valor total dos direitos creditórios reportados ao SCR com base nas classificações de risco das operações - A | 100% |  |
| `TAB_X_SCR_RISCO_OPER_B` | (X.8.2) Valor total dos direitos creditórios reportados ao SCR com base nas classificações de risco das operações - B | 100% |  |
| `TAB_X_SCR_RISCO_OPER_C` | (X.8.2) Valor total dos direitos creditórios reportados ao SCR com base nas classificações de risco das operações - C | 100% |  |
| `TAB_X_SCR_RISCO_OPER_D` | (X.8.2) Valor total dos direitos creditórios reportados ao SCR com base nas classificações de risco das operações - D | 100% |  |
| `TAB_X_SCR_RISCO_OPER_E` | (X.8.2) Valor total dos direitos creditórios reportados ao SCR com base nas classificações de risco das operações - E | 100% |  |
| `TAB_X_SCR_RISCO_OPER_F` | (X.8.2) Valor total dos direitos creditórios reportados ao SCR com base nas classificações de risco das operações - F | 100% |  |
| `TAB_X_SCR_RISCO_OPER_G` | (X.8.2) Valor total dos direitos creditórios reportados ao SCR com base nas classificações de risco das operações - G | 100% |  |
| `TAB_X_SCR_RISCO_OPER_H` | (X.8.2) Valor total dos direitos creditórios reportados ao SCR com base nas classificações de risco das operações - H | 100% |  |
| `TAB_X_DEBITO_TRIBUT` | (X.9.1) Valor total dos direitos creditórios cedidos por cedentes que possuem débitos tributários inscritos em dívida Ativa da União | 100% |  |

## Tabela X_1 → `cotistas_serie`

| Campo | Descrição oficial | Cobertura | Observação |
|---|---|---:|---|
| `TAB_X_CLASSE_SERIE` | (X) Classe/Série | 100% |  |
| `TAB_X_NR_COTST` | (X.1) Número de Cotistas | 100% | Conta **posições por veículo**, não pessoas únicas. Um investidor presente em N fundos é contado N vezes. |

## Tabela X_1_1 → `cotistas_tipo`

| Campo | Descrição oficial | Cobertura | Observação |
|---|---|---:|---|
| `TAB_X_NR_COTST_SENIOR_PF` | (X.1.1) Número de Cotistas (Classe Sênior) - Pessoa física | 100% |  |
| `TAB_X_NR_COTST_SENIOR_PJ_NAO_FINANC` | (X.1.1) Número de Cotistas (Classe Sênior) - Pessoa jurídica não-financeira | 100% |  |
| `TAB_X_NR_COTST_SENIOR_BANCO` | (X.1.1) Número de Cotistas (Classe Sênior) - Banco comercial | 100% |  |
| `TAB_X_NR_COTST_SENIOR_CORRETORA_DISTRIB` | (X.1.1) Número de Cotistas (Classe Sênior) - Corretora ou distribuidora | 100% |  |
| `TAB_X_NR_COTST_SENIOR_PJ_FINANC` | (X.1.1) Número de Cotistas (Classe Sênior) - Outras pessoas jurídicas financeiras | 100% |  |
| `TAB_X_NR_COTST_SENIOR_INVNR` | (X.1.1) Número de Cotistas (Classe Sênior) - Investidores não residentes | 100% |  |
| `TAB_X_NR_COTST_SENIOR_EAPC` | (X.1.1) Número de Cotistas (Classe Sênior) - Entidade aberta de previdência complementar | 100% |  |
| `TAB_X_NR_COTST_SENIOR_EFPC` | (X.1.1) Número de Cotistas (Classe Sênior) - Entidade fechada de previdência complementar | 100% |  |
| `TAB_X_NR_COTST_SENIOR_RPPS` | (X.1.1) Número de Cotistas (Classe Sênior) - Regime próprio de previdência dos servidores públicos | 100% |  |
| `TAB_X_NR_COTST_SENIOR_SEGUR` | (X.1.1) Número de Cotistas (Classe Sênior) - Sociedade seguradora ou resseguradora | 100% |  |
| `TAB_X_NR_COTST_SENIOR_CAPITALIZ` | (X.1.1) Número de Cotistas (Classe Sênior) - Sociedade de capitalização e de arrendamento mercantil | 100% |  |
| `TAB_X_NR_COTST_SENIOR_COTA_FIDC` | (X.1.1) Número de Cotistas (Classe Sênior) - Fundos de investimento em cotas de FIDC | 100% |  |
| `TAB_X_NR_COTST_SENIOR_FII` | (X.1.1) Número de Cotistas (Classe Sênior) - Fundos de investimento imobiliário | 100% |  |
| `TAB_X_NR_COTST_SENIOR_OUTRO_FI` | (X.1.1) Número de Cotistas (Classe Sênior) - Outros fundos de investimento | 100% |  |
| `TAB_X_NR_COTST_SENIOR_CLUBE` | (X.1.1) Número de Cotistas (Classe Sênior) - Clubes de investimento | 100% |  |
| `TAB_X_NR_COTST_SENIOR_OUTRO` | (X.1.1) Número de Cotistas (Classe Sênior) - Outros | 100% |  |
| `TAB_X_NR_COTST_SUBORD_PF` | (X.1.2) Número de Cotistas (Classe Subordinada) - Pessoa física | 91% |  |
| `TAB_X_NR_COTST_SUBORD_PJ_NAO_FINANC` | (X.1.2) Número de Cotistas (Classe Subordinada) - Pessoa jurídica não-financeira | 91% |  |
| `TAB_X_NR_COTST_SUBORD_BANCO` | (X.1.2) Número de Cotistas (Classe Subordinada) - Banco comercial | 91% |  |
| `TAB_X_NR_COTST_SUBORD_CORRETORA_DISTRIB` | (X.1.2) Número de Cotistas (Classe Subordinada) - Corretora ou distribuidora | 91% |  |
| `TAB_X_NR_COTST_SUBORD_PJ_FINANC` | (X.1.2) Número de Cotistas (Classe Subordinada) - Outras pessoas jurídicas financeiras | 91% |  |
| `TAB_X_NR_COTST_SUBORD_INVNR` | (X.1.2) Número de Cotistas (Classe Subordinada) - Investidores não residentes | 91% |  |
| `TAB_X_NR_COTST_SUBORD_EAPC` | (X.1.2) Número de Cotistas (Classe Subordinada) - Entidade aberta de previdência complementar | 91% |  |
| `TAB_X_NR_COTST_SUBORD_EFPC` | (X.1.2) Número de Cotistas (Classe Subordinada) - Entidade fechada de previdência complementar | 91% |  |
| `TAB_X_NR_COTST_SUBORD_RPPS` | (X.1.2) Número de Cotistas (Classe Subordinada) - Regime próprio de previdência dos servidores públicos | 91% |  |
| `TAB_X_NR_COTST_SUBORD_SEGUR` | (X.1.2) Número de Cotistas (Classe Subordinada) - Sociedade seguradora ou resseguradora | 91% |  |
| `TAB_X_NR_COTST_SUBORD_CAPITALIZ` | (X.1.2) Número de Cotistas (Classe Subordinada) - Sociedade de capitalização e de arrendamento mercantil | 91% |  |
| `TAB_X_NR_COTST_SUBORD_COTA_FIDC` | (X.1.2) Número de Cotistas (Classe Subordinada) - Fundos de investimento em cotas de FIDC | 91% |  |
| `TAB_X_NR_COTST_SUBORD_FII` | (X.1.2) Número de Cotistas (Classe Subordinada) - Fundos de investimento imobiliário | 91% |  |
| `TAB_X_NR_COTST_SUBORD_OUTRO_FI` | (X.1.2) Número de Cotistas (Classe Subordinada) - Outros fundos de investimento | 91% |  |
| `TAB_X_NR_COTST_SUBORD_CLUBE` | (X.1.2) Número de Cotistas (Classe Subordinada) - Clubes de investimento | 91% |  |
| `TAB_X_NR_COTST_SUBORD_OUTRO` | (X.1.2) Número de Cotistas (Classe Subordinada) - Outros | 91% |  |

## Tabela X_2 → `series_cotas`

| Campo | Descrição oficial | Cobertura | Observação |
|---|---|---:|---|
| `TAB_X_CLASSE_SERIE` | (X) Classe/Série | 100% |  |
| `TIPO_COTA` | — | 100% |  |
| `TAB_X_QT_COTA` | (X) Quantidade de Cotas | 100% |  |
| `TAB_X_VL_COTA` | (X.2) Valor da Cota | 100% |  |
| `VL_SERIE` | — | 100% |  |

## Tabela X_3 → `rentab_cotas`

| Campo | Descrição oficial | Cobertura | Observação |
|---|---|---:|---|
| `TAB_X_CLASSE_SERIE` | (X) Classe/Série | 100% |  |
| `TIPO_COTA` | — | 100% |  |
| `TAB_X_VL_RENTAB_MES` | (X.3) Rentabilidade Apurada no Mês | 100% |  |

## Tabela X_4 → `captacoes`

| Campo | Descrição oficial | Cobertura | Observação |
|---|---|---:|---|
| `TAB_X_TP_OPER` | (X.4) Tipo de Operação | 100% |  |
| `TAB_X_VL_TOTAL` | (X.4) Valor Total | 100% |  |

## Tabela X_5 → `liquidez`

| Campo | Descrição oficial | Cobertura | Observação |
|---|---|---:|---|
| `TAB_X_VL_LIQUIDEZ_0` | (X.5) Ativos com liquidez imediata | 100% |  |
| `TAB_X_VL_LIQUIDEZ_30` | (X.5) Ativos que podem ser liquidados em até 30 dias | 100% |  |
| `TAB_X_VL_LIQUIDEZ_60` | (X.5) Ativos que podem ser liquidados em até 60 dias | 100% |  |
| `TAB_X_VL_LIQUIDEZ_90` | (X.5)  Ativos que podem ser liquidados em até 90 dias | 100% |  |
| `TAB_X_VL_LIQUIDEZ_180` | (X.5) Ativos que podem ser liquidados em até 180 dias | 100% |  |
| `TAB_X_VL_LIQUIDEZ_360` | (X.5) Ativos que podem ser liquidados em até 360 dias | 100% |  |
| `TAB_X_VL_LIQUIDEZ_MAIOR_360` | (X.5) Ativos que podem ser liquidados em mais de 360 dias | 100% |  |

## Tabela X_6 → `desempenho`

| Campo | Descrição oficial | Cobertura | Observação |
|---|---|---:|---|
| `TAB_X_CLASSE_SERIE` | (X) Classe/Série | 100% |  |
| `TAB_X_PR_DESEMP_ESPERADO` | — | 100% | Desempenho declarado como esperado pelo administrador. Comparável ao realizado apenas quando ambos são informados. |
| `TAB_X_PR_DESEMP_REAL` | — | 100% |  |

## Tabela X_7 → `garantias`

| Campo | Descrição oficial | Cobertura | Observação |
|---|---|---:|---|
| `TAB_X_VL_GARANTIA_DIRCRED` | — | 100% | Garantia real sobre os direitos creditórios. Declarada por pouquíssimos veículos: a proteção do investidor vem de subordinação e coobrigação. |
| `TAB_X_PR_GARANTIA_DIRCRED` | — | 100% |  |

## Tabelas derivadas (camada analítica)

| Artefato | Conteúdo | Unidade de análise |
|---|---|---|
| `serie_mercado_mensal.csv` | série 2013-2026 de PL, carteira, cotistas e circularidade | veículo-mês agregado |
| `lente_1..9_*.csv` | as nove lentes de exposição | varia por lente (ver `lentes_catalogo.csv`) |
| `rf2_catalogo.csv` | fichas dos 46 sinais de atenção | sinal |
| `rf2_sinais.csv` | disparos observados | veículo × sinal |
| `rf2_score_veiculo.csv` | score decomposto em seis dimensões | veículo |
| `sacados_concentracao.csv` | concentração por devedor | veículo |
| `rj_matches_cedentes.csv` | vínculos com recuperação judicial | cedente × empresa |
| `backtest_resumo.csv` | desempenho dos sinais antes de eventos | caso × sinal × grupo |
| `painel_dados.json` | tudo que o painel exibe, com evidência por número | indicador |
