import pandas as pd
import matplotlib.pyplot as plt

def calcular_adensamento_r(df_adensamento):
    """
    Calcula os parâmetros de adensamento.
    """
    if 'Tempo (min)' in df_adensamento.columns:
        tempo_min = df_adensamento['Tempo (min)']
    elif 'Tempo (s)' in df_adensamento.columns:
        tempo_min = df_adensamento['Tempo (s)'] / 60.0
    else:
        tempo_min = (df_adensamento['Raiz Tempo (s)'] ** 2) / 60.0

    recalque_mm = df_adensamento['Deslocamento Vertical (mm)']

    # 1. Recalque Final (mm)
    recalque_final = recalque_mm.max()

    # 2. Grau de Consolidação (%)
    u_pct = (recalque_mm / recalque_final) * 100.0

    # 3. Índices de t50 e t90
    idx_50 = (u_pct - 50.0).abs().idxmin()
    idx_90 = (u_pct - 90.0).abs().idxmin()

    t50_min = tempo_min.loc[idx_50]
    t90_min = tempo_min.loc[idx_90]
    rec_50 = recalque_mm.loc[idx_50]
    rec_90 = recalque_mm.loc[idx_90]
    inicio_cisalhamento_min = tempo_min.max()

    return {
        'recalque_final_mm': recalque_final,
        't50_min': t50_min,
        't90_min': t90_min,
        'rec_50_mm': rec_50,
        'rec_90_mm': rec_90,
        'inicio_cisalhamento_min': inicio_cisalhamento_min
    }


def plotar_adensamento(dados_processados, filtro=None, salvar=False):
    """
    Plota as curvas de adensamento com cores distintas e linhas verticais/horizontais em t50 e t90.
    """
    if not dados_processados:
        print("Erro: Nenhum dado fornecido.")
        return

    # Filtragem de ensaios se solicitado
    if filtro is not None:
        dados_filtrados = {
            k: v for k, v in dados_processados.items()
            if str(filtro) in k
        }
        if not dados_filtrados:
            print(f"Aviso: Nenhuma amostra encontrada para o filtro '{filtro}'.")
            return
    else:
        dados_filtrados = dados_processados

    # Ordenação por tensão nominal
    chaves_ord = sorted(
        dados_filtrados.keys(),
        key=lambda k: dados_filtrados[k]['resumo_tecnico'].get('tensao_normal_efetiva_kPa', 0)
    )

    fig, ax = plt.subplots(figsize=(9, 5.5), dpi=150)

    # Paleta de cores distintas para cada ensaio
    cores = ['#1f77b4', '#d62728', '#2ca02c', '#9467bd', '#ff7f0e']

    print("\n" + "="*70)
    print(" 3. Resultados da fase de adensamento")
    print("="*70)
    print(f"{'Ensaio':<10} | {'Recalque final (mm)':<20} | {'t50 (min)':<10} | {'t90 (min)':<10} | {'Início cis. (min)':<18}")
    print("-" * 78)

    for idx, chave in enumerate(chaves_ord):
        amostra = dados_filtrados[chave]
        df_ad = amostra.get('adensamento')
        resumo = amostra.get('resumo_tecnico', {})

        if df_ad is None or df_ad.empty:
            continue

        # Leitura e conversão de tempo
        if 'Tempo (min)' in df_ad.columns:
            tempo_min = df_ad['Tempo (min)']
        elif 'Tempo (s)' in df_ad.columns:
            tempo_min = df_ad['Tempo (s)'] / 60.0
        else:
            tempo_min = (df_ad['Raiz Tempo (s)'] ** 2) / 60.0

        recalque_mm = df_ad['Deslocamento Vertical (mm)']

        # Processamento pelo critério do R
        res_r = calcular_adensamento_r(df_ad)
        resumo.update(res_r)

        # Identificação amigável do ensaio
        if '100' in chave:
            nome_ensaio = "100 kPa"
        elif '200' in chave:
            nome_ensaio = "200 kPa"
        elif '300' in chave:
            nome_ensaio = "300 kPa"
        else:
            nome_ensaio = f"{resumo.get('tensao_normal_nominal', 'N/A')} kPa"

        # Exibição dos resultados formatados
        print(f"{nome_ensaio:<10} | {res_r['recalque_final_mm']:<20.2f} | {res_r['t50_min']:<10.4f} | {res_r['t90_min']:<10.4f} | {res_r['inicio_cisalhamento_min']:<18.4f}")

        cor_curva = cores[idx % len(cores)]

        # Plotagem da curva principal com cor própria
        ax.plot(tempo_min, recalque_mm, color=cor_curva, linestyle='-',
                linewidth=1.8, label=f"{nome_ensaio}")

    # Configuração gráfica
    ax.set_xlabel("Tempo (min)", fontsize=11, labelpad=8)
    ax.set_ylabel("Recalque (mm)", fontsize=11, labelpad=8)

    # Inversão do eixo Y (recalque cresce para baixo)
    ax.invert_yaxis()

    ax.grid(True, linestyle=':', color='gainsboro', alpha=0.8)
    ax.legend(frameon=True, facecolor='white', edgecolor='black', fontsize=9.5)

    for spine in ax.spines.values():
        spine.set_color('black')
        spine.set_linewidth(1.0)

    subtitulo = f"Amostra {filtro}" if filtro else "Todas as Amostras"
    ax.set_title(f"Fase de Adensamento - {subtitulo}", fontsize=12, fontweight='bold', pad=12)

    plt.tight_layout()
    if salvar:
        nome_arq = f"adensamento_{filtro}.png" if filtro else "adensamento_comparativo.png"
        plt.savefig(nome_arq, dpi=300, bbox_inches='tight')
    plt.show()
