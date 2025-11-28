# -*- coding: utf-8 -*-
"""
Módulo de Serviço de Grafo (Backend)

Centraliza a lógica de criação do grafo de caminhamento
usando NetworkX e Matplotlib.
"""
import networkx as nx
import matplotlib.pyplot as plt
import mplcursors
from tkinter import messagebox

def criar_figura_grafo(caminho_data, nome_pessoa, data_inicio_str, data_fim_str, on_node_click_callback=None):
    """
    Cria e retorna a figura Matplotlib do grafo.
    Retorna (Figure, mplcursors.Cursor, Graph, node_ids_ordenados).
    Uma função opcional `on_node_click_callback` pode ser informada — ela receberá o
    evento `sel` do mplcursors quando um nó for selecionado (o callback pode verificar
    `sel.mouseevent.dblclick` para detectar duplo-clique).
    """
    G = nx.DiGraph()
    pos = {}
    node_labels = {}
    node_colors = []
    node_ids_ordenados = []
    node_anterior = None

    # 1. Construir o grafo
    try:
        for i, (datahora, nome_camera, andar, nrsala, video_path, start_second) in enumerate(caminho_data):
            node_id = f"{i}_{nome_camera}"
            andar_val = andar if andar is not None else 0
            nrsala_val = nrsala if nrsala is not None else -1
            
            pos[node_id] = (i, andar_val) 
            node_labels[node_id] = f"Sala {nrsala_val}\n{nome_camera}\n{datahora.strftime('%d/%m %H:%M:%S')}"
            
            cor = "skyblue"
            if nrsala_val == 0:
                cor = "#90EE90"
            node_colors.append(cor)

            G.add_node(node_id,
                       pessoa=nome_pessoa,
                       camera=nome_camera,
                       andar=andar_val,
                       sala=nrsala_val,
                       horario=datahora.strftime('%Y-%m-%d %H:%M:%S'),
                       video_path=video_path,
                       start_second=start_second)
            
            node_ids_ordenados.append(node_id)
            
            if node_anterior:
                G.add_edge(node_anterior, node_id)
            node_anterior = node_id
    except ValueError:
        messagebox.showerror(
            "Erro de Incompatibilidade de Dados",
            "Não foi possível gerar o grafo.\n\n"
            "Causa provável: A versão da base de dados pode estar dessincronizada com a aplicação, "
            "retornando um número incorreto de colunas para a tela de 'Acompanhar Pessoa'.\n\n"
            "Verifique se todas as colunas, incluindo 'nomearquivovideomarcacao' e 'segundomarcacao', "
            "estão presentes no resultado da consulta."
        )
        return None, None


    # 2. Configurar a Figura Matplotlib
    fig, ax = plt.subplots(figsize=(10, 6))
    plt.subplots_adjust(left=0.1, right=0.95, top=0.9, bottom=0.1)
    
    # 3. Desenhar os componentes
    nodes = nx.draw_networkx_nodes(G, pos, ax=ax, nodelist=node_ids_ordenados,
                                   node_color=node_colors, node_size=3500,
                                   edgecolors="black")

    nx.draw_networkx_edges(G, pos, ax=ax, node_size=3500,
                           arrowstyle='->', arrowsize=20,
                           connectionstyle='arc3,rad=0.1')
    
    nx.draw_networkx_labels(G, pos, labels=node_labels, ax=ax, font_size=8)

    # 4. Configurar Eixos e Título
    ax.set_title(f"Percurso de: {nome_pessoa} ({data_inicio_str} a {data_fim_str})", fontsize=14)
    ax.set_xticks([])
    
    y_andares = sorted(list(set(andar for _, andar in pos.values())))
    if not y_andares:
         y_andares = [0]
         
    ax.set_yticks(y_andares)
    ax.set_yticklabels([f"Andar {andar}" for andar in y_andares], fontsize=10)
    ax.tick_params(axis='y', left=True, right=False)
    ax.spines['left'].set_visible(True)
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['bottom'].set_visible(False)

    # 5. Configurar o Tooltip e o clique
    # O cursor agora responde apenas a cliques, não a hovers.
    cursor = mplcursors.cursor(nodes, hover=False)
    cursor.enabled = True 
    
    # Se o chamador forneceu um callback para clique, conectamos também aqui.
    # Note: o evento 'add' é disparado ao adicionar uma seleção (hover/click).
    # O callback do chamador pode checar sel.mouseevent.dblclick para filtrar.
    if on_node_click_callback is not None:
        @cursor.connect("add")
        def on_add(sel):
            # Preenche o annotation com o texto para que o callback externo possa usá-lo se quiser,
            # mas o principal é chamar o callback.
            node_index = sel.index
            node_id = node_ids_ordenados[node_index]
            metadata = G.nodes[node_id]
            texto_tooltip = (
                f"Pessoa: {metadata['pessoa']}\n"
                f"Câmera: {metadata['camera']}\n"
                f"Horário: {metadata['horario']}"
            )
            sel.annotation.set_text(texto_tooltip)
            
            try:
                # O callback externo é responsável por verificar se foi um duplo-clique
                on_node_click_callback(sel)
            except Exception as e:
                # reporta erro amigável ao usuário sem quebrar a geração do grafo
                messagebox.showerror("Erro do Callback", f"Erro no callback do nó: {e}")
    
    # retorna também o grafo e a ordem dos ids para quem quiser manipular nós externamente
    return fig, cursor, G, node_ids_ordenados