# ♠️ Projeto de Estatística Aplicada: BLACKJACK HIPERGEOMÉTRICO (O Jogo do 21)

Este projeto explora a intersecção entre a teoria de probabilidade e a jogabilidade em tempo real, utilizando o clássico jogo do Blackjack (21) como estudo de caso para a **Distribuição Hipergeométrica**.

---

## 🎯 Requisitos do Projeto & Destaques

| Critério de Avaliação | Ênfase no Projeto | Detalhes Técnicos |
| :--- | :--- | :--- |
| **Criatividade** | ✅ **Alta** | Aplicamos a teoria estatística (Hipergeométrica) a um jogo real, transformando a tela em um laboratório de probabilidade em tempo real. |
| **Jogabilidade** | ✅ **Funcional** | O jogo segue as regras básicas do Blackjack (Hit/Stand), possui controle de pontuação (+10) e lida corretamente com o Ás (1/11) e o Blackjack natural. |
| **Distribuições de Probabilidade** | ✅ **Essência do Projeto** | O gráfico lateral atualiza os parâmetros $N$ e $K_{10}$ a cada carta e exibe a **PMF (Função Massa de Probabilidade)** Hipergeométrica de forma explícita. |
| **Apresentação** | ✅ **Clara e Explícita** | O projeto roda em uma tela dividida, com representações claras para cartas, valores, placar e análise estatística. |

---

## 🧠 Análise Técnica: Por Que a Hipergeométrica?

O Blackjack é um exemplo clássico de **amostragem sem reposição**. Quando uma carta é sacada, ela altera a composição do baralho restante, modificando as probabilidades futuras.

A **Distribuição Hipergeométrica** é o modelo exato para calcular a probabilidade de um número $k$ de sucessos (por exemplo, tirar uma carta de valor 10) em $n$ tentativas, dado um baralho remanescente de tamanho $N$ e $K$ cartas de sucesso.

### Visualização na Tela (`[G] Alternar Gráfico`):

O projeto oferece duas visualizações em tempo real:

#### Modo 1: Risco Imediato (`prob_hit` - Padrão)
Exibe a probabilidade teórica de:
1. Sacar uma carta de valor 10 (Maior fator de risco de estouro).
2. Estourar (Bust) com a próxima jogada.

#### Modo 2: PMF Completa (`pmf_completa`)
Exibe a comparação mais completa dos dados. O histograma mostra:
* **PMF Teórica (Barras Rixas e Curva Vermelha):** O que a matemática **prevê** que acontecerá (a curva ideal).
* **Histograma Empírico (Barras Azuis):** O resultado de **1000 simulações** instantâneas realizadas com os parâmetros atuais do baralho ($N$ e $K_{10}$ atualizados).

Esta comparação visual explícita cumpre o requisito de mostrar o confronto entre a previsão teórica e o resultado empírico em tempo real.

---

## 🛠️ Como Executar o Projeto

**Linguagem:** Python

**Bibliotecas Necessárias:**

```bash
pip install pygame numpy matplotlib scipy
