# -*- coding: utf-8 -*-
"""
Script AUTOMATIZADO com GUI para reconhecimento facial em vídeos (V3.1)

(FIX V3.1) - Corrige o salvamento de dados, incluindo o 'nomeCamera' 
             na tabela 'tb_videos_processados' para permitir a
             junção com a tela de Acompanhamento.

Requisitos:
pip install opencv-python face_recognition pandas psycopg2-binary
"""
import tkinter as tk
from tkinter import ttk, scrolledtext
import face_recognition
import cv2
import os
import pandas as pd
import sys
import psycopg2
import shutil
import time
from datetime import datetime
import threading  
import queue      

# ==========================================================
# ⚙️ CONFIGURAÇÃO DO BANCO DE DADOS
# ==========================================================
DB_NAME = "postgres"
DB_USER = "supervisorio"
DB_PASS = "supervisorio101"
DB_HOST = "localhost"
DB_PORT = 5432
# ==========================================================
INTERVALO_MONITORAMENTO = 60 
# ==========================================================


def get_db_connection():
    """Tenta estabelecer uma conexão com o banco de dados."""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT
        )
        return conn
    except Exception as e:
        print(f"❌ Erro de Banco de Dados: Não foi possível conectar ao PostgreSQL:\n{e}")
        return None

# (NOVO) Classe principal da Aplicação com GUI
class ProcessadorApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Processador de Mídia - Supervisório (V3.1)")
        self.root.geometry("800x600")

        # --- Variáveis de Estado e Estatísticas ---
        self.parametros = None
        self.encodings_conhecidos = []
        self.nomes_conhecidos = []
        self.fotos_conhecidas = []
        
        self.pastas_fotos_processadas = set() 
        
        self.var_fotos_carregadas = tk.IntVar(value=0)
        self.var_videos_processados = tk.IntVar(value=0)
        self.var_rostos_encontrados = tk.IntVar(value=0)
        self.var_rostos_desconhecidos = tk.IntVar(value=0)
        self.var_status_thread = tk.StringVar(value="Iniciando...")

        # --- Controle da Thread ---
        self.running = True
        self.log_queue = queue.Queue()
        self.setup_ui()
        
        self.root.after(100, self.verificar_fila_logs)
        self.iniciar_thread_processamento()
        self.root.protocol("WM_DELETE_WINDOW", self.ao_fechar)

    def setup_ui(self):
        """Constrói a interface gráfica do monitor."""
        
        stats_frame = ttk.LabelFrame(self.root, text="Estatísticas de Execução", padding=10)
        stats_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(stats_frame, text="Fotos de Referência Carregadas:", font=("Arial", 10)).grid(row=0, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(stats_frame, textvariable=self.var_fotos_carregadas, font=("Arial", 10, "bold")).grid(row=0, column=1, sticky="w")
        
        ttk.Label(stats_frame, text="Vídeos Processados (nesta sessão):", font=("Arial", 10)).grid(row=1, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(stats_frame, textvariable=self.var_videos_processados, font=("Arial", 10, "bold")).grid(row=1, column=1, sticky="w")
        
        ttk.Label(stats_frame, text="Rostos Encontrados:", font=("Arial", 10)).grid(row=2, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(stats_frame, textvariable=self.var_rostos_encontrados, font=("Arial", 10, "bold"), foreground="green").grid(row=2, column=1, sticky="w")
        
        ttk.Label(stats_frame, text="Rostos Desconhecidos:", font=("Arial", 10)).grid(row=3, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(stats_frame, textvariable=self.var_rostos_desconhecidos, font=("Arial", 10, "bold"), foreground="red").grid(row=3, column=1, sticky="w")

        log_frame = ttk.LabelFrame(self.root, text="Log de Processamento", padding=10)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, state='disabled', height=10, font=("Courier New", 9))
        self.log_text.pack(fill="both", expand=True)

        status_bar = ttk.Frame(self.root, relief="sunken", padding=(5, 2))
        status_bar.pack(fill="x", side="bottom")
        ttk.Label(status_bar, textvariable=self.var_status_thread).pack(side="left")

    def adicionar_log(self, mensagem):
        """(Seguro para Threads) Envia uma mensagem de log para a fila da GUI."""
        self.log_queue.put(('log', f"[{datetime.now().strftime('%H:%M:%S')}] {mensagem}\n"))

    def atualizar_stat(self, stat_nome, valor):
        """(Seguro para Threads) Envia uma atualização de estatística para a fila da GUI."""
        self.log_queue.put(('stat', (stat_nome, valor)))

    def verificar_fila_logs(self):
        """(GUI Thread) Verifica a fila de mensagens e atualiza a interface."""
        while not self.log_queue.empty():
            try:
                tipo, dados = self.log_queue.get_nowait()
                
                if tipo == 'log':
                    self.log_text.config(state='normal')
                    self.log_text.insert(tk.END, dados)
                    self.log_text.see(tk.END) # Auto-scroll
                    self.log_text.config(state='disabled')
                
                elif tipo == 'stat':
                    nome_stat, valor = dados
                    if nome_stat == 'fotos':
                        self.var_fotos_carregadas.set(self.var_fotos_carregadas.get() + valor)
                    elif nome_stat == 'videos':
                        self.var_videos_processados.set(self.var_videos_processados.get() + valor)
                    elif nome_stat == 'encontrados':
                        self.var_rostos_encontrados.set(self.var_rostos_encontrados.get() + valor)
                    elif nome_stat == 'desconhecidos':
                        self.var_rostos_desconhecidos.set(self.var_rostos_desconhecidos.get() + valor)
                
                elif tipo == 'status_thread':
                    self.var_status_thread.set(dados)
                    
            except queue.Empty:
                pass
        
        self.root.after(100, self.verificar_fila_logs)

    def iniciar_thread_processamento(self):
        """Inicia a thread de trabalho em segundo plano."""
        self.running = True
        self.thread = threading.Thread(target=self.loop_de_processamento, daemon=True)
        self.thread.start()

    def ao_fechar(self):
        """Chamado quando a janela da GUI é fechada."""
        print("Parando o monitoramento...")
        self.adicionar_log("Parando o monitoramento... Aguarde o lote atual.")
        self.running = False 
        self.root.destroy()  

    # ==========================================================
    # MÉTODOS DE PROCESSAMENTO (Executados na Thread de Trabalho)
    # ==========================================================

    def loop_de_processamento(self):
        """(Thread de Trabalho) O loop principal de monitoramento."""
        
        self.log_queue.put(('status_thread', "Carregando parâmetros..."))
        self.parametros = self.carregar_parametros_db()
        if self.parametros is None:
            self.adicionar_log("❌ ERRO FATAL: Não foi possível carregar os parâmetros. A thread será encerrada.")
            self.log_queue.put(('status_thread', "Erro! Verifique o console."))
            return

        self.log_queue.put(('status_thread', "Carregando fotos de referência..."))
        self.atualizar_rostos_conhecidos()

        self.adicionar_log("🚀 MONITORAMENTO INICIADO")
        
        try:
            while self.running:
                self.log_queue.put(('status_thread', f"Verificando mídias... (Próxima verificação em {INTERVALO_MONITORAMENTO}s)"))
                
                # 1. Verifica se há NOVAS fotos
                self.atualizar_rostos_conhecidos()
                
                # 2. Processa os vídeos encontrados
                self.processar_lote_videos()
                
                self.log_queue.put(('status_thread', f"Aguardando {INTERVALO_MONITORAMENTO} segundos..."))
                
                for _ in range(INTERVALO_MONITORAMENTO):
                    if not self.running:
                        break
                    time.sleep(1)
                    
        except Exception as e:
            self.adicionar_log(f"❌ ERRO CRÍTICO NA THREAD: {e}")
            self.log_queue.put(('status_thread', "Erro crítico na thread! Verifique o log."))
        
        self.adicionar_log("Monitoramento encerrado.")
        self.log_queue.put(('status_thread', "Parado."))


    def carregar_parametros_db(self):
        """(Thread de Trabalho) Carrega parâmetros do DB."""
        self.adicionar_log("Conectando ao banco de dados para carregar parâmetros...")
        sql = """
            SELECT "idParametro", "caminhoFotosClientes", "caminhoMapas",
                   "caminhoVideoAProcessar", "caminhoVideoProcessados",
                   "caminhoVideoMarcoes", "intevalorFrames", "escalaImagem",
                   "modeloDeteccao", "toleranciaReconhecimento", "gerarvideomarcacoes"
            FROM sch_supervisorio.tb_parametro LIMIT 1
        """
        conn = get_db_connection()
        if conn is None: 
            return None
        
        parametros = None
        try:
            with conn.cursor() as cur:
                cur.execute(sql)
                result = cur.fetchone()
                if result:
                    parametros = {
                        "id": result[0], "fotos": result[1], "mapas": result[2],
                        "videos_a_processar": result[3], "videos_processados": result[4],
                        "video_marcoes": result[5], "intervalo_frames": result[6],
                        "escala_imagem": float(result[7]) if result[7] is not None else 1.0,
                        "modelo_deteccao": result[8],
                        "tolerancia": result[9], "gerar_marcoes": result[10]
                    }
                    self.adicionar_log("✅ Parâmetros carregados com sucesso.")
        except Exception as e:
            self.adicionar_log(f"❌ Erro de Consulta: Erro ao carregar parâmetros:\n{e}")
        finally:
            conn.close()
        
        return parametros

    def atualizar_rostos_conhecidos(self):
        """
        (Thread de Trabalho) Carrega APENAS NOVAS pastas de fotos.
        """
        pasta_fotos = self.parametros['fotos']
        if not os.path.isdir(pasta_fotos):
            self.adicionar_log(f"❌ Erro: A pasta de fotos '{pasta_fotos}' não foi encontrada.")
            return

        novas_fotos_encontradas = 0
        
        for nome_pasta_pessoa in os.listdir(pasta_fotos):
            if nome_pasta_pessoa in self.pastas_fotos_processadas:
                continue
                
            caminho_subpasta = os.path.join(pasta_fotos, nome_pasta_pessoa)

            if os.path.isdir(caminho_subpasta):
                self.adicionar_log(f"  -> Nova pasta de fotos detectada: '{nome_pasta_pessoa}'")
                fotos_na_pasta = 0
                for arquivo_foto in os.listdir(caminho_subpasta):
                    if not arquivo_foto.lower().endswith((".jpg", ".jpeg", ".png")):
                        continue
                        
                    caminho_imagem = os.path.join(caminho_subpasta, arquivo_foto)
                    try:
                        imagem = face_recognition.load_image_file(caminho_imagem)
                        faces = face_recognition.face_encodings(imagem)
                        if faces:
                            self.encodings_conhecidos.append(faces[0])
                            self.nomes_conhecidos.append(nome_pasta_pessoa) 
                            self.fotos_conhecidas.append(arquivo_foto)
                            fotos_na_pasta += 1
                        else:
                            self.adicionar_log(f"    ⚠️  Aviso: Nenhum rosto detectado em '{arquivo_foto}'.")
                    except Exception as e:
                        self.adicionar_log(f"    ❌ Erro ao processar o arquivo '{arquivo_foto}': {e}")
                
                if fotos_na_pasta > 0:
                    self.atualizar_stat('fotos', fotos_na_pasta)
                    novas_fotos_encontradas += fotos_na_pasta
                
                self.pastas_fotos_processadas.add(nome_pasta_pessoa)
        
        if novas_fotos_encontradas > 0:
            self.adicionar_log(f"✅ {novas_fotos_encontradas} novas fotos de referência carregadas.")

    def processar_lote_videos(self):
        """
        (Thread de Trabalho) Varre subpastas de câmeras e processa vídeos.
        """
        pasta_raiz_videos = self.parametros['videos_a_processar']
        pasta_destino_processados = self.parametros['videos_processados']
        extensoes_validas = ('.mp4', '.avi', '.mov', '.mkv')
        
        if not os.path.isdir(pasta_raiz_videos):
            self.adicionar_log(f"⚠️ Pasta de vídeos a processar não encontrada: {pasta_raiz_videos}")
            return

        videos_encontrados_no_lote = 0
        
        for nome_camera in os.listdir(pasta_raiz_videos):
            if not self.running: return 
            
            pasta_camera = os.path.join(pasta_raiz_videos, nome_camera)
            if not os.path.isdir(pasta_camera):
                continue

            self.adicionar_log(f"Verificando Câmera: {nome_camera}")
            
            for nome_video in os.listdir(pasta_camera):
                if not self.running: return 
                
                if not nome_video.lower().endswith(extensoes_validas):
                    continue
                    
                videos_encontrados_no_lote += 1
                caminho_video_entrada = os.path.join(pasta_camera, nome_video)
                
                self.adicionar_log(f"  🎥 Processando: {nome_camera} / {nome_video}")
                
                # 3. Processa o vídeo
                resultados = self.processar_video(caminho_video_entrada)
                
                # 4. Salva os resultados no banco
                # (MODIFICADO V3.1) Passa o 'nome_camera' para a função de salvar
                self.salvar_resultados_db(resultados, nome_video, nome_camera)
                
                # 5. Move o vídeo processado
                try:
                    os.makedirs(pasta_destino_processados, exist_ok=True)
                    caminho_destino_video = os.path.join(pasta_destino_processados, nome_video)
                    
                    if os.path.exists(caminho_destino_video):
                        base, ext = os.path.splitext(caminho_destino_video)
                        caminho_destino_video = f"{base}_{int(time.time())}{ext}"
                        self.adicionar_log(f"  ⚠️  Aviso: Vídeo já existe no destino. Renomeando para: {os.path.basename(caminho_destino_video)}")

                    self.adicionar_log(f"  🚚 Movendo vídeo para: {caminho_destino_video}")
                    shutil.move(caminho_video_entrada, caminho_destino_video)
                    self.atualizar_stat('videos', 1)
                except Exception as e:
                    self.adicionar_log(f"  ❌ Erro ao mover o vídeo processado: {e}")

        if videos_encontrados_no_lote == 0:
            self.adicionar_log("Nenhum vídeo novo encontrado neste lote.")

    def processar_video(self, caminho_video_entrada):
        """
        (Thread de Trabalho) Processa um único vídeo.
        """
        video = cv2.VideoCapture(caminho_video_entrada)
        if not video.isOpened():
            self.adicionar_log(f"   ❌ Erro: Não foi possível abrir o vídeo '{caminho_video_entrada}'.")
            return []

        fps = video.get(cv2.CAP_PROP_FPS)
        largura = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
        altura = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))

        saida_video = None
        if self.parametros['gerar_marcoes']:
            nome_base_video = os.path.splitext(os.path.basename(caminho_video_entrada))[0]
            nome_arquivo_saida = f"{nome_base_video}_marcado.mp4"
            caminho_video_saida = os.path.join(self.parametros['video_marcoes'], nome_arquivo_saida)
            os.makedirs(self.parametros['video_marcoes'], exist_ok=True)
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            saida_video = cv2.VideoWriter(caminho_video_saida, fourcc, fps, (largura, altura))

        self.adicionar_log(f"   Analizando... (Total frames: {total_frames})")

        resultados = []
        frame_idx = 0
        face_locations = []
        face_names = []
        
        intervalo_frames = self.parametros['intervalo_frames']
        escala_imagem = self.parametros['escala_imagem']
        modelo_deteccao = self.parametros['modelo_deteccao']
        tolerancia = self.parametros['tolerancia']
        
        encodings_atuais = list(self.encodings_conhecidos)
        nomes_atuais = list(self.nomes_conhecidos)
        fotos_atuais = list(self.fotos_conhecidas)

        try:
            while self.running: 
                ret, frame = video.read()
                if not ret:
                    break

                if frame_idx % intervalo_frames == 0:
                    small_frame = cv2.resize(frame, (0, 0), fx=escala_imagem, fy=escala_imagem)
                    rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

                    face_locations = face_recognition.face_locations(rgb_frame, model=modelo_deteccao)
                    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

                    face_names = []
                    for face_encoding in face_encodings:
                        if not encodings_atuais:
                            face_names.append("Desconhecido")
                            continue

                        matches = face_recognition.compare_faces(encodings_atuais, face_encoding, tolerance=tolerancia)
                        face_distances = face_recognition.face_distance(encodings_atuais, face_encoding)

                        nome = "Desconhecido"
                        if True in matches:
                            melhor_idx = face_distances.argmin()
                            if matches[melhor_idx]:
                                nome = nomes_atuais[melhor_idx]
                                foto_reconhecida = fotos_atuais[melhor_idx]
                                tempo_video = frame_idx / fps

                                self.atualizar_stat('encontrados', 1)

                                if not any(d['nome'] == nome for d in resultados):
                                    resultados.append({
                                        "nome": nome,
                                        "tempo_segundos": round(tempo_video, 2),
                                        "foto_reconhecida": foto_reconhecida
                                    })
                                    self.adicionar_log(f"     -> Encontrado: {nome} (foto: '{foto_reconhecida}') aos {tempo_video:.2f}s")
                        else:
                            self.atualizar_stat('desconhecidos', 1)
                            
                        face_names.append(nome)

                if self.parametros['gerar_marcoes'] and saida_video:
                    for (top, right, bottom, left), name in zip(face_locations, face_names):
                        top, right, bottom, left = [int(v / escala_imagem) for v in (top, right, bottom, left)]
                        cor = (0, 255, 0) if name != "Desconhecido" else (0, 0, 255)
                        cv2.rectangle(frame, (left, top), (right, bottom), cor, 2)
                        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), cor, cv2.FILLED)
                        cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 1.0, (255, 255, 255), 1)
                    
                    saida_video.write(frame)

                frame_idx += 1
        
        finally:
            self.adicionar_log(f"   -> Análise concluída.")
            video.release()
            if saida_video:
                saida_video.release()
            cv2.destroyAllWindows()

        return resultados

    def salvar_resultados_db(self, resultados, nome_arquivo_video, nome_camera):
        """
        (MODIFICADO V3.1) Salva os resultados no DB, incluindo o nomeCamera.
        """
        if not resultados:
            self.adicionar_log("   -> Nenhum reconhecimento para salvar no banco.")
            return

        # (MODIFICADO V3.1) Adiciona "nomeCamera" ao SQL
        sql = """
            INSERT INTO sch_supervisorio.tb_videos_processados
            ("nomeArquivoVideo", datahoraprocessamento, "nomeArquivoFoto", 
             "tempoMarcacaoSegundos", "nomePastaPessoa", "nomeCamera")
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        conn = get_db_connection()
        if conn is None:
            self.adicionar_log("   ❌ Erro: Não foi possível conectar ao DB para salvar resultados.")
            return
        
        agora = datetime.now()
        dados_para_inserir = []
        
        for item in resultados:
            dados_para_inserir.append((
                nome_arquivo_video,       
                agora,                    
                item['foto_reconhecida'], 
                item['tempo_segundos'],   
                item['nome'],
                nome_camera # (MODIFICADO V3.1) Adiciona o novo campo
            ))
        
        try:
            with conn.cursor() as cur:
                cur.executemany(sql, dados_para_inserir)
            conn.commit()
            self.adicionar_log(f"   -> {len(dados_para_inserir)} registros de reconhecimento salvos no banco.")
        except Exception as e:
            conn.rollback()
            self.adicionar_log(f"   ❌ Erro ao salvar resultados no banco: {e} (Verifique se a coluna 'nomeCamera' existe em 'tb_videos_processados')")
        finally:
            conn.close()


# --- Ponto de Entrada da Aplicação ---
if __name__ == "__main__":
    root = tk.Tk()
    app = ProcessadorApp(root)
    root.mainloop()