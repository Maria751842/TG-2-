import pandas as pd
import pulp
import locale

# Definindo o formato de número desejado
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

# Leitura do arquivo CSV
file_path = 'C:/Users/carva/OneDrive/Área de Trabalho/API 6/Analises.csv'
df = pd.read_csv(file_path, delimiter=';', decimal=',')

# Converter colunas relevantes para o tipo numérico
cols_to_convert = ['QtdTransp', 'VlrFrete']
df[cols_to_convert] = df[cols_to_convert].apply(pd.to_numeric)

# Filtrar os dados pelo incoterm CIF
df_cif = df[df['incoterm'] == 'CIF']

# Agrupar os dados por CodFabrica e CodCliente e calcular a soma de QtdTransp e VlrFrete
grouped = df_cif.groupby(['CodFabrica', 'CodCliente']).agg({'QtdTransp': 'sum', 'VlrFrete': 'sum'}).reset_index()

# Calcular o custo médio por unidade transportada
grouped['Custo Médio por Unidade'] = grouped['VlrFrete'] / grouped['QtdTransp']

# Dados de capacidade anual das fábricas
capacidades = {
    3403208: 90000000,
    3423909: 56000000,
    3424402: 90000000
}

# Dados de demanda anual dos clientes
demandas = {
    2301: 5973721, 2302: 1778080, 2303: 5958798, 2304: 896173, 2305: 3241494, 2306: 3244827,
    2307: 12738726, 2308: 6792503, 2309: 7471374, 2310: 2098730, 2311: 7295028, 2312: 1350774,
    2313: 1439856, 2314: 3977784, 2315: 3666906, 2316: 271034, 2317: 1272373, 2318: 569236,
    2319: 1589336, 2320: 5063433, 2321: 10686204, 2322: 2495205, 2323: 1753764, 2324: 20427048,
    2325: 7828763, 2326: 5788209, 2327: 11836544, 2328: 6145143, 2329: 13860432, 2330: 3482379,
    2331: 4084642, 2332: 10839219, 2333: 1336988, 2334: 1898750, 2335: 14197671, 2336: 1716192,
    2337: 827342, 2338: 2539443, 2339: 1789064, 2340: 973767, 2341: 5304924, 2342: 838856,
    2343: 8150094, 2344: 678417, 2345: 3600095, 2346: 3522678, 2347: 3675315, 2348: 1310374,
    2349: 1761137, 2350: 4402893, 2351: 1331761
}

# Definir as fábricas que podem entregar para cada cliente
fabrica_clientes = {
    3403208: [2301, 2302, 2303, 2304, 2305, 2306, 2307, 2308, 2309, 2310, 2311, 2312, 2313, 2314, 2315, 2316, 2317, 2318, 2319, 2320, 2321, 2322, 2323, 2324, 2325, 2326, 2327, 2328, 2329, 2330, 2331, 2332, 2333, 2334, 2335, 2339, 2340, 2341, 2342, 2343, 2344, 2345, 2346, 2347, 2348, 2349, 2350, 2351],
    3423909: [2305, 2308, 2309, 2310, 2311, 2324, 2325, 2326, 2327, 2328, 2329, 2330, 2331, 2332, 2333, 2334, 2335, 2336, 2337, 2338, 2339, 2340, 2341, 2342, 2343, 2347, 2348, 2349, 2350, 2351],
    3424402: [2301, 2302, 2303, 2304, 2305, 2306, 2307, 2308, 2309, 2310, 2311, 2319, 2320, 2321, 2322, 2323, 2324, 2325, 2326, 2327, 2328, 2329, 2330, 2331, 2332, 2333, 2334, 2335, 2336, 2337, 2338, 2344, 2345, 2346, 2347, 2348, 2349, 2350, 2351]
}

# Formatação dos dados para o problema de otimização
costs = {}
original_transp = {}
for i, row in grouped.iterrows():
    factory = row['CodFabrica']
    client = row['CodCliente']
    if factory in fabrica_clientes and client in fabrica_clientes[factory]:
        costs[(factory, client)] = locale.format_string('%.17f', row['Custo Médio por Unidade'], grouping=True)
        original_transp[(factory, client)] = row['QtdTransp']

# Definição do problema de otimização
prob = pulp.LpProblem("Minimizacao_Custo_Transporte", pulp.LpMinimize)

# Variáveis de decisão
transp_vars = pulp.LpVariable.dicts("Transp", costs.keys(), lowBound=0, cat='Continuous')

# Função objetivo
prob += pulp.lpSum([locale.atof(costs[(f, c)]) * transp_vars[(f, c)] for (f, c) in costs]), "Custo_Total_Transporte"

# Restrições de capacidade das fábricas
for f in capacidades:
    prob += pulp.lpSum([transp_vars[(f, c)] for c in demandas if (f, c) in costs]) <= capacidades[f], f"Capacidade_{f}"

# Restrições de demanda dos clientes
for c in demandas:
    prob += pulp.lpSum([transp_vars[(f, c)] for f in capacidades if (f, c) in costs]) == demandas[c], f"Demanda_{c}"

# Resolver o problema
prob.solve()

# Preparação dos resultados
results = []
for (f, c) in costs:
    qtd_transp = original_transp[(f, c)]
    qtd_transp_otimizada = pulp.value(transp_vars[(f, c)])
    custo_medio_unidade = locale.atof(costs[(f, c)])
    custo_total = qtd_transp * custo_medio_unidade
    custo_medio_unidade_5 = custo_medio_unidade * 1.05
    custo_total_5 = qtd_transp * custo_medio_unidade_5
    results.append([str(int(f)), str(int(c)), locale.format_string('%.17f', qtd_transp, grouping=True), locale.format_string('%.17f', custo_medio_unidade, grouping=True), locale.format_string('%.17f', custo_total, grouping=True), locale.format_string('%.17f', qtd_transp_otimizada, grouping=True), locale.format_string('%.17f', custo_medio_unidade_5, grouping=True), locale.format_string('%.17f', custo_total_5, grouping=True)])

# Criação do DataFrame de resultados
result_df = pd.DataFrame(results, columns=['CodFabrica', 'CodCliente', 'QtdTranspCIF', 'Custo por Unidade', 'Custo Total', 'QtdTransp Otimizada', 'Custo por Unidade com 5%', 'Custo Total com 5%'])

# Exibir os resultados
print(result_df)

# Salvar os resultados em um arquivo CSV na pasta especificada
output_path = 'C:/Users/carva/OneDrive/Área de Trabalho/API 6/Resultados_Otimizacao.csv'
result_df.to_csv(output_path, index=False)