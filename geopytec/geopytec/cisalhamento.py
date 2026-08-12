import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress

# ====================================================================
# FUNÇÃO 1: CISALHAMENTO
# ====================================================================
def plot_cisalhamento(ensaio_processado, filtro=None, salvar_figura=False):
    """
    Plota o gráfico comparativo ou individual de cisalhamento no padrão de relatório.
    """
    if not ensaio_processado:
        print("Erro: Nenhum dado de ensaio encontrado em ensaio_processado.")
        return

    # 1. Aplicação do Filtro (Se informado)
    if filtro is not None:
        dados_filtrados = {
            k: v for k, v in ensaio_processado.items()
            if str(filtro) in k
        }
        if not dados_filtrados:
            print(f"Aviso: Nenhuma amostra encontrada para o filtro '{filtro}'.")
            return
    else:
        dados_filtrados = ensaio_processado

    fig, ax = plt.subplots(figsize=(10, 6), dpi=150)
    cores = ['#1f77b4', '#d62728', '#2ca02c', '#9467bd', '#ff7f0e']
    estilos_linha = ['-', '-', '-','-','-']

    deform_alvo_ref = None
    crit_nome_ref = ""

    # Ordena as amostras selecionadas pela tensão normal
    chaves_ordenadas = sorted(
        dados_filtrados.keys(),
        key=lambda k: dados_filtrados[k]['resumo_tecnico'].get('tensao_normal_efetiva_kPa', 0)
    )

    for idx, nome_arquivo in enumerate(chaves_ordenadas):
        dados = dados_filtrados[nome_arquivo]
        df_cis = dados.get('cisalhamento')
        resumo = dados.get('resumo_tecnico', {})

        if df_cis is None or df_cis.empty:
            continue

        # Garante o cálculo da Deformação Horizontal (%)
        largura_caixa = resumo.get('largura_caixa_mm', 100.0)
        df_cis['Deformacao_%'] = (df_cis['Deslocamento Horizontal (mm)'] / largura_caixa) * 100.0

        deform = df_cis['Deformacao_%']
        tau = df_cis['Tensão Cisalhante (kPa)']

        # Dados da Ruptura
        tau_r = resumo.get('tau_ruptura_kPa', 0)
        deform_r = resumo.get('deformacao_ruptura_%', 10.0)
        sn_nominal = resumo.get('tensao_normal_nominal', 'N/A')

        if deform_alvo_ref is None:
            deform_alvo_ref = deform_r
            crit_nome_ref = resumo.get('criterio_aplicado', '10% Deformação')
        cor = cores[idx % len(cores)]
        estilo = estilos_linha[idx % len(estilos_linha)]

        # 1. Curva Tensão x Deformação (Linha Preta)
        ax.plot(deform, tau, color=cor, linestyle=estilo, linewidth=1.5)

        # 2. Ponto de Ruptura (Círculo Vermelho com Borda Preta)
        ax.scatter([deform_r], [tau_r], color='red', edgecolor='black', s=50, zorder=5)

        # 3. Valor da Tensão sobre o Ponto de Ruptura
        ax.annotate(f"{tau_r:.1f} kPa",
                    xy=(deform_r, tau_r),
                    xytext=(0, 7),
                    textcoords='offset points',
                    ha='center', va='bottom',
                    fontsize=9.5, fontweight='bold', color='black')

        # 4. Rótulo da Tensão Normal na extremidade da curva
        ult_x = deform.iloc[-1]
        ult_y = tau.iloc[-1]

        if '100' in str(sn_nominal) or '100' in nome_arquivo:
            label_sn = r"$\sigma_n = 100\text{ kPa}$"
        elif '200' in str(sn_nominal) or '200' in nome_arquivo:
            label_sn = r"$\sigma_n = 200\text{ kPa}$"
        elif '300' in str(sn_nominal) or '300' in nome_arquivo:
            label_sn = r"$\sigma_n = 300\text{ kPa}$"
        else:
            label_sn = f"$\\sigma_n = {resumo.get('tensao_normal_efetiva_kPa', 0):.0f}\\text{{ kPa}}$"

        ax.annotate(label_sn,
                    xy=(ult_x, ult_y),
                    xytext=(5, -2),
                    textcoords='offset points',
                    ha='left', va='center',
                    fontsize=10, color='black')

    # 5. Linha vertical pontilhada indicando a deformação de corte
    if deform_alvo_ref is not None:
        ax.axvline(x=deform_alvo_ref, color='gray', linestyle=':', linewidth=0.8, alpha=0.7)

    # Ajuste dinâmico do Título
    subtitulo = f"Amostra {filtro}" if filtro else f"Deformação horizontal {deform_alvo_ref:.0f}%"
    ax.set_title(f"Curvas tensão × deformação - {subtitulo}",
                 fontsize=12, fontweight='bold', pad=15)

    ax.set_xlabel("Deformação horizontal (%)", fontsize=11, labelpad=10)
    ax.set_ylabel(r"$\tau\text{ (kPa)}$", fontsize=11, labelpad=10)

    ax.set_xlim(0, 22)
    ax.set_ylim(bottom=0)
    ax.grid(True, linestyle=':', color='gainsboro', alpha=0.8)

    for spine in ax.spines.values():
        spine.set_color('black')
        spine.set_linewidth(1.0)

    plt.tight_layout()
    if salvar_figura:
        nome_arq = f"cisalhamento_{filtro}.png" if filtro else "cisalhamento_comparativo.png"
        plt.savefig(nome_arq, dpi=300, bbox_inches='tight')
    plt.show()


# ====================================================================
# FUNÇÃO 2: ENVOLTÓRIA DE MOHR-COULOMB
# ====================================================================
def envoltoria(dados_processados, criterio_escolhido="Deformação horizontal 10%", salvar=False):
    """
    Calcula a Envoltória de Mohr-Coulomb (c' e phi') e plota o gráfico
    no padrão exato do relatório do R.
    """
    if not dados_processados:
        print("Erro: Nenhum dado fornecido.")
        return

    sigmas = []
    taus = []

    # Extrai os pares (sigma_n, tau_ruptura) do dicionário
    for chave, amostra in dados_processados.items():
        resumo = amostra.get('resumo_tecnico', {})

        sigma = resumo.get('tensao_normal_efetiva_kPa', 0)
        if sigma == 0:
            if '100' in chave: sigma = 100
            elif '200' in chave: sigma = 200
            elif '300' in chave: sigma = 300

        tau = resumo.get('tau_ruptura_kPa', 0)

        if tau > 0:
            sigmas.append(sigma)
            taus.append(tau)

    sigmas = np.array(sigmas)
    taus = np.array(taus)

    if len(sigmas) < 2:
        print("Erro: Necessário ao menos 2 pontos para ajustar a envoltória.")
        return

    regressao = linregress(sigmas, taus)
    c_kpa = regressao.intercept
    tan_phi = regressao.slope
    phi_graus = np.degrees(np.arctan(tan_phi))
    r2 = regressao.rvalue ** 2

    # Exibição da Tabela no Terminal
    print("\n" + "="*50)
    print(" 5. Envoltória de resistência")
    print(" A envoltória foi ajustada segundo Mohr-Coulomb.")
    print("="*50)
    print(f"{'Parâmetro':<30} | {'Valor':<15}")
    print("-" * 48)
    print(f"{'Coesão efetiva (c\')':<30} | {c_kpa:.2f} kPa")
    print(f"{'Ângulo de atrito efetivo (φ\')':<30} | {phi_graus:.2f}°")
    print(f"{'R²':<30} | {r2:.2f}")
    print("-" * 48)
    print(f" Equação ajustada: τ = {c_kpa:.2f} + σn·tan({phi_graus:.2f}°)")
    print("="*50 + "\n")

    # Plotagem do Gráfico
    fig, ax = plt.subplots(figsize=(8, 5), dpi=150)

    xmax = 400
    ymax = 260
    x_reta = np.linspace(0, xmax, 100)
    y_reta = c_kpa + tan_phi * x_reta

    ax.plot(x_reta, y_reta, color='red', linewidth=1.5, zorder=2)
    ax.scatter(sigmas, taus, color='black', s=45, zorder=4)

    texto_box = f"$c = {c_kpa:.2f}\\text{{ kPa}}$\n$\\phi = {phi_graus:.2f}^\\circ$\n$R^2 = {r2:.0f}$" if r2 == 1 else f"$c = {c_kpa:.2f}\\text{{ kPa}}$\n$\\phi = {phi_graus:.2f}^\\circ$\n$R^2 = {r2:.4f}$"

    ax.text(0.05, 0.92, texto_box, transform=ax.transAxes,
            fontsize=9.5, verticalalignment='top',
            bbox=dict(boxstyle='square,pad=0.5', facecolor='white', edgecolor='gainsboro', alpha=0.8))

    ax.set_title(f"Envoltória de resistência - {criterio_escolhido}", fontsize=11, fontweight='bold', pad=12)
    ax.set_xlabel(r"$\sigma_n\text{ (kPa)}$", fontsize=10, labelpad=8)
    ax.set_ylabel(r"$\tau\text{ (kPa)}$", fontsize=10, labelpad=8)

    ax.set_xlim(0, xmax)
    ax.set_ylim(0, ymax)
    ax.set_xticks([0, 100, 200, 300, 400])
    ax.set_yticks([0, 50, 100, 150, 200, 250])

    ax.grid(True, linestyle=':', color='gainsboro', alpha=0.8)

    for spine in ax.spines.values():
        spine.set_color('black')
        spine.set_linewidth(1.0)

    plt.tight_layout()
    if salvar:
        plt.savefig("envoltoria_mohr_coulomb.png", dpi=300, bbox_inches='tight')
    plt.show()

    return c_kpa, phi_graus, r2
