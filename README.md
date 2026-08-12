# geopytec
geopytec library


GeoPyTec é uma biblioteca Python de código aberto desenvolvida para automatizar o processamento, a análise e a visualização de dados de ensaios geotécnicos, com foco especial no Ensaio de Cisalhamento Direto.

Criada para otimizar a rotina de laboratórios de mecânica dos solos e engenheiros geotécnicos, a biblioteca transforma dados brutos (arquivos CSV) em relatórios executivos completos e gráficos no padrão de engenharia em questão de segundos.

Principais Funcionalidades
Leitura Automatizada: Processamento dinâmico de múltiplos arquivos CSV simultaneamente.

Identificação automática de todos os parâmetros inseridos nos arquivos CSV, como: dimensões da caixa, tamanho do corpo de prova etc.

Limpeza e Estruturação: Identificação e tratamento automático de ruídos nos dados brutos do equipamento.

Fase de Adensamento: Plotagem das curvas de adensamento (Deslocamento Vertical x Tempo).

Fase de Cisalhamento: Geração de curvas de Tensão x Deformação horizontal_%, com identificação automática dos pontos de ruptura, de acordo com a orientação do pesquisador: pico, final ou porcentagem.

Envoltória de Resistência: Cálculo automático da Coesão Efetiva (c'), Ângulo de Atrito Efetivo (φ') e coeficiente de determinação (R²) via critério de Mohr-Coulomb.

Geração de Relatórios: Exportação dos parâmetros e resumos técnicos diretamente para planilhas profissionais em Excel (.xlsx).

Como Instalar
Se você estiver utilizando o Google Colab ou o Jupyter Notebook, basta rodar o seguinte comando em uma célula de código:

**!pip install git+https://github.com/Andrekllen08/geopytec.git**

# Em seguida Importar a biblioteca:

import geopytec as gpt
from google.colab import files

Nota: Certifique-se de ter as bibliotecas base instaladas no seu ambiente virtual (pandas, numpy, matplotlib, scipy, openpyxl). Ao instalar via GitHub, o arquivo setup.py instalará essas dependências automaticamente.


Abaixo está o fluxo de trabalho completo para processar um conjunto de ensaios de cisalhamento direto.

 # Upload dos Dados
Para iniciar, importe a biblioteca e faça o upload dos arquivos .csv gerados pelo equipamento (geralmente nomeados como 100kPa.csv, 200kPa.csv e 300kPa.csv).

****import geopytec as gpt
from google.colab import files****

# 1. Abre a interface para selecionar os arquivos CSV no seu computador
print("Faça o upload dos arquivos CSV do ensaio:")
arquivos = files.upload()

2. Processamento
O motor da GeoPyTec vai ler, limpar e organizar todos os dados em um único "fichário" (Dicionário Python) chamado ensaio_processado.

# 2. Processa os dados brutos e gera as tabelas limpas
ensaio_processado, df_resumo = gpt.processamento.executar(arquivos).

# 2.1 df_resumo, apresenta os principais resultados do ensaio de cisalhamento direto drenado
display(df_resumo).

# 3. Visualização e Parâmetros
Com os dados estruturados, você pode gerar todos os gráficos do relatório.

# 3.1 Plota as curvas da fase de Adensamento para todos os arquivos inseridos
gpt.adensamento.plotar_adensamento(ensaio_processado, filtro=None, salvar=False)
# 3.2 Plota a curva de Adensamento de apenas um ensaio a partir do nome do arquivo
gpt.adensamento.plotar_adensamento(ensaio_processado, filtro='nome_arquivo', salvar=False)

# 3.2.1 Exemplo: Econtrando o nome do arquivo usando a função nome_ensaio. Exemplo arquivo de 100Kpa

dados_100, chave=gpt.processamento.nome_ensaio(ensaio_processado, tensao_alvo='100')

gpt.adensamento.plotar_adensamento(ensaio_processado, filtro=chave, salvar=False)


# 3.3 Plota e salva a curva de Adensamento
gpt.adensamento.plotar_adensamento(ensaio_processado, filtro=None, salvar=True)

# 3.3 Plota as curvas de Tensão x Deformação % (Cisalhamento) de todos os arquivos carregados
gpt.cisalhamento.plot_cisalhamento(ensaio_processado, filtro=None, salvar=False).

# 3.4 Plota e salva a curva de Adensamento de apenas um ensaio a partir do nome do arquivo

gpt.cisalhamento.plot_cisalhamento(ensaio_processado, filtro=None, salvar=True ).

# 3.5 Calcula a Envoltória de Mohr-Coulomb e extrai os parâmetros (c', phi', R²)
c, phi, r2 = gpt.cisalhamento.envoltoria(ensaio_processado)

# 4. Gera a planilha com os resultados e faz o download automático
nome_relatorio = gpt.io.exportar_relatorio(ensaio_processado, c_kpa=c, phi_graus=phi)
files.download(nome_relatorio)

# 5. Estrutura de Módulos
A biblioteca foi construída de forma modular para facilitar futuras expansões (como ensaios triaxiais e ensaios de adensamento oedométrico):

gpt.processamento: Motor principal que executa a limpeza, tratamento de strings, conversão de unidades e padronização dos DataFrames.

gpt.adensamento: Módulo de visualização focado nas deformações verticais e raízes de tempo.

gpt.cisalhamento: Módulo de cálculos e visualização focado em tensões cisalhantes, deformações horizontais e critérios de ruptura.

gpt.io: Módulo de Input/Output responsável pela comunicação com o sistema, exportação de planilhas e relatórios (openpyxl).

👨‍💻 Autor
Desenvolvido por André Monteiro Klen.
