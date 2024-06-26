import pandas as pd #manipular e analisar os dados
import numpy as np #operações matemáticas
import matplotlib as plt #gráficos
import pulp

#define o caminho do arquivo do computador(onde estão osarquivos que quero abrir)
File = file_path = r"C:\Users\maria\OneDrive\Área de Trabalho\TG-2-\assets\codigo"





#abre os arquivos necessários
df = pd.read_csv(File+"/Rotas.csv", sep=',', decimal = '.')
df2 = pd.read_csv(File+"/Clientes.csv", sep=',', decimal = '.')
df3 = pd.read_csv(File+"/Fabricas.csv", sep=',', decimal = '.',encoding ='latin1')

#checagem dos arquivos
##1
df.info() 
##2
df2.info()
##3
df3.info()

#integra o df de Rotas com o df de Clientes e Fabricas - único dataframe
rotas_final = df.merge(df2, left_on='CO.Cliente',right_on='CO.Cliente',how='inner').merge(df3, left_on='CO.Fabrica',right_on='CO.Fabrica',how='inner') 


#checagem do df final
rotas_final.info()

#visualiza o df final
rotas_final.head(5)

#cria nova coluna com condição
rotas_final['Capacidade'] = None
rotas_final.loc[rotas_final['Veiculo'] == 'P24', 'Capacidade'] = 3600
rotas_final.loc[rotas_final['Veiculo'] == 'P12', 'Capacidade'] = 1800

#cria nova coluna com cálculo
rotas_final['Produtividade'] = rotas_final['Qtd.Transp'] / rotas_final['Capacidade'] * 100

#Análises
##filtros

fabricas = rotas_final['CO.Fabrica'].unique()
print(fabricas)

#análise segmentada de uma fábrica

co_fabrica = 3424402
incoterm = 'CIF'

df_filtrado = rotas_final[(rotas_final['CO.Fabrica'] == co_fabrica) & (rotas_final['Incoterm'] == incoterm)]

clientes = df_filtrado['CO.Cliente'].unique()
print(clientes)

#Exportar a lista de clientes
with open('clientes.txt', 'w') as file:
	for client in clientes:
		file.write(str(client) + '\n')


#frete médio por fábrica e cliente


df_filtrado['frete/unidade'] = df_filtrado['Vlr.Frete'] / df_filtrado['Qtd.Transp']
frete_media = df_filtrado.groupby(['CO.Fabrica', 'CO.Cliente'])['frete/unidade'].mean().reset_index()
frete_media.info()
print(frete_media)

frete_media.to_csv(File+'/Frete.csv', index=False)
#####


#exporta o novo df para csv
rotas_final.to_csv(File+'/Rotas_final.csv', index=False)



#abre os arquivos necessários para fazer o novo merge
df_final = pd.read_csv(File +"/Rotas_final.csv", sep=',', decimal = '.')
df_indice = pd.read_csv(File +"/VRP.csv",sep=';',decimal = '.')


#cria nova coluna na planilha Rota_final para fazer a concatenacao da fábrica com cliente
df_final['Indice'] = df_final['CO.Fabrica'].astype(str) +"-"+ df_final['CO.Cliente'].astype(str)


# Realizar o merge entre df_final e df_indice
rotas_final = df_final.merge(df_indice, on='Indice', how='inner')

# Aqui começa a fazer o filtro da coluna Incoterm, verifica se é FOB e se o valor do frete é maior que zero

# Cria uma máscara booleana para as linhas onde 'Incoterm' é "FOB"
mascara_incoterm_fob = rotas_final['Incoterm'] == 'FOB'

# Cria uma máscara booleana para as linhas onde 'Vlr.Frete' é maior que 0
mascara_vlr_frete_maior_que_zero = rotas_final['Vlr.Frete'] > 0

# Combina as duas máscaras usando o operador lógico E (&)
# Ou seja, queremos as linhas onde ambas as condições são verdadeiras
mascara_combinada = mascara_incoterm_fob & mascara_vlr_frete_maior_que_zero

# Aplica a máscara combinada, selecionando as linhas onde ambas as condições são falsas, ou seja, coloca apenas as linhas onde o FOB é 0
linhas_selecionadas = rotas_final.loc[~mascara_combinada]

# Substitui o DataFrame original pelas linhas selecionadas
rotas_final = linhas_selecionadas

#Faz a comparação da distancia da tabela indice com a Distancia já existente na rota final
rotas_final['Comparacao']= rotas_final['Distance'].astype(float) / df_final['Dist'].astype(float)


#cria nova coluna na planilha Rota_final para fazer a concatenacao da fábrica com cliente
rotas_final['Dias entrega'] = (pd.to_datetime(rotas_final['Dt.Entrega'], format='%d/%m/%y') - pd.to_datetime(rotas_final['Dt.Emissao'], format='%d/%m/%y')).dt.days

# Cria uma máscara booleana para as linhas onde 'Incoterm' é "FOB"
mascara_dia_menor_zero= rotas_final['Dias entrega'] < 0

# Armazena as datas de entrega originais em uma variável separada
datas_entrega_originais = rotas_final.loc[mascara_dia_menor_zero, 'Dt.Entrega']

# Substitui as datas de entrega pelas datas de emissão onde 'Dias entrega' é menor que zero
rotas_final.loc[mascara_dia_menor_zero, 'Dt.Entrega'] = rotas_final.loc[mascara_dia_menor_zero, 'Dt.Emissao']

# Substitui as datas de emissão pelas datas de entrega originais onde 'Dias entrega' é menor que zero
rotas_final.loc[mascara_dia_menor_zero, 'Dt.Emissao'] = datas_entrega_originais

# Cria novamente a coluna para verificação se existe a possibilidade de entregas menores que 0
rotas_final['Dias entrega'] = (pd.to_datetime(rotas_final['Dt.Entrega'], format='%d/%m/%y') - pd.to_datetime(rotas_final['Dt.Emissao'], format='%d/%m/%y')).dt.days


#Cria a nova coluna para achar a média do transporte
rotas_final['Media transporte'] = rotas_final['Vlr.Frete'].astype(float) / rotas_final['Qtd.Transp'].astype(float)

#Cria a nova coluna para achar a média do transporte do próximo ano
rotas_final['Media próximo ano'] = rotas_final['Media transporte'].astype(float) * 1.05


df_filtrado = rotas_final[rotas_final['Media próximo ano'] > 0]

print(df_filtrado.head(10))

#exporta o novo df para csv
rotas_final.to_csv(File+'/Rotas_final.csv', index=False)


# Inicializando o problema de minimização
prob = pulp.LpProblem("Custos_de_Transporte", pulp.LpMinimize)

# Função objetivo
for _, row in df_final.iterrows():
    if row["Vlr.Frete"] != 0:  # Verifica se o valor de frete é diferente de zero
        prob += (row["Dist"] * row["Qtd.Transp"]) / row["Vlr.Frete"]
    else:
        prob += 0  # Define o custo da remessa como zero se o valor de frete for zero

# Restrições
for index, row in df_final.iterrows():
    qtd_transp = row["Qtd.Transp"]
    capacidade = row["Capacidade"]
    if qtd_transp <= capacidade:
        prob += qtd_transp <= capacidade

# Resolvendo o problema
prob.solve()

# Adicionando os resultados ao DataFrame
df_final["Custo_Remessa"] = 0  # Inicializa a coluna com zeros
for index, row in df_final.iterrows():
    if row["Vlr.Frete"] != 0:
        df_final.at[index, "Custo_Remessa"] = (row["Dist"] * row["Qtd.Transp"]) / row["Vlr.Frete"]

df_final["Custo_Total"] = df_final["Custo_Remessa"]

# Salvando o DataFrame atualizado no mesmo arquivo CSV
df_final.to_csv(File + "/Rotas_final.csv", index=False)

print("Arquivo 'Rotas_final.csv' atualizado com sucesso.")