import pandas as pd
import numpy as np
from .io import ler

def tensao_ruptura(df_cis, criterio='deformacao_fixa', alvo=10.0, largura_caixa_mm=100.0):
    """
    Calcula a tensão de ruptura considerando a porcentagem de deformação desejada
    e a largura real da caixa lida nos metadados (L0).
    """
    df_cis = df_cis.copy()

    # Garantia de dados numéricos
    for col in ['Deslocamento Horizontal (mm)', 'Tensão Cisalhante (kPa)', 'Tensão Normal (kPa)']:
        if col in df_cis.columns and df_cis[col].dtype == object:
            df_cis[col] = df_cis[col].astype(str).str.replace(',', '.').astype(float)

    # Deformação Horizontal real (%): (ΔL / L0) * 100
    df_cis['Deformacao_Horizontal_%'] = (df_cis['Deslocamento Horizontal (mm)'] / largura_caixa_mm) * 100.0

    if criterio == 'deformacao_fixa':
        desloc_alvo_mm = largura_caixa_mm * (alvo / 100.0)
        idx_ruptura = (df_cis['Deslocamento Horizontal (mm)'] - desloc_alvo_mm).abs().idxmin()
        tipo_criterio = f"{alvo:.1f}% Deformação ({desloc_alvo_mm:.1f} mm)"

    elif criterio == 'pico':
        idx_ruptura = df_cis['Tensão Cisalhante (kPa)'].idxmax()
        tipo_criterio = "Pico Máximo"

    else:  # 'final'
        idx_ruptura = df_cis['Deslocamento Horizontal (mm)'].idxmax()
        tipo_criterio = "Final do Ensaio"

    tau_ruptura = df_cis.loc[idx_ruptura, 'Tensão Cisalhante (kPa)']
    desloc_ruptura = df_cis.loc[idx_ruptura, 'Deslocamento Horizontal (mm)']
    deform_ruptura = df_cis.loc[idx_ruptura, 'Deformacao_Horizontal_%']

    return tau_ruptura, desloc_ruptura, deform_ruptura, tipo_criterio, idx_ruptura


def reduzir_amostras_inteligente(df, idx_ponto_chave, num_pontos_alvo=600):
    """Aplica downsampling inteligente no DataFrame sem perder o ponto de ruptura."""
    if len(df) <= num_pontos_alvo:
        return df.copy()
    fator_passo = len(df) // num_pontos_alvo
    df_reduzido = df.iloc[::fator_passo].copy()
    if idx_ponto_chave not in df_reduzido.index:
        df_ponto = df.loc[[idx_ponto_chave]]
        df_reduzido = pd.concat([df_reduzido, df_ponto]).sort_index()
    return df_reduzido.reset_index(drop=True)


def executar(arquivos_carregados, criterio_ruptura='deformacao_fixa', alvo=10.0, num_pontos_grafico=600):
    """
    Função principal de carregamento e tratamento do lote de ensaios com integração automática de metadados.
    Recebe um dicionário de arquivos (ex: gerado por files.upload() ou carregado via pasta).
    """
    ensaio_processado = {}
    resumo_metadados = []

    for nome_arquivo, conteudo in arquivos_carregados.items():
        meta, df_ad, df_cis = ler(conteudo)

        # Integração automática da largura da caixa (L0) dos metadados
        try:
            largura_caixa_mm = float(str(meta.get('Largura (mm)', '100')).replace(',', '.'))
        except ValueError:
            largura_caixa_mm = 100.0

        # Tratamento de Adensamento
        if df_ad is not None and not df_ad.empty:
            df_ad = df_ad.dropna(subset=['Tempo (s)', 'Deslocamento Vertical (mm)']).sort_values(by='Tempo (s)')
            df_ad['Tempo (min)'] = df_ad['Tempo (s)'] / 60.0
            idx_chv_ad = df_ad['Deslocamento Vertical (mm)'].idxmax()
            df_ad_otimizado = reduzir_amostras_inteligente(df_ad, idx_chv_ad, num_pontos_grafico)
        else:
            df_ad_otimizado = None

        # Tratamento de Cisalhamento
        if df_cis is not None and not df_cis.empty:
            df_cis = df_cis.dropna(subset=['Deslocamento Horizontal (mm)', 'Tensão Cisalhante (kPa)', 'Tensão Normal (kPa)'])
            df_cis = df_cis[df_cis['Deslocamento Horizontal (mm)'] >= 0].reset_index(drop=True)

            tensao_normal_efetiva = df_cis['Tensão Normal (kPa)'].mean()

            tau_r, desloc_r, deform_r, tipo_crit, idx_r = tensao_ruptura(
                df_cis,
                criterio=criterio_ruptura,
                alvo=alvo,
                largura_caixa_mm=largura_caixa_mm
            )

            df_cis_otimizado = reduzir_amostras_inteligente(df_cis, idx_r, num_pontos_grafico)

            resumo_amostra = {
                'tensao_normal_nominal': meta.get('Nome do Corpo De Prova', meta.get('Nome do Corpo de Prova', 'N/A')),
                'largura_caixa_mm': largura_caixa_mm,
                'tensao_normal_efetiva_kPa': tensao_normal_efetiva,
                'tau_ruptura_kPa': tau_r,
                'deslocamento_ruptura_mm': desloc_r,
                'deformacao_ruptura_%': deform_r,
                'criterio_aplicado': tipo_crit
            }
        else:
            df_cis_otimizado = None
            resumo_amostra = {}

        ensaio_processado[nome_arquivo] = {
            'metadados': meta,
            'resumo_tecnico': resumo_amostra,
            'adensamento': df_ad_otimizado,
            'cisalhamento': df_cis_otimizado
        }

        resumo_metadados.append({
            'Arquivo': nome_arquivo,
            'Amostra': meta.get('Nome da Amostra', 'N/A'),
            'CP': resumo_amostra.get('tensao_normal_nominal', 'N/A'),
            'Caixa (mm)': f"{resumo_amostra.get('largura_caixa_mm', 100):.0f} mm",
            'σn Efetiva (kPa)': f"{resumo_amostra.get('tensao_normal_efetiva_kPa', 0):.2f}",
            'τ Ruptura (kPa)': f"{resumo_amostra.get('tau_ruptura_kPa', 0):.2f}",
            'Desloc. (mm)': f"{resumo_amostra.get('deslocamento_ruptura_mm', 0):.2f}",
            'Deformação (%)': f"{resumo_amostra.get('deformacao_ruptura_%', 0):.1f}%",
            'Critério': resumo_amostra.get('criterio_aplicado', 'N/A')
        })

    df_resumo = pd.DataFrame(resumo_metadados)
    return ensaio_processado, df_resumo


def nome_ensaio(ensaio_processado, tensao_alvo='100'):
    """Localiza a chave do arquivo no dicionário com base na tensão alvo."""
    tensao_str = str(tensao_alvo)
    chaves_encontradas = [k for k in ensaio_processado.keys() if tensao_str in k]

    if not chaves_encontradas:
        raise KeyError(f"Nenhum arquivo contendo '{tensao_str}' foi localizado em ensaio_processado.")

    chave_exata = chaves_encontradas[0]
    return ensaio_processado[chave_exata], chave_exata
