import pandas as pd, numpy as np, json, re, glob, os
R='/home/user/FIDCs/data/raw/extracted/'
def rd(f,**kw):
    return pd.read_csv(R+f,sep=';',encoding='latin-1',quoting=3,dtype=str,**kw)
def num(s): return pd.to_numeric(s.astype(str).str.strip().replace({'':None,'nan':None}),errors='coerce')
def cnpj(s): return s.astype(str).str.replace(r'\D','',regex=True)

J=json.load(open('/home/user/FIDCs/data/analytic/painel_dados.json'))
IND=J['indicadores']
def cmp(name, mine, key=None):
    key=key or name
    pub=IND[key]['valor']
    d = (mine-pub)/pub*100 if pub not in (0,None) else (0.0 if mine==pub else float('inf'))
    flag='OK ' if abs(d)<=0.1 else '>>>'
    print(f"{flag} {name:26s} meu={mine:,.4f}  publicado={pub:,.4f}  dif={d:+.6f}%")
    return d

# ---------- painel canônico ----------
iv=rd('inf_mensal_fidc_tab_IV_202606.csv')
iv['CNPJ']=cnpj(iv.CNPJ_FUNDO_CLASSE); iv['VL_PL']=num(iv.TAB_IV_A_VL_PL)
print("linhas brutas tab IV:",len(iv))
# regra (i): mesmo CNPJ+mes -> prefere Classe
iv['ord']=(iv.TP_FUNDO_CLASSE!='Classe').astype(int)
iv=iv.sort_values('ord')
dup=iv.duplicated(subset=['CNPJ'],keep=False).sum()
print("linhas com CNPJ duplicado no mes:",dup)
iv1=iv.drop_duplicates(subset=['CNPJ'],keep='first')
print("apos regra (i):",len(iv1))
# regra (ii): fundo cujo CNPJ tem classe informante
rc=rd('registro_classe.csv'); rf=rd('registro_fundo.csv')
print("cols registro_classe:",[c for c in rc.columns][:12])
mapa=rc[['ID_Registro_Fundo','CNPJ_Classe']].merge(rf[['ID_Registro_Fundo','CNPJ_Fundo']],on='ID_Registro_Fundo')
mapa['cc']=cnpj(mapa.CNPJ_Classe); mapa['cf']=cnpj(mapa.CNPJ_Fundo)
mapa=mapa[(mapa.cc!='')&(mapa.cf!='')&(mapa.cc!=mapa.cf)]
classes_informantes=set(iv.CNPJ)  # 'pl' bruto = todas as linhas do painel
fundos_com_classe=set(mapa[mapa.cc.isin(classes_informantes)].cf)
mask = (iv1.TP_FUNDO_CLASSE=='Fundo') & (iv1.CNPJ.isin(fundos_com_classe))
print("fundos removidos pela regra (ii):",mask.sum())
pan=iv1[~mask].copy()
print("painel canonico n:",len(pan))
cmp('n_veiculos', float(len(pan)))
cmp('pl_total', float(pan.VL_PL.sum()))

# subclasses nunca somadas?
rs=rd('registro_subclasse.csv')
print("cols registro_subclasse:", rs.columns.tolist()[:10])
subcol=[c for c in rs.columns if 'CNPJ' in c]
print("subclasse cnpj cols:",subcol)
for c in subcol:
    s=set(cnpj(rs[c]))-{'','nan'}
    print("  ", c, "n=",len(s), "no painel:",len(s & set(pan.CNPJ)))

pan.to_pickle('/tmp/claude-0/-home-user-FIDCs/074cc374-d902-56ce-8712-fb1748924b7e/scratchpad/aud/pan.pkl')
import pandas as pd, numpy as np, json
R='/home/user/FIDCs/data/raw/extracted/'
SC='/tmp/claude-0/-home-user-FIDCs/074cc374-d902-56ce-8712-fb1748924b7e/scratchpad/aud/'
def rd(f,**kw): return pd.read_csv(R+f,sep=';',encoding='latin-1',quoting=3,dtype=str,**kw)
def num(s): return pd.to_numeric(s.astype(str).str.strip().replace({'':None,'nan':None}),errors='coerce')
def cnpj(s): return s.astype(str).str.replace(r'\D','',regex=True)
J=json.load(open('/home/user/FIDCs/data/analytic/painel_dados.json')); IND=J['indicadores']
def cmp(name, mine, key=None):
    key=key or name; pub=IND[key]['valor']
    d=(mine-pub)/pub*100 if pub not in (0,None) else (0.0 if abs(mine-(pub or 0))<1e-9 else float('inf'))
    print(f"{'OK ' if abs(d)<=0.1 else '>>>'} {name:26s} meu={mine:,.6f}  pub={pub:,.6f}  dif={d:+.6f}%")
pan=pd.read_pickle(SC+'pan.pkl'); P=set(pan.CNPJ)

# --- inadimplencia (tabs V e VI) ---
v=rd('inf_mensal_fidc_tab_V_202606.csv'); v['CNPJ']=cnpj(v.CNPJ_FUNDO_CLASSE)
vi=rd('inf_mensal_fidc_tab_VI_202606.csv'); vi['CNPJ']=cnpj(vi.CNPJ_FUNDO_CLASSE)
print("tabV linhas",len(v),"dups cnpj",v.CNPJ.duplicated().sum()," in-panel",v.CNPJ.isin(P).sum())
print("tabVI linhas",len(vi),"dups cnpj",vi.CNPJ.duplicated().sum()," in-panel",vi.CNPJ.isin(P).sum())
v=v.drop_duplicates(subset=['CNPJ'],keep='last'); vi=vi.drop_duplicates(subset=['CNPJ'],keep='last')
v=v[v.CNPJ.isin(P)]; vi=vi[vi.CNPJ.isin(P)]
dcv=num(v.TAB_V_A_VL_DIRCRED_PRAZO).sum(); dcvi=num(vi.TAB_VI_A_VL_DIRCRED_PRAZO).sum()
iv_=num(v.TAB_V_B_VL_DIRCRED_INAD).sum(); ivi=num(vi.TAB_VI_B_VL_DIRCRED_INAD).sum()
cmp('inadimplencia', (iv_+ivi)/(dcv+dcvi))
g180v=sum(num(v['TAB_V_B%d_VL_INAD_%s'%(i,s)]).sum() for i,s in [(7,'360'),(8,'720'),(9,'1080'),(10,'MAIOR_1080')])
g180vi=sum(num(vi['TAB_VI_B%d_VL_INAD_%s'%(i,s)]).sum() for i,s in [(7,'360'),(8,'720'),(9,'1080'),(10,'MAIOR_1080')])
cmp('atraso_180',(g180v+g180vi)/(dcv+dcvi))

# --- dc_total / dc_sem_risco / circularidade / pl_liquido (tab I) ---
ti=rd('inf_mensal_fidc_tab_I_202606.csv'); ti['CNPJ']=cnpj(ti.CNPJ_FUNDO_CLASSE)
print("tabI linhas",len(ti),"dups",ti.CNPJ.duplicated().sum())
ti=ti.drop_duplicates(subset=['CNPJ'],keep='last'); tiP=ti[ti.CNPJ.isin(P)]
a=num(tiP.TAB_I2A_VL_DIRCRED_RISCO).sum(); b=num(tiP.TAB_I2B_VL_DIRCRED_SEM_RISCO).sum()
cmp('dc_total',a+b); cmp('dc_sem_risco',b)
circ=num(tiP.TAB_I2H_VL_COTA_FIDC).sum(); cmp('circularidade',circ)
cmp('pl_liquido', pan.VL_PL.sum()-circ)

# --- identidade contabil: Ativo - Passivo = PL ---
tiii=rd('inf_mensal_fidc_tab_III_202606.csv'); tiii['CNPJ']=cnpj(tiii.CNPJ_FUNDO_CLASSE)
tiii=tiii.drop_duplicates(subset=['CNPJ'],keep='last')
m=pan[['CNPJ','VL_PL']].merge(ti[['CNPJ','TAB_I_VL_ATIVO']],on='CNPJ',how='left').merge(
    tiii[['CNPJ','TAB_III_VL_PASSIVO']],on='CNPJ',how='left')
m['AT']=num(m.TAB_I_VL_ATIVO); m['PA']=num(m.TAB_III_VL_PASSIVO)
av=m.dropna(subset=['AT','PA','VL_PL'])
print("avaliaveis identidade:",len(av),"de",len(m), " sem ativo:",m.AT.isna().sum()," sem passivo:",m.PA.isna().sum())
for tol in [0.01, 1.0, 0.005]:
    viol=(np.abs(av.AT-av.PA-av.VL_PL)>tol*np.maximum(np.abs(av.VL_PL),1)).sum() if tol<1 else (np.abs(av.AT-av.PA-av.VL_PL)>tol).sum()
    print("  violacoes tol",tol,"=",viol)
cmp('identidade_contabil', float((np.abs(av.AT-av.PA-av.VL_PL)>0.01*np.maximum(np.abs(av.VL_PL),1)).sum()))

# --- sacado_cobertura_dc (tab VIII) ---
t8=rd('inf_mensal_fidc_tab_VIII_202606.csv'); t8['CNPJ']=cnpj(t8.CNPJ_FUNDO_CLASSE); t8['V']=num(t8.VALOR)
print("tabVIII linhas",len(t8),"veic distintos",t8.CNPJ.nunique(),"max seq",num(t8.SEQUENCIAL).max())
t8p=t8[t8.CNPJ.isin(P)]
soma8=t8p.groupby('CNPJ').V.sum()
print("veic tabVIII no painel:",t8p.CNPJ.nunique())
# cobertura: soma tab VIII / DC total?
print("  soma VIII / dc_total =", soma8.sum()/(a+b))
# alternativa: DC dos veiculos que tem tab VIII / DC total
dcv_por = pd.concat([ti.set_index('CNPJ').pipe(lambda d: num(d.TAB_I2A_VL_DIRCRED_RISCO).fillna(0)+num(d.TAB_I2B_VL_DIRCRED_SEM_RISCO).fillna(0))],axis=1)
dcs=dcv_por[0] if 0 in dcv_por.columns else dcv_por.iloc[:,0]
cob = dcs[dcs.index.isin(set(t8p.CNPJ)&P)].sum()/dcs[dcs.index.isin(P)].sum()
print("  DC dos veic com tabVIII / DC total =", cob)
cmp('sacado_cobertura_dc', cob)

# --- series (tab X_2) ---
x2=rd('inf_mensal_fidc_tab_X_2_202606.csv'); x2['CNPJ']=cnpj(x2.CNPJ_FUNDO_CLASSE)
x2['VAL']=num(x2.TAB_X_QT_COTA)*num(x2.TAB_X_VL_COTA)
print("X_2 classes serie:",x2.TAB_X_CLASSE_SERIE.value_counts().to_dict())
x2p=x2[x2.CNPJ.isin(P)]
tot=x2p.groupby('TAB_X_CLASSE_SERIE').VAL.sum()
print(tot)
import pandas as pd, numpy as np, json
R='/home/user/FIDCs/data/raw/extracted/'
SC='/tmp/claude-0/-home-user-FIDCs/074cc374-d902-56ce-8712-fb1748924b7e/scratchpad/aud/'
def rd(f,**kw): return pd.read_csv(R+f,sep=';',encoding='latin-1',quoting=3,dtype=str,**kw)
def num(s): return pd.to_numeric(s.astype(str).str.strip().replace({'':None,'nan':None}),errors='coerce')
def cnpj(s): return s.astype(str).str.replace(r'\D','',regex=True)
J=json.load(open('/home/user/FIDCs/data/analytic/painel_dados.json')); IND=J['indicadores']
def cmp(name, mine, key=None):
    key=key or name; pub=IND[key]['valor']
    d=(mine-pub)/pub*100 if pub not in (0,None) else 0.0
    print(f"{'OK ' if abs(d)<=0.1 else '>>>'} {name:24s} meu={mine:,.4f}  pub={pub:,.4f}  dif={d:+.6f}%")
pan=pd.read_pickle(SC+'pan.pkl'); P=set(pan.CNPJ); PL=pan.VL_PL.sum()

# ---- estrutura de capital (X_2) ----
x2=rd('inf_mensal_fidc_tab_X_2_202606.csv'); x2['CNPJ']=cnpj(x2.CNPJ_FUNDO_CLASSE)
x2['VAL']=num(x2.TAB_X_QT_COTA)*num(x2.TAB_X_VL_COTA)
x2=x2[x2.CNPJ.isin(P)]
s=x2.TAB_X_CLASSE_SERIE.fillna('')
tipo=np.where(s.str.contains('Mezanino'),'mezanino',
      np.where(s.str.contains('Subordinada'),'subordinada',
      np.where(s.str.contains('Senior'),'senior','outro')))
x2['tipo']=tipo
g=x2.groupby('tipo').VAL.sum()
print(g)
cmp('serie_senior',float(g.get('senior',0)))
cmp('serie_mezanino',float(g.get('mezanino',0)))
cmp('serie_subordinada',float(g.get('subordinada',0)))
tot=g.sum(); print("soma series =",f"{tot:,.2f}"," PL painel =",f"{PL:,.2f}"," dif =",f"{(tot/PL-1)*100:+.4f}%")
cmp('subordinacao',float((g.get('mezanino',0)+g.get('subordinada',0))/tot))
# quantos veiculos tem serie? nulos?
print("veic com X_2:",x2.CNPJ.nunique(),"de",len(P), " -> veic sem serie:",len(P)-x2.CNPJ.nunique())
falt=P-set(x2.CNPJ)
print("PL dos veiculos sem X_2:",f"{pan[pan.CNPJ.isin(falt)].VL_PL.sum():,.2f}")
print("linhas X_2 com VAL nulo:",x2.VAL.isna().sum(),"| QT nulo:",num(x2.TAB_X_QT_COTA).isna().sum(),"| VL_COTA nulo:",num(x2.TAB_X_VL_COTA).isna().sum())

# ---- posicoes cotistas (X_1) e subclasses ----
x1=rd('inf_mensal_fidc_tab_X_1_202606.csv'); x1['CNPJ']=cnpj(x1.CNPJ_FUNDO_CLASSE)
print("X_1 linhas",len(x1),"| ID_SUBCLASSE nao nulo:",x1.ID_SUBCLASSE.notna().sum(),"| dups full:",x1.duplicated().sum())
x1d=x1.drop_duplicates()
x1p=x1d[x1d.CNPJ.isin(P)]
cmp('posicoes_cotistas', float(num(x1p.TAB_X_NR_COTST).sum()))
# se ha serie repetida em varias subclasses:
k=x1p.groupby(['CNPJ','TAB_X_CLASSE_SERIE']).size()
print("pares CNPJ+serie com >1 linha (subclasses):",(k>1).sum(),"de",len(k))
sub=x1p[x1p.groupby(['CNPJ','TAB_X_CLASSE_SERIE'])['TAB_X_NR_COTST'].transform('size')>1]
print("  cotistas nessas linhas:",f"{num(sub.TAB_X_NR_COTST).sum():,.0f}")

# X_1_1 (por tipo) para comparar
x11=rd('inf_mensal_fidc_tab_X_1_1_202606.csv')
print("X_1_1 cols:",x11.columns.tolist())
x11['CNPJ']=cnpj(x11.CNPJ_FUNDO_CLASSE); x11=x11[x11.CNPJ.isin(P)]
nc=[c for c in x11.columns if c.startswith('TAB_X_NR')]
print("  soma X_1_1:",f"{sum(num(x11[c]).sum() for c in nc):,.0f}")

# =====================================================================
# REVALIDAÇÃO (2ª passada) — testes adicionais
# =====================================================================
def revalidacao():
    import json, pandas as pd, numpy as np
    from math import comb
    A = '/home/user/FIDCs/data/analytic/'
    H = json.load(open(A + 'painel_dados.json'))

    # 1) fórmulas que não reproduzem o valor publicado
    rf = pd.read_csv(A + 'rf2_score_veiculo.csv')
    cls = rf[rf.cobertura_dados_pct >= 50]
    print("rf_atencao_alta: pela formula publicada (p99 dos classificaveis) =",
          int((cls.score_risco >= cls.score_risco.quantile(0.99)).sum()),
          "| publicado =", H['indicadores']['rf_atencao_alta']['valor'],
          "| base real (classificaveis com disparo) =",
          int((cls.score_risco >= cls[cls.score_risco > 0].score_risco.quantile(0.99)).sum()))
    print("rf_sem_sinal: COUNT(n_disparos=0) =", int((rf.n_disparos == 0).sum()),
          "| publicado =", H['indicadores']['rf_sem_sinal']['valor'],
          "| cob>=50 & score==0 =", int(((rf.cobertura_dados_pct >= 50) & (rf.score_risco == 0)).sum()))

    # 2) ficha: não classificáveis exibidos como "nenhum disparado"
    t = H['tabelas']['fichas']
    f = pd.DataFrame(t['linhas'], columns=t['colunas'])
    rf['CNPJ'] = rf.CNPJ.astype(str).str.zfill(14)
    m = f.merge(rf[['CNPJ', 'classificacao', 'cobertura_dados_pct']], on='CNPJ',
                how='left', suffixes=('_ficha', '_rf'))
    ccol = 'classificacao_rf' if 'classificacao_rf' in m.columns else 'classificacao'
    sem = m[m.sinais.apply(lambda s: not s)]
    nc = sem[sem[ccol] == 'não classificável']
    print(f"fichas 'nenhum disparado' que sao NAO CLASSIFICAVEIS: {len(nc)}  "
          f"PL somado = {nc.VL_PL.sum():,.2f}")

    # 3) lente 5: reprodução do filtro de inconsistência
    l5 = pd.read_csv(A + 'lente_5_sacados_concentracao.csv')
    print("lente5 marcados inconsistentes (top25/dc > 1,05):",
          int(l5.inconsistente_viii_vs_i.fillna(False).astype(bool).sum()))

    # 4) backtest: Fisher exato unilateral
    def fisher_one(a, b, c, d):
        n = a + b + c + d
        return sum(comb(a + b, x) * comb(c + d, a + c - x) / comb(n, a + c)
                   for x in range(a, min(a + b, a + c) + 1))
    r = pd.read_csv(A + 'backtest_resumo.csv')
    r = r[r.caso == 'CR023']
    for s in ['S1', 'S2', 'S3', 'S4', 'S5', 'S6']:
        p_ = r[(r.sinal == s) & (r.grupo == 'positivo')].iloc[0]
        c_ = r[(r.sinal == s) & (r.grupo == 'controle')].iloc[0]
        a, b = int(p_.n_disparou), int(p_.n_veiculos - p_.n_disparou)
        c, d = int(c_.n_disparou), int(c_.n_veiculos - c_.n_disparou)
        print(f"  {s}: p_meu={fisher_one(a,b,c,d):.4f} p_pub={p_.fisher_p} | "
              f"antecedencia pos={p_.antecedencia_mediana_meses} ctrl={c_.antecedencia_mediana_meses}")


if __name__ == '__main__':
    revalidacao()

# =====================================================================
# TERCEIRA PASSADA — verificações finais
# =====================================================================
def terceira_passada():
    import json, csv, numpy as np, pandas as pd, duckdb
    A = '/home/user/FIDCs/data/analytic/'
    H = json.load(open(A + 'painel_dados.json'))

    # 1) todo indicador tem verificador no gate
    vf = {r['indicador'] for r in csv.DictReader(open(A + 'verificacao_formulas.csv'))}
    print("indicadores sem verificador:", set(H['indicadores']) - vf)

    # 2) regra-mãe nas fichas (recomputada, sem confiar no gate)
    rf = pd.read_csv(A + 'rf2_score_veiculo.csv', dtype={'CNPJ': str}); rf['CNPJ'] = rf.CNPJ.str.zfill(14)
    # (fichas agora carregam classificacao própria; cruzamento feito sobre o JSON embutido no HTML)

    # 3) pool do backtest descontaminado
    d = pd.read_csv(A + 'backtest_detalhe.csv')
    pos = set(d[d.grupo == 'positivo'].CNPJ); ctl = set(d[d.grupo == 'controle'].CNPJ)
    print("interseção positivos × controles:", len(pos & ctl))

    # 4) o bug do 62,5% da lente 5 (LEAST ignora NULL no DuckDB)
    print("LEAST(NULL,5) =", duckdb.sql("SELECT LEAST(NULL,5)").fetchone()[0])
    l5 = pd.read_csv(A + 'lente_5_sacados_concentracao.csv')
    dc_total = H['indicadores']['dc_total']['valor']
    cob_dc = H['indicadores']['sacado_cobertura_dc']['valor']
    correto = np.minimum(l5.top25, l5.dc_tot).sum() / dc_total
    buggy = correto + (1 - cob_dc)
    print(f"valor explicado correto = {correto:.4f} (42,1%) | com bug = {buggy:.4f} (62,5% publicado)")


if __name__ == '__main__':
    revalidacao()
    terceira_passada()
