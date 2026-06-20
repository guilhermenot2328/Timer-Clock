"""
data_manager.py — Camada de persistência de dados (JSON).

Responsável por criar, ler, atualizar e deletar tarefas,
além de registrar sessões de estudo e calcular métricas acumuladas.
"""

import json
import os
from datetime import datetime
from typing import Optional

# Caminho do arquivo de dados — mesma pasta do script
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "study_data.json")


def _load_data() -> dict:
    """Carrega os dados do arquivo JSON. Retorna estrutura padrão se não existir."""
    if not os.path.exists(DATA_FILE):
        return {"tasks": [], "sessions": []}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Garante que as chaves obrigatórias existam
            data.setdefault("tasks", [])
            data.setdefault("sessions", [])
            return data
    except (json.JSONDecodeError, IOError):
        return {"tasks": [], "sessions": []}


def _save_data(data: dict) -> None:
    """Salva os dados no arquivo JSON com formatação legível."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ──────────────────────────────────────────────
#  CRUD de Tarefas
# ──────────────────────────────────────────────

def get_tasks() -> list[dict]:
    """Retorna a lista de todas as tarefas cadastradas."""
    return _load_data()["tasks"]


def add_task(name: str) -> dict:
    """
    Adiciona uma nova tarefa.

    Args:
        name: Nome da tarefa (não pode ser vazio ou duplicado).

    Returns:
        Dicionário da tarefa criada.

    Raises:
        ValueError: Se o nome for vazio ou já existir.
    """
    name = name.strip()
    if not name:
        raise ValueError("O nome da tarefa não pode ser vazio.")

    data = _load_data()

    # Verifica duplicidade (case-insensitive)
    if any(t["name"].lower() == name.lower() for t in data["tasks"]):
        raise ValueError(f"Já existe uma tarefa com o nome '{name}'.")

    task = {
        "id": _next_id(data["tasks"]),
        "name": name,
        "created_at": datetime.now().isoformat(),
    }
    data["tasks"].append(task)
    _save_data(data)
    return task


def remove_task(task_id: int) -> str:
    """
    Remove uma tarefa pelo ID.

    Args:
        task_id: ID da tarefa a ser removida.

    Returns:
        Nome da tarefa removida.

    Raises:
        ValueError: Se a tarefa não for encontrada.
    """
    data = _load_data()
    for i, task in enumerate(data["tasks"]):
        if task["id"] == task_id:
            removed = data["tasks"].pop(i)
            _save_data(data)
            return removed["name"]
    raise ValueError(f"Tarefa com ID {task_id} não encontrada.")


def get_task_by_id(task_id: int) -> Optional[dict]:
    """Retorna uma tarefa pelo ID, ou None se não existir."""
    data = _load_data()
    for task in data["tasks"]:
        if task["id"] == task_id:
            return task
    return None


# ──────────────────────────────────────────────
#  Sessões de Estudo
# ──────────────────────────────────────────────

def log_session(task_id: int, duration_seconds: int) -> dict:
    """
    Registra uma sessão de estudo concluída.

    Args:
        task_id: ID da tarefa estudada.
        duration_seconds: Duração em segundos da sessão.

    Returns:
        Dicionário da sessão registrada.

    Raises:
        ValueError: Se a tarefa não existir ou a duração for inválida.
    """
    if duration_seconds <= 0:
        raise ValueError("A duração deve ser positiva.")

    data = _load_data()
    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if task is None:
        raise ValueError(f"Tarefa com ID {task_id} não encontrada.")

    session = {
        "task_id": task_id,
        "task_name": task["name"],
        "duration_seconds": duration_seconds,
        "completed_at": datetime.now().isoformat(),
    }
    data["sessions"].append(session)
    _save_data(data)
    return session


# ──────────────────────────────────────────────
#  Métricas e Histórico
# ──────────────────────────────────────────────

def get_task_metrics() -> list[dict]:
    """
    Calcula o tempo total acumulado por tarefa.

    Returns:
        Lista de dicts com {task_id, task_name, total_seconds, total_formatted,
        session_count}.
    """
    data = _load_data()
    metrics: dict[int, dict] = {}

    # Inicializa todas as tarefas (inclusive sem sessões)
    for task in data["tasks"]:
        metrics[task["id"]] = {
            "task_id": task["id"],
            "task_name": task["name"],
            "total_seconds": 0,
            "session_count": 0,
        }

    # Acumula sessões
    for session in data["sessions"]:
        tid = session["task_id"]
        if tid in metrics:
            metrics[tid]["total_seconds"] += session["duration_seconds"]
            metrics[tid]["session_count"] += 1

    # Formata o tempo acumulado
    result = []
    for m in metrics.values():
        m["total_formatted"] = format_seconds(m["total_seconds"])
        result.append(m)

    # Ordena por tempo total (maior primeiro)
    result.sort(key=lambda x: x["total_seconds"], reverse=True)
    return result


def get_sessions(task_id: Optional[int] = None) -> list[dict]:
    """Retorna o histórico de sessões, opcionalmente filtrado por tarefa."""
    data = _load_data()
    sessions = data["sessions"]
    if task_id is not None:
        sessions = [s for s in sessions if s["task_id"] == task_id]
    return sessions


# ──────────────────────────────────────────────
#  Utilitários
# ──────────────────────────────────────────────

def _next_id(items: list[dict]) -> int:
    """Gera o próximo ID sequencial."""
    if not items:
        return 1
    return max(item["id"] for item in items) + 1


def format_seconds(total_seconds: int) -> str:
    """Converte segundos em formato legível 'Xh Ym Zs'."""
    if total_seconds <= 0:
        return "0m 0s"
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0 or hours > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    return " ".join(parts)
