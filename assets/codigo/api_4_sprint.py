import pandas as pd #manipular e analisar os dados
import numpy as np #operações matemáticas
import matplotlib as plt #gráficos
from pulp import *

#define o caminho do arquivo do computador(onde estão osarquivos que quero abrir)
File = r"./dados/Dados API 6"

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
rotas_final.to_csv(File + '/Rotas_final.csv', index=False)



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
rotas_final.to_csv(File +'/Rotas_final.csv', index=False)


df_final = pd.read_csv(File +"/Rotas_final.csv", sep=',', decimal = '.')

# Inicializando o problema de minimização
prob = pulp.LpProblem("Custos_de_Transporte", LpMinimize)

# Variáveis do problema
x11 = LpVariable("x11 ",lowBound = 0)
x12= LpVariable("x12",lowBound = 0)
x13= LpVariable("x13",lowBound = 0)
x14= LpVariable("x14",lowBound = 0)
x15= LpVariable("x15",lowBound = 0)
x16= LpVariable("x16",lowBound = 0)
x17= LpVariable("x17",lowBound = 0)
x18= LpVariable("x18",lowBound = 0)
x19= LpVariable("x19",lowBound = 0)
x110= LpVariable("x110",lowBound = 0)
x111= LpVariable("x111",lowBound = 0)
x112= LpVariable("x112",lowBound = 0)
x113= LpVariable("x113",lowBound = 0)
x114= LpVariable("x114",lowBound = 0)
x115= LpVariable("x115",lowBound = 0)
x116= LpVariable("x116",lowBound = 0)
x117= LpVariable("x117",lowBound = 0)
x118= LpVariable("x118",lowBound = 0)
x119= LpVariable("x119",lowBound = 0)
x120= LpVariable("x120",lowBound = 0)
x121= LpVariable("x121",lowBound = 0)
x122= LpVariable("x122",lowBound = 0)
x123= LpVariable("x123",lowBound = 0)
x124= LpVariable("x124",lowBound = 0)
x125= LpVariable("x125",lowBound = 0)
x126= LpVariable("x126",lowBound = 0)
x127= LpVariable("x127",lowBound = 0)
x128= LpVariable("x128",lowBound = 0)
x129= LpVariable("x129",lowBound = 0)
x130= LpVariable("x130",lowBound = 0)
x131= LpVariable("x131",lowBound = 0)
x132= LpVariable("x132",lowBound = 0)
x133= LpVariable("x133",lowBound = 0)
x134= LpVariable("x134",lowBound = 0)
x135= LpVariable("x135",lowBound = 0)
x136= LpVariable("x136",lowBound = 0)
x137= LpVariable("x137",lowBound = 0)
x138= LpVariable("x138",lowBound = 0)
x139= LpVariable("x139",lowBound = 0)
x140= LpVariable("x140",lowBound = 0)
x141= LpVariable("x141",lowBound = 0)
x142= LpVariable("x142",lowBound = 0)
x143= LpVariable("x143",lowBound = 0)
x144= LpVariable("x144",lowBound = 0)
x145= LpVariable("x145",lowBound = 0)
x146= LpVariable("x146",lowBound = 0)
x147= LpVariable("x147",lowBound = 0)
x148= LpVariable("x148",lowBound = 0)
x149= LpVariable("x149",lowBound = 0)
x150= LpVariable("x150",lowBound = 0)
x151= LpVariable("x151",lowBound = 0)
x21= LpVariable("x21",lowBound = 0)
x22= LpVariable("x22",lowBound = 0)
x23= LpVariable("x23",lowBound = 0)
x24= LpVariable("x24",lowBound = 0)
x25= LpVariable("x25",lowBound = 0)
x26= LpVariable("x26",lowBound = 0)
x27= LpVariable("x27",lowBound = 0)
x28= LpVariable("x28",lowBound = 0)
x29= LpVariable("x29",lowBound = 0)
x210= LpVariable("x210",lowBound = 0)
x211= LpVariable("x211",lowBound = 0)
x212= LpVariable("x212",lowBound = 0)
x213= LpVariable("x213",lowBound = 0)
x214= LpVariable("x214",lowBound = 0)
x215= LpVariable("x215",lowBound = 0)
x216= LpVariable("x216",lowBound = 0)
x217= LpVariable("x217",lowBound = 0)
x218= LpVariable("x218",lowBound = 0)
x219= LpVariable("x219",lowBound = 0)
x220= LpVariable("x220",lowBound = 0)
x221= LpVariable("x221",lowBound = 0)
x222= LpVariable("x222",lowBound = 0)
x223= LpVariable("x223",lowBound = 0)
x224= LpVariable("x224",lowBound = 0)
x225= LpVariable("x225",lowBound = 0)
x226= LpVariable("x226",lowBound = 0)
x227= LpVariable("x227",lowBound = 0)
x228= LpVariable("x228",lowBound = 0)
x229= LpVariable("x229",lowBound = 0)
x230= LpVariable("x230",lowBound = 0)
x231= LpVariable("x231",lowBound = 0)
x232= LpVariable("x232",lowBound = 0)
x233= LpVariable("x233",lowBound = 0)
x234= LpVariable("x234",lowBound = 0)
x235= LpVariable("x235",lowBound = 0)
x236= LpVariable("x236",lowBound = 0)
x237= LpVariable("x237",lowBound = 0)
x238= LpVariable("x238",lowBound = 0)
x239= LpVariable("x239",lowBound = 0)
x240= LpVariable("x240",lowBound = 0)
x241= LpVariable("x241",lowBound = 0)
x242= LpVariable("x242",lowBound = 0)
x243= LpVariable("x243",lowBound = 0)
x244= LpVariable("x244",lowBound = 0)
x245= LpVariable("x245",lowBound = 0)
x246= LpVariable("x246",lowBound = 0)
x247= LpVariable("x247",lowBound = 0)
x248= LpVariable("x248",lowBound = 0)
x249= LpVariable("x249",lowBound = 0)
x250= LpVariable("x250",lowBound = 0)
x251= LpVariable("x251",lowBound = 0)
x31= LpVariable("x31",lowBound = 0)
x32= LpVariable("x32",lowBound = 0)
x33= LpVariable("x33",lowBound = 0)
x34= LpVariable("x34",lowBound = 0)
x35= LpVariable("x35",lowBound = 0)
x36= LpVariable("x36",lowBound = 0)
x37= LpVariable("x37",lowBound = 0)
x38= LpVariable("x38",lowBound = 0)
x39= LpVariable("x39",lowBound = 0)
x310= LpVariable("x310",lowBound = 0)
x311= LpVariable("x311",lowBound = 0)
x312= LpVariable("x312",lowBound = 0)
x313= LpVariable("x313",lowBound = 0)
x314= LpVariable("x314",lowBound = 0)
x315= LpVariable("x315",lowBound = 0)
x316= LpVariable("x316",lowBound = 0)
x317= LpVariable("x317",lowBound = 0)
x318= LpVariable("x318",lowBound = 0)
x319= LpVariable("x319",lowBound = 0)
x320= LpVariable("x320",lowBound = 0)
x321= LpVariable("x321",lowBound = 0)
x322= LpVariable("x322",lowBound = 0)
x323= LpVariable("x323",lowBound = 0)
x324= LpVariable("x324",lowBound = 0)
x325= LpVariable("x325",lowBound = 0)
x326= LpVariable("x326",lowBound = 0)
x327= LpVariable("x327",lowBound = 0)
x328= LpVariable("x328",lowBound = 0)
x329= LpVariable("x329",lowBound = 0)
x330= LpVariable("x330",lowBound = 0)
x331= LpVariable("x331",lowBound = 0)
x332= LpVariable("x332",lowBound = 0)
x333= LpVariable("x333",lowBound = 0)
x334= LpVariable("x334",lowBound = 0)
x335= LpVariable("x335",lowBound = 0)
x336= LpVariable("x336",lowBound = 0)
x337= LpVariable("x337",lowBound = 0)
x338= LpVariable("x338",lowBound = 0)
x339= LpVariable("x339",lowBound = 0)
x340= LpVariable("x340",lowBound = 0)
x341= LpVariable("x341",lowBound = 0)
x342= LpVariable("x342",lowBound = 0)
x343= LpVariable("x343",lowBound = 0)
x344= LpVariable("x344",lowBound = 0)
x345= LpVariable("x345",lowBound = 0)
x346= LpVariable("x346",lowBound = 0)
x347= LpVariable("x347",lowBound = 0)
x348= LpVariable("x348",lowBound = 0)
x349= LpVariable("x349",lowBound = 0)
x350= LpVariable("x350",lowBound = 0)
x351= LpVariable("x351",lowBound = 0)

df_filtrado = df_final[df_final["Incoterm"] != "FOB"]

custo_medio_por_unidade = np.average(df_filtrado["Media próximo ano"])

# Definindo a função objetivo
prob += x11 * custo_medio_por_unidade + x12 * custo_medio_por_unidade + x13 * custo_medio_por_unidade + x14 * custo_medio_por_unidade + x15 * custo_medio_por_unidade + x16 * custo_medio_por_unidade + x17 * custo_medio_por_unidade + x18 * custo_medio_por_unidade + x19 * custo_medio_por_unidade + x110 * custo_medio_por_unidade + x111 * custo_medio_por_unidade + x112 * custo_medio_por_unidade + x113 * custo_medio_por_unidade + x114 * custo_medio_por_unidade + x115 * custo_medio_por_unidade + x116 * custo_medio_por_unidade + x117 * custo_medio_por_unidade + x118 * custo_medio_por_unidade + x119 * custo_medio_por_unidade + x120 * custo_medio_por_unidade + x121 * custo_medio_por_unidade + x122 * custo_medio_por_unidade + x123 * custo_medio_por_unidade + x124 * custo_medio_por_unidade + x125 * custo_medio_por_unidade + x126 * custo_medio_por_unidade + x127 * custo_medio_por_unidade + x128 * custo_medio_por_unidade + x129 * custo_medio_por_unidade + x130 * custo_medio_por_unidade + x131 * custo_medio_por_unidade + x132 * custo_medio_por_unidade + x133 * custo_medio_por_unidade + x134 * custo_medio_por_unidade + x135 * custo_medio_por_unidade + x136 * custo_medio_por_unidade + x137 * custo_medio_por_unidade + x138 * custo_medio_por_unidade + x139 * custo_medio_por_unidade + x140 * custo_medio_por_unidade + x141 * custo_medio_por_unidade + x142 * custo_medio_por_unidade + x143 * custo_medio_por_unidade + x144 * custo_medio_por_unidade + x145 * custo_medio_por_unidade + x146 * custo_medio_por_unidade + x147 * custo_medio_por_unidade + x148 * custo_medio_por_unidade + x149 * custo_medio_por_unidade + x150 * custo_medio_por_unidade + x151 * custo_medio_por_unidade + x21 * custo_medio_por_unidade + x22 * custo_medio_por_unidade + x23 * custo_medio_por_unidade + x24 * custo_medio_por_unidade + x25 * custo_medio_por_unidade + x26 * custo_medio_por_unidade + x27 * custo_medio_por_unidade + x28 * custo_medio_por_unidade + x29 * custo_medio_por_unidade + x210 * custo_medio_por_unidade + x211 * custo_medio_por_unidade + x212 * custo_medio_por_unidade + x213 * custo_medio_por_unidade + x214 * custo_medio_por_unidade + x215 * custo_medio_por_unidade + x216 * custo_medio_por_unidade + x217 * custo_medio_por_unidade + x218 * custo_medio_por_unidade + x219 * custo_medio_por_unidade + x220 * custo_medio_por_unidade + x221 * custo_medio_por_unidade + x222 * custo_medio_por_unidade + x223 * custo_medio_por_unidade + x224 * custo_medio_por_unidade + x225 * custo_medio_por_unidade + x226 * custo_medio_por_unidade + x227 * custo_medio_por_unidade + x228 * custo_medio_por_unidade + x229 * custo_medio_por_unidade + x230 * custo_medio_por_unidade + x231 * custo_medio_por_unidade + x232 * custo_medio_por_unidade + x233 * custo_medio_por_unidade + x234 * custo_medio_por_unidade + x235 * custo_medio_por_unidade + x236 * custo_medio_por_unidade + x237 * custo_medio_por_unidade + x238 * custo_medio_por_unidade + x239 * custo_medio_por_unidade + x240 * custo_medio_por_unidade + x241 * custo_medio_por_unidade + x242 * custo_medio_por_unidade + x243 * custo_medio_por_unidade + x244 * custo_medio_por_unidade + x245 * custo_medio_por_unidade + x246 * custo_medio_por_unidade + x247 * custo_medio_por_unidade + x248 * custo_medio_por_unidade + x249 * custo_medio_por_unidade + x250 * custo_medio_por_unidade + x251 * custo_medio_por_unidade + x31 * custo_medio_por_unidade + x32 * custo_medio_por_unidade + x33 * custo_medio_por_unidade + x34 * custo_medio_por_unidade + x35 * custo_medio_por_unidade + x36 * custo_medio_por_unidade + x37 * custo_medio_por_unidade + x38 * custo_medio_por_unidade + x39 * custo_medio_por_unidade + x310 * custo_medio_por_unidade + x311 * custo_medio_por_unidade + x312 * custo_medio_por_unidade + x313 * custo_medio_por_unidade + x314 * custo_medio_por_unidade + x315 * custo_medio_por_unidade + x316 * custo_medio_por_unidade + x317 * custo_medio_por_unidade + x318 * custo_medio_por_unidade + x319 * custo_medio_por_unidade + x320 * custo_medio_por_unidade + x321 * custo_medio_por_unidade + x322 * custo_medio_por_unidade + x323 * custo_medio_por_unidade + x324 * custo_medio_por_unidade + x325 * custo_medio_por_unidade + x326 * custo_medio_por_unidade + x327 * custo_medio_por_unidade + x328 * custo_medio_por_unidade + x329 * custo_medio_por_unidade + x330 * custo_medio_por_unidade + x331 * custo_medio_por_unidade + x332 * custo_medio_por_unidade + x333 * custo_medio_por_unidade + x334 * custo_medio_por_unidade + x335 * custo_medio_por_unidade + x336 * custo_medio_por_unidade + x337 * custo_medio_por_unidade + x338 * custo_medio_por_unidade + x339 * custo_medio_por_unidade + x340 * custo_medio_por_unidade + x341 * custo_medio_por_unidade + x342 * custo_medio_por_unidade + x343 * custo_medio_por_unidade + x344 * custo_medio_por_unidade + x345 * custo_medio_por_unidade + x346 * custo_medio_por_unidade + x347 * custo_medio_por_unidade + x348 * custo_medio_por_unidade + x349 * custo_medio_por_unidade + x350 * custo_medio_por_unidade + x351 * custo_medio_por_unidade

# Restrições


# Ver a estrutura do problema
prob

# Resolvendo o problema
prob.solve()

for v in prob.variables():
	print(v.name, "=", v.varValue)
	
print("Custo total = ",value(prob.objective))