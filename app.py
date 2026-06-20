"""
app.py — Interface gráfica do Study Timer (CustomTkinter).

Um aplicativo moderno de produtividade para gerenciar tarefas,
cronometrar sessões de estudo e visualizar métricas acumuladas.
"""

import customtkinter as ctk
from tkinter import messagebox
import threading
import time
import winsound
import data_manager as dm

# ──────────────────────────────────────────────
#  Paleta de Cores e Configurações Visuais
# ──────────────────────────────────────────────

# Cores do tema (paleta premium escura com acentos vibrantes)
COLORS = {
    "bg_primary": "#0F0F1A",       # Fundo principal (quase preto azulado)
    "bg_secondary": "#1A1A2E",     # Cards / painéis
    "bg_tertiary": "#16213E",      # Inputs / áreas interativas
    "accent": "#6C63FF",           # Roxo vibrante principal
    "accent_hover": "#5A52D5",     # Hover do accent
    "accent_green": "#00D4AA",     # Verde para sucesso / progresso
    "accent_red": "#FF6B6B",       # Vermelho para remoção / alerta
    "accent_amber": "#FFB347",     # Âmbar para avisos
    "text_primary": "#EAEAEA",     # Texto principal
    "text_secondary": "#8892A8",   # Texto secundário / labels
    "text_muted": "#4A5568",       # Texto muito discreto
    "border": "#2D2D44",           # Bordas sutis
    "timer_ring": "#6C63FF",       # Anel do timer
    "timer_bg": "#1E1E36",         # Fundo do timer
}

FONT_FAMILY = "Segoe UI"
TIMER_FONT = ("Consolas", 64)
TITLE_FONT = (FONT_FAMILY, 22, "bold")
SUBTITLE_FONT = (FONT_FAMILY, 14, "bold")
BODY_FONT = (FONT_FAMILY, 13)
SMALL_FONT = (FONT_FAMILY, 11)
TINY_FONT = (FONT_FAMILY, 10)


class StudyTimerApp(ctk.CTk):
    """Janela principal do aplicativo Study Timer."""

    def __init__(self):
        super().__init__()

        # ── Configuração da janela ──
        self.title("⏱ Study Timer — Produtividade")
        self.geometry("960x680")
        self.minsize(900, 640)
        self.configure(fg_color=COLORS["bg_primary"])

        # ── Estado do Timer ──
        self.timer_running = False
        self.timer_paused = False
        self.timer_thread: threading.Thread | None = None
        self.remaining_seconds = 0
        self.total_session_seconds = 0
        self.selected_task: dict | None = None

        # ── Layout principal: sidebar + conteúdo ──
        self._build_sidebar()
        self._build_main_content()

        # ── Carrega dados iniciais ──
        self._refresh_task_list()
        self._refresh_metrics()

        # Atalho de teclado para focar
        self.bind("<Escape>", lambda e: self._stop_timer())

    # ══════════════════════════════════════════════
    #  SIDEBAR (Navegação + Tarefas)
    # ══════════════════════════════════════════════

    def _build_sidebar(self):
        """Constrói o painel lateral com lista de tarefas."""
        self.sidebar = ctk.CTkFrame(
            self, width=280, fg_color=COLORS["bg_secondary"],
            corner_radius=0, border_width=0,
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # ── Logo / Título ──
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", padx=20, pady=(24, 4))

        ctk.CTkLabel(
            logo_frame, text="📚", font=(FONT_FAMILY, 28),
            text_color=COLORS["accent"],
        ).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            logo_frame, text="Study Timer",
            font=TITLE_FONT, text_color=COLORS["text_primary"],
        ).pack(side="left")

        ctk.CTkLabel(
            self.sidebar, text="Gerencie suas tarefas e sessões de estudo",
            font=TINY_FONT, text_color=COLORS["text_muted"],
            wraplength=240, justify="left",
        ).pack(fill="x", padx=24, pady=(0, 16))

        # ── Separador ──
        ctk.CTkFrame(
            self.sidebar, height=1, fg_color=COLORS["border"],
        ).pack(fill="x", padx=16, pady=(0, 16))

        # ── Adicionar nova tarefa ──
        ctk.CTkLabel(
            self.sidebar, text="NOVA TAREFA",
            font=(FONT_FAMILY, 10, "bold"),
            text_color=COLORS["text_secondary"],
        ).pack(anchor="w", padx=24, pady=(0, 6))

        add_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        add_frame.pack(fill="x", padx=16, pady=(0, 12))

        self.task_entry = ctk.CTkEntry(
            add_frame, placeholder_text="Nome da tarefa...",
            font=BODY_FONT, height=38,
            fg_color=COLORS["bg_tertiary"],
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            placeholder_text_color=COLORS["text_muted"],
        )
        self.task_entry.pack(side="left", fill="x", expand=True, padx=(4, 6))
        self.task_entry.bind("<Return>", lambda e: self._add_task())

        ctk.CTkButton(
            add_frame, text="＋", width=38, height=38,
            font=(FONT_FAMILY, 18, "bold"),
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            corner_radius=10,
            command=self._add_task,
        ).pack(side="right")

        # ── Lista de Tarefas (scrollável) ──
        ctk.CTkLabel(
            self.sidebar, text="MINHAS TAREFAS",
            font=(FONT_FAMILY, 10, "bold"),
            text_color=COLORS["text_secondary"],
        ).pack(anchor="w", padx=24, pady=(8, 6))

        self.task_scroll = ctk.CTkScrollableFrame(
            self.sidebar, fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["accent"],
        )
        self.task_scroll.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # ── Rodapé da sidebar ──
        footer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        footer.pack(fill="x", padx=16, pady=(4, 16))

        self.task_count_label = ctk.CTkLabel(
            footer, text="0 tarefas", font=TINY_FONT,
            text_color=COLORS["text_muted"],
        )
        self.task_count_label.pack(side="left", padx=8)

    # ══════════════════════════════════════════════
    #  CONTEÚDO PRINCIPAL (Timer + Métricas)
    # ══════════════════════════════════════════════

    def _build_main_content(self):
        """Constrói a área principal com timer e métricas."""
        self.main = ctk.CTkFrame(
            self, fg_color=COLORS["bg_primary"], corner_radius=0,
        )
        self.main.pack(side="right", fill="both", expand=True)

        # ── Tabview: Timer | Métricas ──
        self.tabs = ctk.CTkTabview(
            self.main, fg_color=COLORS["bg_primary"],
            segmented_button_fg_color=COLORS["bg_secondary"],
            segmented_button_selected_color=COLORS["accent"],
            segmented_button_selected_hover_color=COLORS["accent_hover"],
            segmented_button_unselected_color=COLORS["bg_secondary"],
            segmented_button_unselected_hover_color=COLORS["bg_tertiary"],
            text_color=COLORS["text_primary"],
            text_color_disabled=COLORS["text_muted"],
            corner_radius=12,
        )
        self.tabs.pack(fill="both", expand=True, padx=20, pady=(16, 20))

        tab_timer = self.tabs.add("⏱  Timer")
        tab_metrics = self.tabs.add("📊  Métricas")
        tab_history = self.tabs.add("📋  Histórico")

        self._build_timer_tab(tab_timer)
        self._build_metrics_tab(tab_metrics)
        self._build_history_tab(tab_history)

    # ──────────────────────────────────────────────
    #  ABA: Timer
    # ──────────────────────────────────────────────

    def _build_timer_tab(self, parent):
        """Constrói a aba do cronômetro."""
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(expand=True)

        # ── Tarefa selecionada ──
        self.selected_label = ctk.CTkLabel(
            container, text="Nenhuma tarefa selecionada",
            font=SUBTITLE_FONT, text_color=COLORS["text_secondary"],
        )
        self.selected_label.pack(pady=(10, 4))

        self.status_label = ctk.CTkLabel(
            container, text="Selecione uma tarefa na sidebar para começar",
            font=SMALL_FONT, text_color=COLORS["text_muted"],
        )
        self.status_label.pack(pady=(0, 20))

        # ── Display do Timer (Canvas circular) ──
        self.timer_canvas_frame = ctk.CTkFrame(
            container, fg_color=COLORS["timer_bg"],
            corner_radius=120, width=240, height=240,
        )
        self.timer_canvas_frame.pack(pady=(0, 16))
        self.timer_canvas_frame.pack_propagate(False)

        self.timer_display = ctk.CTkLabel(
            self.timer_canvas_frame, text="00:00",
            font=TIMER_FONT, text_color=COLORS["text_primary"],
        )
        self.timer_display.place(relx=0.5, rely=0.5, anchor="center")

        # ── Barra de progresso ──
        self.progress_bar = ctk.CTkProgressBar(
            container, width=300, height=6,
            progress_color=COLORS["accent"],
            fg_color=COLORS["bg_tertiary"],
            corner_radius=3,
        )
        self.progress_bar.pack(pady=(0, 20))
        self.progress_bar.set(0)

        # ── Input de minutos ──
        time_frame = ctk.CTkFrame(container, fg_color="transparent")
        time_frame.pack(pady=(0, 16))

        ctk.CTkLabel(
            time_frame, text="Duração (minutos):",
            font=BODY_FONT, text_color=COLORS["text_secondary"],
        ).pack(side="left", padx=(0, 8))

        self.minutes_entry = ctk.CTkEntry(
            time_frame, width=80, height=36,
            font=BODY_FONT, justify="center",
            fg_color=COLORS["bg_tertiary"],
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            placeholder_text="25",
            placeholder_text_color=COLORS["text_muted"],
        )
        self.minutes_entry.pack(side="left")
        self.minutes_entry.insert(0, "25")

        # ── Presets de tempo ──
        presets_frame = ctk.CTkFrame(container, fg_color="transparent")
        presets_frame.pack(pady=(0, 20))

        for mins, label in [(15, "15m"), (25, "25m"), (45, "45m"), (60, "1h"), (90, "1h30")]:
            ctk.CTkButton(
                presets_frame, text=label, width=56, height=30,
                font=SMALL_FONT,
                fg_color=COLORS["bg_tertiary"],
                hover_color=COLORS["accent"],
                text_color=COLORS["text_secondary"],
                corner_radius=8,
                command=lambda m=mins: self._set_preset(m),
            ).pack(side="left", padx=3)

        # ── Botões de controle ──
        controls = ctk.CTkFrame(container, fg_color="transparent")
        controls.pack(pady=(0, 10))

        self.start_btn = ctk.CTkButton(
            controls, text="▶  Iniciar", width=130, height=44,
            font=(FONT_FAMILY, 14, "bold"),
            fg_color=COLORS["accent_green"],
            hover_color="#00B894",
            text_color="#0F0F1A",
            corner_radius=12,
            command=self._start_timer,
        )
        self.start_btn.pack(side="left", padx=6)

        self.pause_btn = ctk.CTkButton(
            controls, text="⏸  Pausar", width=120, height=44,
            font=(FONT_FAMILY, 14, "bold"),
            fg_color=COLORS["accent_amber"],
            hover_color="#E6A23C",
            text_color="#0F0F1A",
            corner_radius=12,
            state="disabled",
            command=self._pause_timer,
        )
        self.pause_btn.pack(side="left", padx=6)

        self.stop_btn = ctk.CTkButton(
            controls, text="⏹  Parar", width=120, height=44,
            font=(FONT_FAMILY, 14, "bold"),
            fg_color=COLORS["accent_red"],
            hover_color="#E05252",
            text_color="#FFFFFF",
            corner_radius=12,
            state="disabled",
            command=self._stop_timer,
        )
        self.stop_btn.pack(side="left", padx=6)

    # ──────────────────────────────────────────────
    #  ABA: Métricas 
    # ──────────────────────────────────────────────

    def _build_metrics_tab(self, parent):
        """Constrói a aba de métricas / dashboard."""
        # ── Header ──
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16, 8))

        ctk.CTkLabel(
            header, text="Dashboard de Produtividade",
            font=TITLE_FONT, text_color=COLORS["text_primary"],
        ).pack(side="left")

        ctk.CTkButton(
            header, text="🔄 Atualizar", width=110, height=32,
            font=SMALL_FONT,
            fg_color=COLORS["bg_tertiary"],
            hover_color=COLORS["accent"],
            text_color=COLORS["text_secondary"],
            corner_radius=8,
            command=self._refresh_metrics,
        ).pack(side="right")

        # ── Cards de resumo ──
        self.summary_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.summary_frame.pack(fill="x", padx=20, pady=(4, 12))

        self.total_time_card = self._create_summary_card(
            self.summary_frame, "⏱", "Tempo Total", "0h 0m", COLORS["accent"]
        )
        self.total_sessions_card = self._create_summary_card(
            self.summary_frame, "🔥", "Sessões", "0", COLORS["accent_green"]
        )
        self.total_tasks_card = self._create_summary_card(
            self.summary_frame, "📋", "Tarefas", "0", COLORS["accent_amber"]
        )

        # ── Tabela de métricas por tarefa ──
        ctk.CTkLabel(
            parent, text="TEMPO POR TAREFA",
            font=(FONT_FAMILY, 10, "bold"),
            text_color=COLORS["text_secondary"],
        ).pack(anchor="w", padx=24, pady=(4, 6))

        self.metrics_scroll = ctk.CTkScrollableFrame(
            parent, fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
        )
        self.metrics_scroll.pack(fill="both", expand=True, padx=16, pady=(0, 12))

    def _create_summary_card(self, parent, icon, title, value, color):
        """Cria um card de resumo para o dashboard."""
        card = ctk.CTkFrame(
            parent, fg_color=COLORS["bg_secondary"],
            corner_radius=14, border_width=1,
            border_color=COLORS["border"],
        )
        card.pack(side="left", fill="x", expand=True, padx=6, pady=4)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(padx=16, pady=14)

        ctk.CTkLabel(
            inner, text=icon, font=(FONT_FAMILY, 24),
        ).pack(anchor="w")

        ctk.CTkLabel(
            inner, text=title, font=TINY_FONT,
            text_color=COLORS["text_muted"],
        ).pack(anchor="w", pady=(4, 0))

        value_label = ctk.CTkLabel(
            inner, text=value, font=(FONT_FAMILY, 20, "bold"),
            text_color=color,
        )
        value_label.pack(anchor="w")

        return value_label  # Retorna label para atualização dinâmica

    # ──────────────────────────────────────────────
    #  ABA: Histórico
    # ──────────────────────────────────────────────

    def _build_history_tab(self, parent):
        """Constrói a aba de histórico de sessões."""
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16, 8))

        ctk.CTkLabel(
            header, text="Histórico de Sessões",
            font=TITLE_FONT, text_color=COLORS["text_primary"],
        ).pack(side="left")

        self.history_scroll = ctk.CTkScrollableFrame(
            parent, fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
        )
        self.history_scroll.pack(fill="both", expand=True, padx=16, pady=(4, 12))

    # ══════════════════════════════════════════════
    #  LÓGICA DE TAREFAS
    # ══════════════════════════════════════════════

    def _add_task(self):
        """Adiciona uma nova tarefa via input da sidebar."""
        name = self.task_entry.get().strip()
        if not name:
            messagebox.showwarning("Aviso", "Digite o nome da tarefa.")
            return
        try:
            dm.add_task(name)
            self.task_entry.delete(0, "end")
            self._refresh_task_list()
            self._refresh_metrics()
        except ValueError as e:
            messagebox.showerror("Erro", str(e))

    def _remove_task(self, task_id: int):
        """Remove uma tarefa após confirmação."""
        task = dm.get_task_by_id(task_id)
        if task and messagebox.askyesno(
            "Confirmar Remoção",
            f"Deseja remover a tarefa '{task['name']}'?\n\n"
            "O histórico de sessões dessa tarefa será mantido.",
        ):
            try:
                dm.remove_task(task_id)
                # Desseleciona se era a tarefa ativa
                if self.selected_task and self.selected_task["id"] == task_id:
                    self.selected_task = None
                    self.selected_label.configure(text="Nenhuma tarefa selecionada")
                    self.status_label.configure(
                        text="Selecione uma tarefa na sidebar para começar"
                    )
                self._refresh_task_list()
                self._refresh_metrics()
            except ValueError as e:
                messagebox.showerror("Erro", str(e))

    def _select_task(self, task: dict):
        """Seleciona uma tarefa para o timer."""
        if self.timer_running:
            messagebox.showwarning(
                "Timer Ativo",
                "Pare o timer antes de trocar de tarefa."
            )
            return
        self.selected_task = task
        self.selected_label.configure(
            text=f"📌  {task['name']}",
            text_color=COLORS["accent"],
        )
        self.status_label.configure(
            text="Pronto! Defina o tempo e clique em Iniciar.",
            text_color=COLORS["accent_green"],
        )
        self._refresh_task_list()  # Atualiza visual de seleção

    def _refresh_task_list(self):
        """Atualiza a lista de tarefas na sidebar."""
        # Limpa widgets antigos
        for widget in self.task_scroll.winfo_children():
            widget.destroy()

        tasks = dm.get_tasks()
        self.task_count_label.configure(
            text=f"{len(tasks)} tarefa{'s' if len(tasks) != 1 else ''}"
        )

        if not tasks:
            ctk.CTkLabel(
                self.task_scroll,
                text="Nenhuma tarefa ainda.\nCrie uma acima! ✨",
                font=SMALL_FONT,
                text_color=COLORS["text_muted"],
                justify="center",
            ).pack(pady=30)
            return

        for task in tasks:
            is_selected = (
                self.selected_task and self.selected_task["id"] == task["id"]
            )
            self._create_task_card(task, is_selected)

    def _create_task_card(self, task: dict, selected: bool):
        """Cria um card visual para uma tarefa na sidebar."""
        bg = COLORS["accent"] if selected else COLORS["bg_tertiary"]
        text_color = "#FFFFFF" if selected else COLORS["text_primary"]
        border_color = COLORS["accent"] if selected else COLORS["border"]

        card = ctk.CTkFrame(
            self.task_scroll, fg_color=bg,
            corner_radius=10, height=44,
            border_width=1, border_color=border_color,
            cursor="hand2",
        )
        card.pack(fill="x", pady=2, padx=4)
        card.pack_propagate(False)

        # Nome da tarefa (clicável)
        name_label = ctk.CTkLabel(
            card, text=f"  {task['name']}",
            font=BODY_FONT, text_color=text_color,
            cursor="hand2", anchor="w",
        )
        name_label.pack(side="left", fill="x", expand=True, padx=(8, 0))

        # Bind de clique na tarefa
        for widget in (card, name_label):
            widget.bind("<Button-1>", lambda e, t=task: self._select_task(t))

        # Botão de remover
        del_btn = ctk.CTkButton(
            card, text="✕", width=28, height=28,
            font=(FONT_FAMILY, 12, "bold"),
            fg_color="transparent",
            hover_color=COLORS["accent_red"],
            text_color=COLORS["text_muted"] if not selected else "#FFFFFF",
            corner_radius=6,
            command=lambda tid=task["id"]: self._remove_task(tid),
        )
        del_btn.pack(side="right", padx=4)

    # ══════════════════════════════════════════════
    #  LÓGICA DO TIMER
    # ══════════════════════════════════════════════

    def _set_preset(self, minutes: int):
        """Define um tempo preset no entry."""
        self.minutes_entry.delete(0, "end")
        self.minutes_entry.insert(0, str(minutes))

    def _start_timer(self):
        """Inicia ou retoma o cronômetro."""
        if not self.selected_task:
            messagebox.showwarning(
                "Sem Tarefa",
                "Selecione uma tarefa na sidebar antes de iniciar.",
            )
            return

        if self.timer_paused:
            # Retoma de pausa
            self.timer_paused = False
            self.timer_running = True
            self._update_button_states(running=True)
            self.status_label.configure(
                text="⏱ Timer retomado!",
                text_color=COLORS["accent_green"],
            )
            return

        # Valida entrada de minutos
        try:
            minutes = int(self.minutes_entry.get())
            if minutes <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Tempo Inválido",
                "Digite um número inteiro positivo para os minutos.",
            )
            return

        # Inicia novo timer
        self.total_session_seconds = minutes * 60
        self.remaining_seconds = self.total_session_seconds
        self.timer_running = True
        self.timer_paused = False
        self._update_button_states(running=True)

        self.status_label.configure(
            text=f"⏱ Estudando: {self.selected_task['name']}",
            text_color=COLORS["accent_green"],
        )

        # Thread do timer (não trava a UI)
        self.timer_thread = threading.Thread(target=self._timer_loop, daemon=True)
        self.timer_thread.start()

    def _pause_timer(self):
        """Pausa o cronômetro."""
        if self.timer_running and not self.timer_paused:
            self.timer_paused = True
            self.timer_running = False
            self.start_btn.configure(text="▶  Retomar", state="normal")
            self.pause_btn.configure(state="disabled")
            self.status_label.configure(
                text="⏸ Timer pausado",
                text_color=COLORS["accent_amber"],
            )

    def _stop_timer(self):
        """Para o cronômetro e registra a sessão parcial."""
        if not self.timer_running and not self.timer_paused:
            return

        elapsed = self.total_session_seconds - self.remaining_seconds
        self.timer_running = False
        self.timer_paused = False
        self._update_button_states(running=False)
        self.timer_display.configure(text="00:00")
        self.progress_bar.set(0)

        # Registra sessão se houve tempo significativo (≥ 5 segundos)
        if elapsed >= 5 and self.selected_task:
            dm.log_session(self.selected_task["id"], elapsed)
            self.status_label.configure(
                text=f"✅ Sessão de {dm.format_seconds(elapsed)} registrada!",
                text_color=COLORS["accent_green"],
            )
            self._refresh_metrics()
            self._refresh_history()
        else:
            self.status_label.configure(
                text="⏹ Timer parado (sessão muito curta, não registrada).",
                text_color=COLORS["text_muted"],
            )

    def _timer_loop(self):
        """Loop do timer executado em thread separada."""
        while self.remaining_seconds > 0:
            if not self.timer_running:
                if self.timer_paused:
                    time.sleep(0.1)
                    continue
                else:
                    return  # Parado pelo usuário

            # Atualiza display na thread principal
            self.after(0, self._update_timer_display)
            time.sleep(1)

            if self.timer_running:
                self.remaining_seconds -= 1

        # Timer concluído!
        self.after(0, self._timer_finished)

    def _update_timer_display(self):
        """Atualiza o display do timer e a barra de progresso."""
        mins = self.remaining_seconds // 60
        secs = self.remaining_seconds % 60
        self.timer_display.configure(text=f"{mins:02d}:{secs:02d}")

        # Atualiza progresso
        if self.total_session_seconds > 0:
            progress = 1 - (self.remaining_seconds / self.total_session_seconds)
            self.progress_bar.set(progress)

            # Muda cor nos últimos 60 segundos
            if self.remaining_seconds <= 60:
                self.progress_bar.configure(progress_color=COLORS["accent_red"])
                self.timer_display.configure(text_color=COLORS["accent_red"])
            elif self.remaining_seconds <= 300:
                self.progress_bar.configure(progress_color=COLORS["accent_amber"])
                self.timer_display.configure(text_color=COLORS["accent_amber"])
            else:
                self.progress_bar.configure(progress_color=COLORS["accent"])
                self.timer_display.configure(text_color=COLORS["text_primary"])

    def _timer_finished(self):
        """Chamado quando o timer chega a zero."""
        elapsed = self.total_session_seconds
        self.timer_running = False
        self.timer_paused = False
        self._update_button_states(running=False)
        self.timer_display.configure(text="00:00", text_color=COLORS["accent_green"])
        self.progress_bar.set(1)
        self.progress_bar.configure(progress_color=COLORS["accent_green"])

        # Registra sessão completa
        if self.selected_task:
            dm.log_session(self.selected_task["id"], elapsed)
            self._refresh_metrics()
            self._refresh_history()

        self.status_label.configure(
            text=f"🎉 Sessão de {dm.format_seconds(elapsed)} concluída!",
            text_color=COLORS["accent_green"],
        )

        # Alerta sonoro (beep do Windows)
        try:
            for _ in range(3):
                winsound.Beep(800, 300)
                time.sleep(0.15)
        except Exception:
            pass  # Fallback silencioso se o áudio falhar

        # Alerta visual (popup)
        messagebox.showinfo(
            "⏱ Sessão Concluída!",
            f"Você completou {dm.format_seconds(elapsed)} de estudo em\n"
            f"'{self.selected_task['name']}'!\n\n"
            "Excelente trabalho! 🎯",
        )

    def _update_button_states(self, running: bool):
        """Atualiza o estado dos botões de controle."""
        if running:
            self.start_btn.configure(text="▶  Iniciar", state="disabled")
            self.pause_btn.configure(state="normal")
            self.stop_btn.configure(state="normal")
        else:
            self.start_btn.configure(text="▶  Iniciar", state="normal")
            self.pause_btn.configure(state="disabled")
            self.stop_btn.configure(state="disabled")

    # ══════════════════════════════════════════════
    #  MÉTRICAS E HISTÓRICO
    # ══════════════════════════════════════════════

    def _refresh_metrics(self):
        """Atualiza o dashboard de métricas."""
        metrics = dm.get_task_metrics()
        sessions = dm.get_sessions()
        tasks = dm.get_tasks()

        # Atualiza cards de resumo
        total_secs = sum(m["total_seconds"] for m in metrics)
        self.total_time_card.configure(text=dm.format_seconds(total_secs))
        self.total_sessions_card.configure(text=str(len(sessions)))
        self.total_tasks_card.configure(text=str(len(tasks)))

        # Limpa tabela anterior
        for widget in self.metrics_scroll.winfo_children():
            widget.destroy()

        if not metrics:
            ctk.CTkLabel(
                self.metrics_scroll,
                text="Nenhuma métrica ainda.\nComplete sessões para ver seus dados! 📊",
                font=SMALL_FONT,
                text_color=COLORS["text_muted"],
                justify="center",
            ).pack(pady=30)
            return

        # Encontra o maior tempo para calcular barras proporcionais
        max_secs = max(m["total_seconds"] for m in metrics) if metrics else 1

        for m in metrics:
            self._create_metric_row(m, max_secs)

    def _create_metric_row(self, metric: dict, max_secs: int):
        """Cria uma linha de métrica com barra de progresso."""
        row = ctk.CTkFrame(
            self.metrics_scroll, fg_color=COLORS["bg_secondary"],
            corner_radius=10, height=60,
        )
        row.pack(fill="x", pady=3, padx=4)
        row.pack_propagate(False)

        # Conteúdo da linha
        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=8)

        # Nome + contagem de sessões
        top = ctk.CTkFrame(inner, fg_color="transparent")
        top.pack(fill="x")

        ctk.CTkLabel(
            top, text=metric["task_name"],
            font=(FONT_FAMILY, 13, "bold"),
            text_color=COLORS["text_primary"],
        ).pack(side="left")

        ctk.CTkLabel(
            top, text=f"{metric['session_count']} sessões",
            font=TINY_FONT,
            text_color=COLORS["text_muted"],
        ).pack(side="right")

        # Barra de progresso proporcional + tempo
        bottom = ctk.CTkFrame(inner, fg_color="transparent")
        bottom.pack(fill="x", pady=(4, 0))

        progress = metric["total_seconds"] / max_secs if max_secs > 0 else 0
        bar = ctk.CTkProgressBar(
            bottom, width=300, height=8,
            progress_color=COLORS["accent"],
            fg_color=COLORS["bg_tertiary"],
            corner_radius=4,
        )
        bar.pack(side="left", fill="x", expand=True, padx=(0, 12))
        bar.set(progress)

        ctk.CTkLabel(
            bottom, text=metric["total_formatted"],
            font=(FONT_FAMILY, 12, "bold"),
            text_color=COLORS["accent"],
        ).pack(side="right")

    def _refresh_history(self):
        """Atualiza o histórico de sessões."""
        for widget in self.history_scroll.winfo_children():
            widget.destroy()

        sessions = dm.get_sessions()

        if not sessions:
            ctk.CTkLabel(
                self.history_scroll,
                text="Nenhuma sessão registrada ainda.\nComplete um timer para começar! ⏱",
                font=SMALL_FONT,
                text_color=COLORS["text_muted"],
                justify="center",
            ).pack(pady=30)
            return

        # Mostra sessões mais recentes primeiro
        for session in reversed(sessions[-50:]):  # Últimas 50
            self._create_history_row(session)

    def _create_history_row(self, session: dict):
        """Cria uma linha no histórico de sessões."""
        row = ctk.CTkFrame(
            self.history_scroll, fg_color=COLORS["bg_secondary"],
            corner_radius=8, height=46,
        )
        row.pack(fill="x", pady=2, padx=4)
        row.pack_propagate(False)

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=14, pady=6)

        # Ícone + nome da tarefa
        ctk.CTkLabel(
            inner, text=f"📖  {session['task_name']}",
            font=BODY_FONT, text_color=COLORS["text_primary"],
        ).pack(side="left")

        # Data/hora
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(session["completed_at"])
            formatted_date = dt.strftime("%d/%m/%Y %H:%M")
        except Exception:
            formatted_date = session.get("completed_at", "")

        ctk.CTkLabel(
            inner, text=formatted_date,
            font=TINY_FONT, text_color=COLORS["text_muted"],
        ).pack(side="right", padx=(12, 0))

        # Duração
        ctk.CTkLabel(
            inner, text=dm.format_seconds(session["duration_seconds"]),
            font=(FONT_FAMILY, 12, "bold"),
            text_color=COLORS["accent_green"],
        ).pack(side="right")


# ══════════════════════════════════════════════
#  PONTO DE ENTRADA
# ══════════════════════════════════════════════

if __name__ == "__main__":
    # Configuração global do CustomTkinter
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    app = StudyTimerApp()
    app.mainloop()
