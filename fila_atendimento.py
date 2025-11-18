#!/usr/bin/env python3
"""
Fila de Atendimento - Simulação
Formato CSV de input (sem cabeçalho, ou com cabeçalho):
id,name,type,service_time_minutes,arrival_time_minutes

Exemplo de linha:
1,Jose Silva,comum,8,5

Tipos aceitos: comum, preferencial, corporativo
Estruturas disponíveis: lista (deque), prioridade (heap)
Algoritmos de ordenação: merge, quick
Saída: arquivo stats_<timestamp>.txt
"""

import csv
import heapq
import math
import time
from collections import deque, namedtuple
from datetime import datetime

# -----------------------------
# Estrutura Cliente
# -----------------------------
class Cliente:
    def __init__(self, cid, nome, tipo, tempo_servico, chegada):
        self.id = cid
        self.nome = nome
        self.tipo = tipo.lower()
        self.tempo_servico = float(tempo_servico)  # em minutos
        self.chegada = float(chegada)  # minuto do dia (simulado)
        # campos calculados
        self.inicio_atendimento = None
        self.termino_atendimento = None

    def espera(self):
        if self.inicio_atendimento is None:
            return None
        return self.inicio_atendimento - self.chegada

    def atendimento_total(self):
        if self.termino_atendimento is None:
            return None
        return self.termino_atendimento - self.chegada

    def __repr__(self):
        return f"Cliente({self.id},{self.nome},{self.tipo},srv={self.tempo_servico},cheg={self.chegada})"

# -----------------------------
# Prioridade por tipo
# menor valor = maior prioridade no heap
# Define prioridade: corporativo (1) > preferencial (2) > comum (3)
# Dentro da mesma prioridade, FIFO por chegada
# -----------------------------
PRIORIDADE_TIPO = {
    'corporativo': 1,
    'preferencial': 2,
    'comum': 3
}

def tipo_prioridade(tipo):
    return PRIORIDADE_TIPO.get(tipo.lower(), 99)

# -----------------------------
# Algoritmos de ordenação (implementados manualmente)
# - merge_sort
# - quick_sort
# Ordenam lista de objetos Cliente com key functor
# -----------------------------
def merge_sort(arr, key=lambda x: x):
    if len(arr) <= 1:
        return arr[:]
    mid = len(arr) // 2
    left = merge_sort(arr[:mid], key)
    right = merge_sort(arr[mid:], key)
    merged = []
    i = j = 0
    while i < len(left) and j < len(right):
        if key(left[i]) <= key(right[j]):
            merged.append(left[i]); i += 1
        else:
            merged.append(right[j]); j += 1
    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged

def quick_sort(arr, key=lambda x: x):
    if len(arr) <= 1:
        return arr[:]
    pivot = key(arr[len(arr)//2])
    left = [x for x in arr if key(x) < pivot]
    middle = [x for x in arr if key(x) == pivot]
    right = [x for x in arr if key(x) > pivot]
    return quick_sort(left, key) + middle + quick_sort(right, key)

# -----------------------------
# Carregar dados CSV
# -----------------------------
def carregar_csv(caminho):
    clientes = []
    with open(caminho, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        # aceitar cabeçalho tentando detectar se primeira linha tem non-numeric arrival
        first = next(reader)
        try:
            # tentar converter arrival como float para checar se é dados
            float(first[4])
            # é dado, processa a primeira linha
            row0 = first
            clientes.append(Cliente(row0[0], row0[1], row0[2], row0[3], row0[4]))
        except Exception:
            # primeiro era cabeçalho -> ignorar
            pass
        for row in reader:
            if not row or len(row) < 5:
                continue
            clientes.append(Cliente(row[0], row[1], row[2], row[3], row[4]))
    return clientes

# -----------------------------
# Simulação (evento-simulado)
# parâmetros:
# - clientes: lista de Cliente
# - estrutura: 'lista' ou 'prioridade'
# - algoritmo_ord: 'merge' ou 'quick' (usado para ordenar chegadas)
# - reorder_rule: 'por_chegada' ou 'por_prioridade' -> como reordenar a fila quando houver mudanças
# - registrar_undo: se True, usamos pilha para registrar atendimentos (simulação de undo)
# -----------------------------
def simular(clientes, estrutura='lista', algoritmo_ord='merge', reorder_rule='por_prioridade', registrar_undo=False):
    # mapa por id
    mapa = {c.id: c for c in clientes}

    # ordena lista de chegadas pelo algoritmo escolhido (por chegada crescente)
    key_chegada = lambda x: x.chegada
    if algoritmo_ord == 'merge':
        chegadas = merge_sort(clientes, key=key_chegada)
    else:
        chegadas = quick_sort(clientes, key=key_chegada)

    # fila principal
    if estrutura == 'lista':
        # usaremos três filas por tipo (mantém classificação e facilita reordenação)
        filas = {
            'corporativo': deque(),
            'preferencial': deque(),
            'comum': deque()
        }
        push = lambda cliente: filas[cliente.tipo].append(cliente)
        pop_next = lambda : pop_from_filas_deque(filas)
    else:
        # prioridade heap: (priority, arrival_time, counter, cliente)
        heap = []
        counter = 0
        def push(cliente):
            nonlocal counter
            heapq.heappush(heap, (tipo_prioridade(cliente.tipo), cliente.chegada, counter, cliente))
            counter += 1
        def pop_next():
            if not heap:
                return None
            return heapq.heappop(heap)[3]

    # estatísticas
    atendidos = []
    undo_stack = []  # para desfazer
    current_time = 0.0
    idx_chegada = 0
    n = len(chegadas)

    # Avançamos no tempo: se não há clientes na fila, pular para próxima chegada
    while idx_chegada < n or ( (estrutura == 'lista' and any(len(q)>0 for q in filas.values())) or (estrutura!='lista' and heap) ):
        # inserir todos que chegaram até current_time
        if idx_chegada < n and ( (estrutura=='lista' and not any(len(q)>0 for q in filas.values())) or (estrutura!='lista' and not heap) ):
            # se fila vazia, saltar tempo para próxima chegada
            current_time = max(current_time, chegadas[idx_chegada].chegada)

        while idx_chegada < n and chegadas[idx_chegada].chegada <= current_time:
            push(chegadas[idx_chegada])
            idx_chegada += 1

        # escolher próximo cliente
        prox = pop_next()
        if prox is None:
            # não há cliente disponível no momento -> pular para próxima chegada
            if idx_chegada < n:
                current_time = max(current_time, chegadas[idx_chegada].chegada)
                continue
            else:
                break

        # aplicar regra de reordenação se estrutura for lista e rule for prioridade:
        # já usamos filas por tipo, então pop_from_filas_deque já respeita prioridade FIFO por tipo.
        # registrar início e fim
        prox.inicio_atendimento = max(current_time, prox.chegada)
        prox.termino_atendimento = prox.inicio_atendimento + prox.tempo_servico

        # avançar tempo
        current_time = prox.termino_atendimento

        atendidos.append(prox)
        if registrar_undo:
            undo_stack.append(prox)

        # também inserir chegadas que ocorreram durante o atendimento
        while idx_chegada < n and chegadas[idx_chegada].chegada <= current_time:
            # se usar estrutura lista, push por tipo; se heap, push normal
            push(chegadas[idx_chegada])
            idx_chegada += 1

        # opcional: reordenar filas internas se reorder_rule pede (aqui só tem efeito numa implementação que mantivesse tudo numa lista única)
        if reorder_rule == 'por_chegada' and estrutura=='lista':
            # sem efeito porque usamos filas por tipo; left as note
            pass

    # calcular estatísticas
    total_espera = sum([c.espera() for c in atendidos if c.espera() is not None])
    total_atendimento = sum([c.tempo_servico for c in atendidos])
    n_atendidos = len(atendidos)
    media_espera = total_espera / n_atendidos if n_atendidos>0 else 0

    stats = {
        'n_atendidos': n_atendidos,
        'tempo_total_espera': total_espera,
        'tempo_medio_espera': media_espera,
        'tempo_total_atendimento': total_atendimento,
        'estrutura': estrutura,
        'algoritmo_ordenacao': algoritmo_ord,
        'reorder_rule': reorder_rule,
        'complexidade_media_ord': complexity_hint(algoritmo_ord),
    }

    return stats, atendidos, mapa, undo_stack

def pop_from_filas_deque(filas):
    # regra de prioridade: corporativo > preferencial > comum
    for t in ['corporativo','preferencial','comum']:
        if filas[t]:
            return filas[t].popleft()
    return None

def complexity_hint(alg):
    if alg == 'merge':
        return 'O(n log n)'
    if alg == 'quick':
        return 'O(n log n) (pior caso O(n^2) se pivô ruim)'
    return 'Desconhecida'

# -----------------------------
# Utilitários: gerar arquivo de saída com estatísticas
# -----------------------------
def salvar_estatisticas(stats, atendidos, arquivo_saida=None):
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    if arquivo_saida is None:
        arquivo_saida = f"stats_{ts}.txt"
    with open(arquivo_saida, 'w', encoding='utf-8') as f:
        f.write("Relatório de Simulação - Fila de Atendimento\n")
        f.write(f"Gerado em: {datetime.now().isoformat()}\n\n")
        f.write(f"Estrutura utilizada: {stats['estrutura']}\n")
        f.write(f"Algoritmo de ordenação: {stats['algoritmo_ordenacao']}\n")
        f.write(f"Regra de reordenação: {stats['reorder_rule']}\n")
        f.write(f"Complexidade média (ordenacao): {stats['complexidade_media_ord']}\n\n")

        f.write(f"Clientes atendidos: {stats['n_atendidos']}\n")
        f.write(f"Tempo total de espera (min): {stats['tempo_total_espera']:.2f}\n")
        f.write(f"Tempo médio de espera (min): {stats['tempo_medio_espera']:.2f}\n")
        f.write(f"Tempo total de atendimento (min): {stats['tempo_total_atendimento']:.2f}\n\n")

        f.write("Detalhes por cliente (id, nome, tipo, chegada, inicio, termino, espera):\n")
        for c in atendidos:
            f.write(f"{c.id},{c.nome},{c.tipo},{c.chegada:.2f},{c.inicio_atendimento:.2f},{c.termino_atendimento:.2f},{c.espera():.2f}\n")
    return arquivo_saida

# -----------------------------
# Menu CLI simples
# -----------------------------
def menu():
    print("=== Sistema de Fila de Atendimento (simulação) ===\n")
    caminho = input("Caminho do arquivo CSV de entrada (100/1000/5000 registros): ").strip()
    try:
        clientes = carregar_csv(caminho)
    except Exception as e:
        print("Erro ao carregar CSV:", e)
        return

    print(f"Lidos {len(clientes)} registros.")
    print("Escolha estrutura de fila:")
    print("1) lista encadeada (deque por tipo)")
    print("2) fila de prioridade (heap)")
    tipo_estr = input("Opção (1/2) [1]: ").strip() or "1"
    estrutura = 'lista' if tipo_estr=='1' else 'prioridade'

    print("Escolha algoritmo de ordenacao para ordenar chegadas:")
    print("1) merge sort")
    print("2) quick sort")
    alg_opt = input("Opção (1/2) [1]: ").strip() or "1"
    algoritmo = 'merge' if alg_opt=='1' else 'quick'

    print("Regra de reordenação (quando aplicável):")
    print("1) por_prioridade (tipo)")
    print("2) por_chegada")
    r_opt = input("Opção (1/2) [1]: ").strip() or "1"
    reorder_rule = 'por_prioridade' if r_opt=='1' else 'por_chegada'

    undo_opt = input("Registrar pilha de undo (simular desfazer atendimentos)? (s/n) [n]: ").strip().lower() or 'n'
    registrar_undo = (undo_opt == 's')

    print("\nExecutando simulação...")
    stats, atendidos, mapa, undo_stack = simular(clientes, estrutura=estrutura, algoritmo_ord=algoritmo, reorder_rule=reorder_rule, registrar_undo=registrar_undo)
    print("Simulação concluída.")
    print(f"Clientes atendidos: {stats['n_atendidos']}")
    print(f"Tempo médio de espera: {stats['tempo_medio_espera']:.2f} min")
    print(f"Tempo total de atendimento: {stats['tempo_total_atendimento']:.2f} min")

    arq = salvar_estatisticas(stats, atendidos)
    print(f"Arquivo de estatísticas gerado: {arq}")

    # mostrar top 5 mais esperaram
    top_espera = sorted(atendidos, key=lambda c: c.espera() or 0, reverse=True)[:5]
    print("\nTop 5 clientes que mais esperaram (id, nome, espera_min):")
    for c in top_espera:
        print(f"{c.id}, {c.nome}, {c.espera():.2f}")

    # opção para desfazer último atendimento (se registrar_undo)
    if registrar_undo and undo_stack:
        resp = input("\nDeseja desfazer o último atendimento registrado? (s/n) [n]: ").strip().lower() or 'n'
        if resp == 's':
            last = undo_stack.pop()
            print(f"Desfeito atendimento de: {last.id} - {last.nome}. (isso é apenas simulação)")

# -----------------------------
# Entrada direta (facilidade para testes)
# -----------------------------
if __name__ == '__main__':
    menu()
