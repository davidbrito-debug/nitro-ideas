"""
Modelos de dados para a Secretária Eletrônica de Consultório
"""

from dataclasses import dataclass, field
from datetime import datetime, date, time
from typing import Optional, List
from enum import Enum


class StatusConsulta(Enum):
    AGENDADA = "agendada"
    CONFIRMADA = "confirmada"
    CANCELADA = "cancelada"
    REALIZADA = "realizada"
    NAO_COMPARECEU = "nao_compareceu"


class DiaSemana(Enum):
    SEGUNDA = 0
    TERCA = 1
    QUARTA = 2
    QUINTA = 3
    SEXTA = 4
    SABADO = 5
    DOMINGO = 6


@dataclass
class Paciente:
    id: Optional[int] = None
    nome: str = ""
    telefone: str = ""
    email: str = ""
    data_nascimento: Optional[date] = None
    cpf: str = ""
    endereco: str = ""
    observacoes: str = ""
    data_cadastro: datetime = field(default_factory=datetime.now)

    def idade(self) -> Optional[int]:
        if self.data_nascimento:
            hoje = date.today()
            return hoje.year - self.data_nascimento.year - (
                (hoje.month, hoje.day) < (self.data_nascimento.month, self.data_nascimento.day)
            )
        return None


@dataclass
class Consulta:
    id: Optional[int] = None
    paciente_id: int = 0
    data: date = field(default_factory=date.today)
    hora: time = field(default_factory=lambda: time(8, 0))
    duracao_minutos: int = 30
    tipo: str = "consulta"
    observacoes: str = ""
    status: StatusConsulta = StatusConsulta.AGENDADA
    data_criacao: datetime = field(default_factory=datetime.now)

    @property
    def data_hora(self) -> datetime:
        return datetime.combine(self.data, self.hora)

    def esta_no_passado(self) -> bool:
        return self.data_hora < datetime.now()


@dataclass
class HorarioAtendimento:
    id: Optional[int] = None
    dia_semana: DiaSemana = DiaSemana.SEGUNDA
    hora_inicio: time = field(default_factory=lambda: time(8, 0))
    hora_fim: time = field(default_factory=lambda: time(18, 0))
    intervalo_minutos: int = 30
    ativo: bool = True


@dataclass
class ConfiguracaoConsultorio:
    nome_consultorio: str = "Meu Consultório"
    nome_profissional: str = "Dr(a). Nome"
    especialidade: str = ""
    telefone: str = ""
    endereco: str = ""
    duracao_consulta_padrao: int = 30
    antecedencia_minima_horas: int = 2
    antecedencia_maxima_dias: int = 60
    mensagem_boas_vindas: str = "Olá! Sou a secretária eletrônica do consultório. Como posso ajudá-lo?"
    mensagem_confirmacao: str = "Sua consulta foi agendada com sucesso!"
