"""
Modelos de dados para o programa de pesquisa de prontuário.
"""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional


class Criterio(Enum):
    """Critério atendido pelo paciente."""
    NOTA_FISCAL = "NF/Nota Fiscal"
    BIOIMPEDANCIA = "Bioimpedanciometria"
    AMBOS = "NF/Nota Fiscal + Bioimpedanciometria"


@dataclass
class PacienteRegistro:
    """Registro de um paciente que atendeu aos critérios de busca."""
    nome_completo: str
    cpf: str
    endereco: str
    data_atendimento: date
    criterio: Criterio
    detalhes: str = ""

    def to_dict(self) -> dict:
        return {
            "Nome Completo": self.nome_completo,
            "CPF": self.cpf,
            "Endereço": self.endereco,
            "Data do Atendimento": self.data_atendimento.strftime("%d/%m/%Y"),
            "Critério Atendido": self.criterio.value,
            "Detalhes": self.detalhes,
        }


@dataclass
class ResultadoPesquisa:
    """Resultado completo de uma pesquisa por data."""
    data_pesquisa: date
    total_pacientes_agenda: int = 0
    pacientes_encontrados: list[PacienteRegistro] = field(default_factory=list)
    erros: list[str] = field(default_factory=list)

    @property
    def total_encontrados(self) -> int:
        return len(self.pacientes_encontrados)

    def resumo(self) -> str:
        linhas = [
            f"Data: {self.data_pesquisa.strftime('%d/%m/%Y')}",
            f"Total na agenda: {self.total_pacientes_agenda}",
            f"Pacientes com critérios: {self.total_encontrados}",
        ]
        if self.erros:
            linhas.append(f"Erros encontrados: {len(self.erros)}")
        return "\n".join(linhas)
