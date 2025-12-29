"""
Módulo de persistência de dados usando SQLite
"""

import sqlite3
import json
from datetime import datetime, date, time
from pathlib import Path
from typing import List, Optional
from contextlib import contextmanager

from models import (
    Paciente, Consulta, HorarioAtendimento, ConfiguracaoConsultorio,
    StatusConsulta, DiaSemana
)


class Database:
    def __init__(self, db_path: str = "consultorio.db"):
        self.db_path = Path(db_path)
        self._criar_tabelas()

    @contextmanager
    def _conexao(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _criar_tabelas(self):
        with self._conexao() as conn:
            cursor = conn.cursor()

            # Tabela de pacientes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pacientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    telefone TEXT,
                    email TEXT,
                    data_nascimento TEXT,
                    cpf TEXT,
                    endereco TEXT,
                    observacoes TEXT,
                    data_cadastro TEXT
                )
            """)

            # Tabela de consultas
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS consultas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    paciente_id INTEGER NOT NULL,
                    data TEXT NOT NULL,
                    hora TEXT NOT NULL,
                    duracao_minutos INTEGER DEFAULT 30,
                    tipo TEXT DEFAULT 'consulta',
                    observacoes TEXT,
                    status TEXT DEFAULT 'agendada',
                    data_criacao TEXT,
                    FOREIGN KEY (paciente_id) REFERENCES pacientes (id)
                )
            """)

            # Tabela de horários de atendimento
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS horarios_atendimento (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dia_semana INTEGER NOT NULL,
                    hora_inicio TEXT NOT NULL,
                    hora_fim TEXT NOT NULL,
                    intervalo_minutos INTEGER DEFAULT 30,
                    ativo INTEGER DEFAULT 1
                )
            """)

            # Tabela de configurações
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS configuracoes (
                    chave TEXT PRIMARY KEY,
                    valor TEXT
                )
            """)

            # Inserir horários padrão se não existirem
            cursor.execute("SELECT COUNT(*) FROM horarios_atendimento")
            if cursor.fetchone()[0] == 0:
                for dia in range(5):  # Segunda a Sexta
                    cursor.execute("""
                        INSERT INTO horarios_atendimento
                        (dia_semana, hora_inicio, hora_fim, intervalo_minutos, ativo)
                        VALUES (?, ?, ?, ?, ?)
                    """, (dia, "08:00", "18:00", 30, 1))

    # ========== PACIENTES ==========

    def salvar_paciente(self, paciente: Paciente) -> int:
        with self._conexao() as conn:
            cursor = conn.cursor()

            data_nasc = paciente.data_nascimento.isoformat() if paciente.data_nascimento else None
            data_cad = paciente.data_cadastro.isoformat() if paciente.data_cadastro else datetime.now().isoformat()

            if paciente.id:
                cursor.execute("""
                    UPDATE pacientes SET
                        nome=?, telefone=?, email=?, data_nascimento=?,
                        cpf=?, endereco=?, observacoes=?
                    WHERE id=?
                """, (paciente.nome, paciente.telefone, paciente.email, data_nasc,
                      paciente.cpf, paciente.endereco, paciente.observacoes, paciente.id))
                return paciente.id
            else:
                cursor.execute("""
                    INSERT INTO pacientes
                    (nome, telefone, email, data_nascimento, cpf, endereco, observacoes, data_cadastro)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (paciente.nome, paciente.telefone, paciente.email, data_nasc,
                      paciente.cpf, paciente.endereco, paciente.observacoes, data_cad))
                return cursor.lastrowid

    def buscar_paciente_por_id(self, id: int) -> Optional[Paciente]:
        with self._conexao() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pacientes WHERE id = ?", (id,))
            row = cursor.fetchone()
            if row:
                return self._row_para_paciente(row)
        return None

    def buscar_pacientes(self, termo: str = "") -> List[Paciente]:
        with self._conexao() as conn:
            cursor = conn.cursor()
            if termo:
                cursor.execute("""
                    SELECT * FROM pacientes
                    WHERE nome LIKE ? OR telefone LIKE ? OR cpf LIKE ?
                    ORDER BY nome
                """, (f"%{termo}%", f"%{termo}%", f"%{termo}%"))
            else:
                cursor.execute("SELECT * FROM pacientes ORDER BY nome")
            return [self._row_para_paciente(row) for row in cursor.fetchall()]

    def excluir_paciente(self, id: int) -> bool:
        with self._conexao() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM pacientes WHERE id = ?", (id,))
            return cursor.rowcount > 0

    def _row_para_paciente(self, row) -> Paciente:
        data_nasc = None
        if row['data_nascimento']:
            data_nasc = date.fromisoformat(row['data_nascimento'])

        data_cad = datetime.now()
        if row['data_cadastro']:
            data_cad = datetime.fromisoformat(row['data_cadastro'])

        return Paciente(
            id=row['id'],
            nome=row['nome'],
            telefone=row['telefone'] or "",
            email=row['email'] or "",
            data_nascimento=data_nasc,
            cpf=row['cpf'] or "",
            endereco=row['endereco'] or "",
            observacoes=row['observacoes'] or "",
            data_cadastro=data_cad
        )

    # ========== CONSULTAS ==========

    def salvar_consulta(self, consulta: Consulta) -> int:
        with self._conexao() as conn:
            cursor = conn.cursor()

            data_str = consulta.data.isoformat()
            hora_str = consulta.hora.strftime("%H:%M")
            data_criacao = consulta.data_criacao.isoformat() if consulta.data_criacao else datetime.now().isoformat()

            if consulta.id:
                cursor.execute("""
                    UPDATE consultas SET
                        paciente_id=?, data=?, hora=?, duracao_minutos=?,
                        tipo=?, observacoes=?, status=?
                    WHERE id=?
                """, (consulta.paciente_id, data_str, hora_str, consulta.duracao_minutos,
                      consulta.tipo, consulta.observacoes, consulta.status.value, consulta.id))
                return consulta.id
            else:
                cursor.execute("""
                    INSERT INTO consultas
                    (paciente_id, data, hora, duracao_minutos, tipo, observacoes, status, data_criacao)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (consulta.paciente_id, data_str, hora_str, consulta.duracao_minutos,
                      consulta.tipo, consulta.observacoes, consulta.status.value, data_criacao))
                return cursor.lastrowid

    def buscar_consulta_por_id(self, id: int) -> Optional[Consulta]:
        with self._conexao() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM consultas WHERE id = ?", (id,))
            row = cursor.fetchone()
            if row:
                return self._row_para_consulta(row)
        return None

    def buscar_consultas_por_data(self, data: date) -> List[Consulta]:
        with self._conexao() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM consultas
                WHERE data = ? AND status NOT IN ('cancelada')
                ORDER BY hora
            """, (data.isoformat(),))
            return [self._row_para_consulta(row) for row in cursor.fetchall()]

    def buscar_consultas_por_paciente(self, paciente_id: int) -> List[Consulta]:
        with self._conexao() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM consultas
                WHERE paciente_id = ?
                ORDER BY data DESC, hora DESC
            """, (paciente_id,))
            return [self._row_para_consulta(row) for row in cursor.fetchall()]

    def buscar_proximas_consultas(self, limite: int = 10) -> List[Consulta]:
        with self._conexao() as conn:
            cursor = conn.cursor()
            hoje = date.today().isoformat()
            cursor.execute("""
                SELECT * FROM consultas
                WHERE data >= ? AND status IN ('agendada', 'confirmada')
                ORDER BY data, hora
                LIMIT ?
            """, (hoje, limite))
            return [self._row_para_consulta(row) for row in cursor.fetchall()]

    def cancelar_consulta(self, id: int) -> bool:
        with self._conexao() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE consultas SET status = 'cancelada' WHERE id = ?
            """, (id,))
            return cursor.rowcount > 0

    def _row_para_consulta(self, row) -> Consulta:
        hora_parts = row['hora'].split(':')
        return Consulta(
            id=row['id'],
            paciente_id=row['paciente_id'],
            data=date.fromisoformat(row['data']),
            hora=time(int(hora_parts[0]), int(hora_parts[1])),
            duracao_minutos=row['duracao_minutos'],
            tipo=row['tipo'] or "consulta",
            observacoes=row['observacoes'] or "",
            status=StatusConsulta(row['status']),
            data_criacao=datetime.fromisoformat(row['data_criacao']) if row['data_criacao'] else datetime.now()
        )

    # ========== HORÁRIOS ==========

    def buscar_horarios_atendimento(self) -> List[HorarioAtendimento]:
        with self._conexao() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM horarios_atendimento ORDER BY dia_semana")
            return [self._row_para_horario(row) for row in cursor.fetchall()]

    def salvar_horario_atendimento(self, horario: HorarioAtendimento) -> int:
        with self._conexao() as conn:
            cursor = conn.cursor()

            hora_inicio = horario.hora_inicio.strftime("%H:%M")
            hora_fim = horario.hora_fim.strftime("%H:%M")

            if horario.id:
                cursor.execute("""
                    UPDATE horarios_atendimento SET
                        dia_semana=?, hora_inicio=?, hora_fim=?,
                        intervalo_minutos=?, ativo=?
                    WHERE id=?
                """, (horario.dia_semana.value, hora_inicio, hora_fim,
                      horario.intervalo_minutos, 1 if horario.ativo else 0, horario.id))
                return horario.id
            else:
                cursor.execute("""
                    INSERT INTO horarios_atendimento
                    (dia_semana, hora_inicio, hora_fim, intervalo_minutos, ativo)
                    VALUES (?, ?, ?, ?, ?)
                """, (horario.dia_semana.value, hora_inicio, hora_fim,
                      horario.intervalo_minutos, 1 if horario.ativo else 0))
                return cursor.lastrowid

    def _row_para_horario(self, row) -> HorarioAtendimento:
        inicio_parts = row['hora_inicio'].split(':')
        fim_parts = row['hora_fim'].split(':')
        return HorarioAtendimento(
            id=row['id'],
            dia_semana=DiaSemana(row['dia_semana']),
            hora_inicio=time(int(inicio_parts[0]), int(inicio_parts[1])),
            hora_fim=time(int(fim_parts[0]), int(fim_parts[1])),
            intervalo_minutos=row['intervalo_minutos'],
            ativo=bool(row['ativo'])
        )

    # ========== CONFIGURAÇÕES ==========

    def salvar_configuracao(self, config: ConfiguracaoConsultorio):
        with self._conexao() as conn:
            cursor = conn.cursor()
            configs = {
                'nome_consultorio': config.nome_consultorio,
                'nome_profissional': config.nome_profissional,
                'especialidade': config.especialidade,
                'telefone': config.telefone,
                'endereco': config.endereco,
                'duracao_consulta_padrao': str(config.duracao_consulta_padrao),
                'antecedencia_minima_horas': str(config.antecedencia_minima_horas),
                'antecedencia_maxima_dias': str(config.antecedencia_maxima_dias),
                'mensagem_boas_vindas': config.mensagem_boas_vindas,
                'mensagem_confirmacao': config.mensagem_confirmacao,
            }
            for chave, valor in configs.items():
                cursor.execute("""
                    INSERT OR REPLACE INTO configuracoes (chave, valor) VALUES (?, ?)
                """, (chave, valor))

    def carregar_configuracao(self) -> ConfiguracaoConsultorio:
        config = ConfiguracaoConsultorio()
        with self._conexao() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT chave, valor FROM configuracoes")
            for row in cursor.fetchall():
                chave, valor = row['chave'], row['valor']
                if hasattr(config, chave):
                    if chave in ['duracao_consulta_padrao', 'antecedencia_minima_horas', 'antecedencia_maxima_dias']:
                        setattr(config, chave, int(valor))
                    else:
                        setattr(config, chave, valor)
        return config
