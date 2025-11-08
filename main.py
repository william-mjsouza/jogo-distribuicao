import pygame
import random
import math
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from scipy.interpolate import make_interp_spline

# === CONFIGURAÇÕES ===
pygame.init()
screen = pygame.display.set_mode((1000, 550))
pygame.display.set_caption("Jogo do 21 com Distribuição Hipergeométrica")
font = pygame.font.SysFont("arial", 24)
clock = pygame.time.Clock()

# === CARTAS E VALORES ===
naipes_map = {'C': '♥', 'O': '♦', 'E': '♠', 'P': '♣'}
naipes = ['C', 'O', 'E', 'P']
valores_cartas = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
valores = {'A': 11, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7,
           '8': 8, '9': 9, '10': 10, 'J': 10, 'Q': 10, 'K': 10}

baralho_completo = [(c, n) for c in valores_cartas for n in naipes]

# === VARIÁVEIS DO JOGO E PONTUAÇÃO ===
baralho = []
mao_jogador = []
mao_computador = []
estado = "INICIO"
grafico_mode = "prob_hit"
score = 0
n_tentativas_grafico = 3 # NOVO: Parâmetro n inicial para o gráfico PMF completa


# === FUNÇÕES DE JOGO ===
def novo_baralho():
    global baralho
    baralho = list(baralho_completo)
    random.shuffle(baralho)


def sacar_carta():
    if not baralho:
        novo_baralho()
    return baralho.pop(0)


def valor_mao(mao):
    val = sum(valores[c[0]] for c in mao)
    num_ases = sum(1 for c in mao if c[0] == 'A')

    while val > 21 and num_ases > 0:
        val -= 10
        num_ases -= 1
    
    if val == 21 and len(mao) == 2:
        return 21.5
    
    return val


def iniciar_jogo():
    global mao_jogador, mao_computador, estado
    novo_baralho()
    mao_jogador = [sacar_carta(), sacar_carta()]
    mao_computador = [sacar_carta(), sacar_carta()]
    
    vj = valor_mao(mao_jogador)
    vc = valor_mao(mao_computador)
    
    if vj == 21.5 or vc == 21.5:
        turno_computador()
        verificar_resultado(blackjack_check=True)
        estado = "FIM"
    else:
        estado = "JOGANDO"


def turno_computador():
    global mao_computador
    while valor_mao(mao_computador) < 17:
        mao_computador.append(sacar_carta())


def verificar_resultado(blackjack_check=False):
    """Verifica o vencedor e atualiza a pontuação (+10 / -10)."""
    global score
    
    vj = valor_mao(mao_jogador) 
    vc = valor_mao(mao_computador)
    
    if vj == 21.5: vj_comp = 21 
    if vc == 21.5: vc_comp = 21 

    # Caso 1: Blackjacks iniciais
    if blackjack_check:
        bj_j = (valor_mao(mao_jogador) == 21.5)
        bj_c = (valor_mao(mao_computador) == 21.5)
        
        if bj_j and not bj_c:
            resultado = "BLACKJACK! JOGADOR VENCEU!"
            score += 10
        elif bj_c and not bj_j:
            resultado = "BLACKJACK DO COMPUTADOR (PERDEU)"
            score -= 10
        elif bj_j and bj_c:
            resultado = "BLACKJACK: EMPATE"
            pass
        else:
             pass 

    # Caso 2: Jogador Estourou
    if valor_mao(mao_jogador) > 21:
        resultado = "JOGADOR ESTOUROU (PERDEU)"
        score -= 10
    
    # Caso 3: Computador Estourou (Vitória)
    elif valor_mao(mao_computador) > 21:
        resultado = "JOGADOR VENCEU! (C: Estourou)"
        score += 10
        
    # Caso 4: Comparação de Pontos
    elif vj > vc:
        resultado = "JOGADOR VENCEU!"
        score += 10
        
    elif vj < vc:
        resultado = "JOGADOR PERDEU"
        score -= 10
        
    # Caso 5: Empate
    else:
        resultado = "EMPATE"
        pass
    
    return resultado

# NOVO: Função para alterar o parâmetro n do gráfico (3 a 10)
def alterar_n_grafico():
    global n_tentativas_grafico
    
    novo_n = n_tentativas_grafico + 1
    
    if novo_n > 10:
        n_tentativas_grafico = 3
    else:
        n_tentativas_grafico = novo_n


# === DISTRIBUIÇÃO HIPERGEOMÉTRICA ===
def prob_hipergeometrica(k, N, K, n):
    if k < 0 or k > n or k > K or n - k > N - K:
        return 0
    try:
        prob = (math.comb(K, k) * math.comb(N - K, n - k)) / math.comb(N, n)
    except ValueError:
        return 0
    return prob


def get_params_hipergeometrica(n_tentativas=1):
    N = len(baralho)
    if N == 0:
        return 52, 16, n_tentativas
    K_total = 16
    cartas_jogadas = mao_jogador + mao_computador
    k_sacados = sum(1 for carta in cartas_jogadas if valores.get(carta[0]) == 10)
    K_10 = K_total - k_sacados
    return N, K_10, n_tentativas


def desenhar_grafico(surface):
    fig, ax = plt.subplots(figsize=(4, 4))
    
    # Usa o parâmetro n global no modo completo
    n_grafico_global = n_tentativas_grafico 
    
    N, K_10, _ = get_params_hipergeometrica()

    if grafico_mode == "pmf_completa":
        # --- CÁLCULO E PLOTAGEM DA PMF COMPLETA ---
        n_tentativas = n_grafico_global # Usa o N variável
        n_simulacoes = 1000 
        
        # Limita k_max para que nunca exceda N restante
        k_max = min(n_tentativas, K_10, N) 
        
        k_valores = np.arange(0, k_max + 1)
        
        pmf_valores = [prob_hipergeometrica(k, N, K_10, n_tentativas) for k in k_valores]

        # 1. Histograma Empírico (Simulação)
        try:
            resultados_empiricos = np.random.hypergeometric(K_10, N - K_10, n_tentativas, size=n_simulacoes)
            
            # Ajusta o bins para que cubra todos os k_valores
            bins_ajustados = np.concatenate([k_valores - 0.5, [k_valores.max() + 0.5]]) if len(k_valores) > 0 else np.array([-0.5, 0.5])

            ax.hist(resultados_empiricos, bins=bins_ajustados, 
                    density=True, rwidth=0.8, color='skyblue', alpha=0.5, 
                    label=f'Empírico ({n_simulacoes} sim.)', zorder=1)
        except ValueError:
             # Este erro pode ocorrer se K_10, N-K_10 ou n_tentativas for inválido
             pass

        # 2. PMF Teórica (Barras e Curva)
        ax.bar(k_valores, pmf_valores, color='purple', alpha=0.55, width=0.4, label='PMF Teórica', zorder=2)

        if len(k_valores) > 1:
            x_smooth = np.linspace(k_valores.min(), k_valores.max(), 300)
            spline = make_interp_spline(k_valores, pmf_valores, k=2)
            y_smooth = spline(x_smooth)
            y_smooth = np.clip(y_smooth, 0, 1)
            ax.plot(x_smooth, y_smooth, color='red', linewidth=2.5, label='Curva Suavizada', zorder=3)
        else:
            # Caso especial para n=1 ou k_max=0
            ax.plot(k_valores, pmf_valores, color='red', marker='o', linestyle='--', linewidth=2, zorder=3)

        # 3. Configurações Finais
        ax.set_xticks(k_valores)
        ax.set_ylim(0, max(max(pmf_valores) * 1.25, 0.2)) 
        ax.set_xlim(-0.5, k_max + 0.5)
        ax.set_xlabel(f"Nº de '10s' em {n_tentativas} cartas (k)")
        ax.set_ylabel("P(X=k) / Freq. Relativa")
        ax.set_title(f"PMF Teórica vs. Empírica (N={N}, K₁₀={K_10}, n={n_tentativas})", fontsize=9)
        ax.legend(fontsize=7, loc='upper right')

        ax.text(0.5, -0.2,
                f"Cartas restantes: N={N} | Cartas '10' restantes: K₁₀={K_10}",
                transform=ax.transAxes,
                ha='center', fontsize=8, color='white',
                bbox=dict(facecolor='black', alpha=0.6, pad=4, edgecolor='none'))

    else:
        # --- CÁLCULO E PLOTAGEM DO PROB_HIT (modo padrão) ---
        p_10 = prob_hipergeometrica(1, N, K_10, 1)
        valor_atual = valor_mao(mao_jogador)
        if valor_atual == 21.5: valor_atual = 21

        max_seguro = 21 - valor_atual

        if valor_atual + 10 > 21:
            titulo = f"PRÓXIMA JOGADA: PERIGO! (N={N})"
            texto_central = f"Se vier um '10' ({p_10*100:.1f}%), você estoura!"
            cor_barra = 'red'
        else:
            titulo = f"PRÓXIMA JOGADA: (N={N}, P(10)={p_10*100:.1f}%)"
            cartas_jogadas = mao_jogador + mao_computador
            K_estouro = 0
            for valor_carta in valores_cartas:
                val = valores[valor_carta]
                if val > max_seguro:
                    total_val = 4
                    sacados_val = sum(1 for carta in cartas_jogadas if carta[0] == valor_carta)
                    K_estouro += (total_val - sacados_val)
            p_estouro = prob_hipergeometrica(1, N, K_estouro, 1)
            texto_central = f"Máx. seguro: {max_seguro}. P(Estourar): {p_estouro * 100:.1f}%"
            cor_barra = 'green'

        ax.bar(['P(10)'], [p_10], color=cor_barra)
        ax.set_ylim(0, 0.5)
        ax.set_ylabel("Probabilidade")
        ax.set_title(titulo, fontsize=9)
        ax.text(0.5, 0.8, texto_central, ha='center', va='center',
                transform=ax.transAxes, fontsize=10)

    # --- Renderiza o gráfico em surface Pygame ---
    canvas = FigureCanvas(fig)
    canvas.draw()
    raw_data = canvas.buffer_rgba()
    size = canvas.get_width_height()
    surf = pygame.image.frombuffer(raw_data, size, "RGBA")
    plt.close(fig)
    return surf


# === LOOP PRINCIPAL ===
novo_baralho()
running = True
resultado = "" # Inicializa a variável resultado

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if estado == "INICIO":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                iniciar_jogo()

        elif estado == "JOGANDO":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_h:
                    mao_jogador.append(sacar_carta())
                    if valor_mao(mao_jogador) > 21 and valor_mao(mao_jogador) != 21.5:
                        resultado = verificar_resultado()
                        # Não chama turno_computador, pois o jogador perdeu automaticamente
                        estado = "FIM"
                elif event.key == pygame.K_s:
                    turno_computador()
                    resultado = verificar_resultado()
                    estado = "FIM"
                elif event.key == pygame.K_g:
                    grafico_mode = 'pmf_completa' if grafico_mode == 'prob_hit' else 'prob_hit'
                elif event.key == pygame.K_n:
                    alterar_n_grafico() # Altera o valor de n

        elif estado == "FIM":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                iniciar_jogo()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_g:
                grafico_mode = 'pmf_completa' if grafico_mode == 'prob_hit' else 'prob_hit'
            elif event.key == pygame.KEYDOWN and event.key == pygame.K_n:
                alterar_n_grafico() # Altera o valor de n


    # === RENDERIZAÇÃO ===
    screen.fill((25, 25, 25))

    if estado in ["JOGANDO", "FIM"]:
        titulo = font.render("Jogo do 21 (Blackjack) - Análise Hipergeométrica", True, (255, 255, 0))
        screen.blit(titulo, (50, 20))

        score_text = font.render(f"PONTUAÇÃO: {score} | N (Gráfico) = {n_tentativas_grafico}", True, (255, 255, 255))
        screen.blit(score_text, (50, 50)) 
        
        # Cartas do jogador
        y = 350
        x = 50
        for carta in mao_jogador:
            simbolo_naipe = naipes_map.get(carta[1], '')
            texto_carta = f"{carta[0]} {simbolo_naipe}"
            pygame.draw.rect(screen, (100, 150, 255), (x, y, 70, 90))
            cor_texto = (255, 0, 0) if carta[1] in ['C', 'O'] else (0, 0, 0)
            text = font.render(texto_carta, True, cor_texto)
            screen.blit(text, (x + 5, y + 30))
            x += 80
            
        vj_display = valor_mao(mao_jogador)
        if vj_display == 21.5:
            vj_display = "BLACKJACK (21)"
        elif vj_display > 21.5:
            vj_display = int(vj_display) 
        else:
            vj_display = int(vj_display)

        texto_jogador = font.render(f"Jogador: {vj_display} pontos", True, (255, 255, 255))
        screen.blit(texto_jogador, (50, 300))

        # Cartas do computador
        y = 100
        x = 50
        for i, carta in enumerate(mao_computador):
            if estado == "JOGANDO" and i == 0:
                texto_carta = "??"
                pygame.draw.rect(screen, (200, 200, 200), (x, y, 70, 90))
                cor_texto = (0, 0, 0)
            else:
                simbolo_naipe = naipes_map.get(carta[1], '')
                texto_carta = f"{carta[0]} {simbolo_naipe}"
                pygame.draw.rect(screen, (255, 100, 100), (x, y, 70, 90))
                cor_texto = (255, 0, 0) if carta[1] in ['C', 'O'] else (0, 0, 0)
            text = font.render(texto_carta, True, cor_texto)
            screen.blit(text, (x + 5, y + 30))
            x += 80

        texto_computador = font.render(f"Computador: {'??' if estado == 'JOGANDO' else valor_mao(mao_computador)} pontos", True, (255, 255, 255))
        screen.blit(texto_computador, (50, 80)) 

        info_baralho = font.render(f"Cartas restantes no Baralho: {len(baralho)}", True, (150, 150, 150))
        screen.blit(info_baralho, (50, 200))

    if estado == "INICIO":
        texto = font.render("Pressione [ESPAÇO] para começar", True, (255, 255, 255))
        screen.blit(texto, (50, 250))

    elif estado == "JOGANDO":
        instrucoes = font.render("[H] Hit | [S] Stand | [G] Alternar Gráfico | [N] Altera n (n={})".format(n_tentativas_grafico), True, (200, 200, 200))
        screen.blit(instrucoes, (50, 480))

    elif estado == "FIM":
        try:
            resultado_final = resultado
        except NameError:
            resultado_final = verificar_resultado()

        resultado_texto = font.render(f"RESULTADO: {resultado_final}", True, (0, 255, 0) if "VENCEU" in resultado_final else (255, 0, 0))
        instrucoes = font.render("[R] Recomeçar | [G] Alternar Gráfico | [N] Altera n (n={})".format(n_tentativas_grafico), True, (200, 200, 200))
        screen.blit(resultado_texto, (50, 450))
        screen.blit(instrucoes, (50, 480))

    # === GRÁFICO HIPERGEOMÉTRICO ===
    grafico_surface = desenhar_grafico(screen)
    screen.blit(grafico_surface, (550, 100))

    pygame.display.flip()
    clock.tick(30)

pygame.quit()