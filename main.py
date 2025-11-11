import pygame
import random
import math
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from scipy.interpolate import make_interp_spline
import json
import os # Para verificar a existência do arquivo de score

# === CONFIGURAÇÕES ===
pygame.init()
screen = pygame.display.set_mode((1000, 550))
pygame.display.set_caption("Jogo do 21 com Distribuição Hipergeométrica")
font = pygame.font.SysFont("arial", 24)
font_small = pygame.font.SysFont("arial", 18)
clock = pygame.time.Clock()

# === ARQUIVO DE SCORE ===
SCORE_FILE = "blackjack_scores.json"
MAX_HIGHSCORES = 5

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
estado = "NOME_JOGADOR" # Estado inicial agora é para input de nome
grafico_mode = "prob_hit"
score = 0
n_tentativas_grafico = 3 
player_name = ""
games_played = 0
MAX_GAMES = 10
high_scores = []
resultado = ""


# === FUNÇÕES DE SCOREBOARD ===

def load_scores():
    global high_scores
    if os.path.exists(SCORE_FILE):
        with open(SCORE_FILE, 'r') as f:
            try:
                high_scores = json.load(f)
            except json.JSONDecodeError:
                high_scores = []
    else:
        high_scores = []

def save_scores():
    with open(SCORE_FILE, 'w') as f:
        json.dump(high_scores, f)

def update_score_history(name, final_score):
    global high_scores
    load_scores()
    
    # Adiciona o novo score e ordena
    high_scores.append({'name': name, 'score': final_score})
    high_scores.sort(key=lambda x: x['score'], reverse=True)
    
    # Mantém apenas o top 5
    high_scores = high_scores[:MAX_HIGHSCORES]
    save_scores()


# === FUNÇÕES DE JOGO (Lógica de 21 mantida) ===
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
    global score, games_played # Resetamos score APENAS na primeira rodada da sessão.
    
    if games_played == 0:
        score = 0
        
    novo_baralho()
    mao_jogador = [sacar_carta(), sacar_carta()]
    mao_computador = [sacar_carta(), sacar_carta()]
    
    vj = valor_mao(mao_jogador)
    vc = valor_mao(mao_computador)
    
    if vj == 21.5 or vc == 21.5:
        turno_computador()
        global resultado
        resultado = verificar_resultado(blackjack_check=True)
        check_session_end()
    else:
        estado = "JOGANDO"

def check_session_end():
    global games_played, estado
    games_played += 1
    if games_played >= MAX_GAMES:
        update_score_history(player_name, score)
        estado = "SCOREBOARD"
    else:
        estado = "FIM" # Volta para o estado FIM para recomeçar a próxima de 10

def turno_computador():
    global mao_computador
    while valor_mao(mao_computador) < 17:
        mao_computador.append(sacar_carta())


def verificar_resultado(blackjack_check=False):
    global score
    
    vj = valor_mao(mao_jogador) 
    vc = valor_mao(mao_computador)
    
    # Normaliza 21.5 para 21
    if vj == 21.5: vj_comp = 21 
    if vc == 21.5: vc_comp = 21 

    if blackjack_check:
        bj_j = (valor_mao(mao_jogador) == 21.5)
        bj_c = (valor_mao(mao_computador) == 21.5)
        
        if bj_j and not bj_c:
            resultado = "BLACKJACK! JOGADOR VENCEU!"
            score += 10
        elif bj_c and not bj_j:
            resultado = "BLACKJACK DO COMPUTADOR (PERDEU)"
            score -= 0
        elif bj_j and bj_c:
            resultado = "BLACKJACK: EMPATE"
            pass
        else:
             pass 

    elif valor_mao(mao_jogador) > 21:
        resultado = "JOGADOR ESTOUROU (PERDEU)"
        score -= 0
    
    elif valor_mao(mao_computador) > 21:
        resultado = "JOGADOR VENCEU! (C: Estourou)"
        score += 10
        
    elif vj > vc:
        resultado = "JOGADOR VENCEU!"
        score += 10
        
    elif vj < vc:
        resultado = "JOGADOR PERDEU"
        score -= 0
        
    else:
        resultado = "EMPATE"
        pass
    
    return resultado

def alterar_n_grafico():
    global n_tentativas_grafico
    
    novo_n = n_tentativas_grafico + 1
    
    if novo_n > 10:
        n_tentativas_grafico = 3
    else:
        n_tentativas_grafico = novo_n


# === FUNÇÕES DE GRÁFICO (Mantidas) ===
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
    
    n_grafico_global = n_tentativas_grafico 
    
    N, K_10, _ = get_params_hipergeometrica()

    if grafico_mode == "pmf_completa":
        n_tentativas = n_grafico_global
        n_simulacoes = 1000 
        k_max = min(n_tentativas, K_10, N) 
        k_valores = np.arange(0, k_max + 1)
        pmf_valores = [prob_hipergeometrica(k, N, K_10, n_tentativas) for k in k_valores]

        try:
            resultados_empiricos = np.random.hypergeometric(K_10, N - K_10, n_tentativas, size=n_simulacoes)
            bins_ajustados = np.concatenate([k_valores - 0.5, [k_valores.max() + 0.5]]) if len(k_valores) > 0 else np.array([-0.5, 0.5])
            ax.hist(resultados_empiricos, bins=bins_ajustados, density=True, rwidth=0.8, color='skyblue', alpha=0.5, label=f'Empírico ({n_simulacoes} sim.)', zorder=1)
        except ValueError:
             pass

        ax.bar(k_valores, pmf_valores, color='purple', alpha=0.55, width=0.4, label='PMF Teórica', zorder=2)

        if len(k_valores) > 1:
            x_smooth = np.linspace(k_valores.min(), k_valores.max(), 300)
            spline = make_interp_spline(k_valores, pmf_valores, k=2)
            y_smooth = spline(x_smooth)
            y_smooth = np.clip(y_smooth, 0, 1)
            ax.plot(x_smooth, y_smooth, color='red', linewidth=2.5, label='Curva Suavizada', zorder=3)
        else:
            ax.plot(k_valores, pmf_valores, color='red', marker='o', linestyle='--', linewidth=2, zorder=3)

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

    canvas = FigureCanvas(fig)
    canvas.draw()
    raw_data = canvas.buffer_rgba()
    size = canvas.get_width_height()
    surf = pygame.image.frombuffer(raw_data, size, "RGBA")
    plt.close(fig)
    return surf


# === FUNÇÕES DE RENDERIZAÇÃO DE ESTADOS ===

def render_nome_jogador():
    global player_name
    screen.fill((25, 25, 25))
    
    titulo = font.render("Jogo do 21: Análise Estatística", True, (255, 255, 0))
    screen.blit(titulo, (50, 50))
    
    instrucao = font.render("Digite seu nome e pressione [ENTER]:", True, (255, 255, 255))
    screen.blit(instrucao, (50, 150))
    
    # Desenha a caixa de texto
    box_rect = pygame.Rect(50, 200, 300, 40)
    pygame.draw.rect(screen, (255, 255, 255), box_rect, 2)
    
    # Renderiza o nome
    text_surface = font.render(player_name + ("|" if clock.get_fps() % 2 else ""), True, (255, 255, 255))
    screen.blit(text_surface, (60, 210))

    # Descrição do Jogo
    regras_titulo = font.render("REGRAS E CONTROLES", True, (0, 255, 255))
    screen.blit(regras_titulo, (50, 300))

    regras = [
        "Objetivo: Vencer o computador sem exceder 21.",
        "[H]: HIT (Pedir mais uma carta)",
        "[S]: STAND (Manter a pontuação)",
        "[G]: Alternar Gráfico (Risco vs. PMF Completa)",
        "[N]: Alterar 'n' do gráfico (3 a 10) - Permite explorar a Variância da PMF.",
        "Sessão: 10 jogos por jogador. (+10 por vitória, -10 por derrota).",
        "[R]: Recomeçar a próxima rodada."
    ]
    
    y_pos = 340
    for regra in regras:
        screen.blit(font_small.render(regra, True, (200, 200, 200)), (50, y_pos))
        y_pos += 25

def render_scoreboard():
    screen.fill((25, 25, 25))
    
    titulo = font.render(f"FIM DA SESSÃO - Placar de {player_name}", True, (255, 255, 0))
    screen.blit(titulo, (50, 50))
    
    final_score_text = font.render(f"Sua Pontuação Final: {score}", True, (0, 255, 0) if score >= 0 else (255, 0, 0))
    screen.blit(final_score_text, (50, 100))

    # Ranking
    ranking_titulo = font.render("TOP 5 PONTUAÇÕES GERAIS", True, (0, 255, 255))
    screen.blit(ranking_titulo, (50, 200))
    
    y_pos = 240
    for i, entry in enumerate(high_scores):
        text = f"{i+1}. {entry['name']} - {entry['score']} pontos"
        color = (255, 255, 255)
        if entry['name'] == player_name and entry['score'] == score:
            color = (255, 220, 0) # Cor de destaque para o jogador atual
        
        screen.blit(font.render(text, True, color), (50, y_pos))
        y_pos += 30

    instrucao = font.render("Pressione [ESPAÇO] para um novo jogador.", True, (200, 200, 200))
    screen.blit(instrucao, (50, 480))


# === LOOP PRINCIPAL ===
load_scores() # Carrega os scores ao iniciar
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if estado == "NOME_JOGADOR":
                if event.key == pygame.K_RETURN:
                    if player_name.strip():
                        # Inicia a primeira rodada do novo jogador
                        games_played = 0
                        iniciar_jogo()
                    else:
                        player_name = "Anônimo" # Fallback se ENTER for pressionado sem nome
                elif event.key == pygame.K_BACKSPACE:
                    player_name = player_name[:-1]
                else:
                    # Limita a 15 caracteres e aceita apenas caracteres visíveis
                    if len(player_name) < 15 and event.unicode.isprintable():
                        player_name += event.unicode.upper()

            elif estado == "SCOREBOARD":
                if event.key == pygame.K_SPACE:
                    # Reseta para um novo jogador
                    player_name = ""
                    games_played = 0
                    score = 0
                    estado = "NOME_JOGADOR"
                    
            elif estado == "JOGANDO":
                if event.key == pygame.K_h:
                    mao_jogador.append(sacar_carta())
                    if valor_mao(mao_jogador) > 21 and valor_mao(mao_jogador) != 21.5:
                        resultado = verificar_resultado() 
                        check_session_end()
                elif event.key == pygame.K_s:
                    turno_computador()
                    resultado = verificar_resultado()
                    check_session_end()
                elif event.key == pygame.K_g:
                    grafico_mode = 'pmf_completa' if grafico_mode == 'prob_hit' else 'prob_hit'
                elif event.key == pygame.K_n:
                    alterar_n_grafico()

            elif estado == "FIM":
                if event.key == pygame.K_r:
                    iniciar_jogo()
                elif event.key == pygame.K_g:
                    grafico_mode = 'pmf_completa' if grafico_mode == 'prob_hit' else 'prob_hit'
                elif event.key == pygame.K_n:
                    alterar_n_grafico()


    # === RENDERIZAÇÃO PRINCIPAL ===
    if estado == "NOME_JOGADOR":
        render_nome_jogador()
        
    elif estado == "SCOREBOARD":
        render_scoreboard()

    elif estado in ["JOGANDO", "FIM"]:
        screen.fill((25, 25, 25))
        titulo = font.render(f"Sessão: {player_name} | Jogo {games_played + (1 if estado != 'FIM' else 0)}/{MAX_GAMES}", True, (255, 255, 0))
        screen.blit(titulo, (50, 20))

        score_text = font.render(f"PONTUAÇÃO: {score} | N (Gráfico) = {n_tentativas_grafico}", True, (255, 255, 255))
        screen.blit(score_text, (50, 50)) 
        
        # --- Desenha Cartas e Pontos (Lógica Mantida) ---
        
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

        if estado == "JOGANDO":
            instrucoes = font.render("[H] Hit | [S] Stand | [G] Alternar Gráfico | [N] Altera n (n={})".format(n_tentativas_grafico), True, (200, 200, 200))
            screen.blit(instrucoes, (50, 480))

        elif estado == "FIM":
            resultado_final = resultado
            resultado_texto = font.render(f"RESULTADO: {resultado_final}", True, (0, 255, 0) if "VENCEU" in resultado_final else (255, 0, 0))
            instrucoes = font.render(f"[R] Recomeçar Jogo {games_played + 1}/{MAX_GAMES} | [G] Alternar Gráfico | [N] Altera n (n={n_tentativas_grafico})", True, (200, 200, 200))
            screen.blit(resultado_texto, (50, 450))
            screen.blit(instrucoes, (50, 480))

        # === GRÁFICO HIPERGEOMÉTRICO ===
        grafico_surface = desenhar_grafico(screen)
        screen.blit(grafico_surface, (550, 100))

    pygame.display.flip()
    clock.tick(30)

pygame.quit()