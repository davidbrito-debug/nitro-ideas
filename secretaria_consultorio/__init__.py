"""
Secretária Eletrônica de Consultório
"""

from .models import Paciente, Consulta, HorarioAtendimento, ConfiguracaoConsultorio
from .database import Database
from .scheduler import Agendador
from .chatbot import Chatbot
from .cli import CLI

__version__ = "1.0.0"
__all__ = [
    'Paciente',
    'Consulta',
    'HorarioAtendimento',
    'ConfiguracaoConsultorio',
    'Database',
    'Agendador',
    'Chatbot',
    'CLI'
]
