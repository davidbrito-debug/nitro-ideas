"""
Sistema de agendamento de consultas
"""

from datetime import datetime, date, time, timedelta
from typing import List, Optional, Tuple

from models import Paciente, Consulta, HorarioAtendimento, StatusConsulta, DiaSemana
from database import Database


class Agendador:
    def __init__(self, db: Database):
        self.db = db

    def obter_horarios_disponiveis(self, data: date, duracao_minutos: int = 30) -> List[time]:
        """Retorna lista de horários disponíveis para uma data específica"""
        # Verificar se a data está no futuro
        if data < date.today():
            return []

        # Obter o dia da semana
        dia_semana = DiaSemana(data.weekday())

        # Buscar horário de atendimento para este dia
        horarios = self.db.buscar_horarios_atendimento()
        horario_dia = None
        for h in horarios:
            if h.dia_semana == dia_semana and h.ativo:
                horario_dia = h
                break

        if not horario_dia:
            return []  # Não há atendimento neste dia

        # Gerar todos os slots do dia
        slots_possiveis = self._gerar_slots(
            horario_dia.hora_inicio,
            horario_dia.hora_fim,
            horario_dia.intervalo_minutos
        )

        # Buscar consultas já agendadas para este dia
        consultas_do_dia = self.db.buscar_consultas_por_data(data)

        # Filtrar slots ocupados
        slots_disponiveis = []
        agora = datetime.now()

        for slot in slots_possiveis:
            slot_datetime = datetime.combine(data, slot)

            # Verificar se não está no passado
            if slot_datetime <= agora:
                continue

            # Verificar se não conflita com consultas existentes
            slot_ocupado = False
            for consulta in consultas_do_dia:
                if self._slots_conflitam(slot, duracao_minutos, consulta.hora, consulta.duracao_minutos):
                    slot_ocupado = True
                    break

            if not slot_ocupado:
                slots_disponiveis.append(slot)

        return slots_disponiveis

    def _gerar_slots(self, hora_inicio: time, hora_fim: time, intervalo_minutos: int) -> List[time]:
        """Gera lista de slots de horário entre início e fim"""
        slots = []
        atual = datetime.combine(date.today(), hora_inicio)
        fim = datetime.combine(date.today(), hora_fim)

        while atual < fim:
            slots.append(atual.time())
            atual += timedelta(minutes=intervalo_minutos)

        return slots

    def _slots_conflitam(self, slot1: time, duracao1: int, slot2: time, duracao2: int) -> bool:
        """Verifica se dois slots de horário conflitam"""
        inicio1 = datetime.combine(date.today(), slot1)
        fim1 = inicio1 + timedelta(minutes=duracao1)

        inicio2 = datetime.combine(date.today(), slot2)
        fim2 = inicio2 + timedelta(minutes=duracao2)

        # Conflito se um começa antes do outro terminar
        return not (fim1 <= inicio2 or fim2 <= inicio1)

    def agendar_consulta(
        self,
        paciente_id: int,
        data: date,
        hora: time,
        tipo: str = "consulta",
        duracao_minutos: int = 30,
        observacoes: str = ""
    ) -> Tuple[bool, str, Optional[Consulta]]:
        """
        Agenda uma consulta.
        Retorna (sucesso, mensagem, consulta)
        """
        # Verificar se o paciente existe
        paciente = self.db.buscar_paciente_por_id(paciente_id)
        if not paciente:
            return False, "Paciente não encontrado.", None

        # Verificar se a data não está no passado
        data_hora = datetime.combine(data, hora)
        if data_hora <= datetime.now():
            return False, "Não é possível agendar consultas no passado.", None

        # Verificar se o horário está disponível
        horarios_disponiveis = self.obter_horarios_disponiveis(data, duracao_minutos)
        if hora not in horarios_disponiveis:
            return False, f"Horário {hora.strftime('%H:%M')} não está disponível nesta data.", None

        # Criar a consulta
        consulta = Consulta(
            paciente_id=paciente_id,
            data=data,
            hora=hora,
            tipo=tipo,
            duracao_minutos=duracao_minutos,
            observacoes=observacoes,
            status=StatusConsulta.AGENDADA
        )

        consulta.id = self.db.salvar_consulta(consulta)

        return True, "Consulta agendada com sucesso!", consulta

    def reagendar_consulta(
        self,
        consulta_id: int,
        nova_data: date,
        nova_hora: time
    ) -> Tuple[bool, str, Optional[Consulta]]:
        """Reagenda uma consulta existente"""
        consulta = self.db.buscar_consulta_por_id(consulta_id)
        if not consulta:
            return False, "Consulta não encontrada.", None

        if consulta.status == StatusConsulta.CANCELADA:
            return False, "Não é possível reagendar uma consulta cancelada.", None

        if consulta.status == StatusConsulta.REALIZADA:
            return False, "Não é possível reagendar uma consulta já realizada.", None

        # Verificar disponibilidade
        horarios_disponiveis = self.obter_horarios_disponiveis(nova_data, consulta.duracao_minutos)
        if nova_hora not in horarios_disponiveis:
            return False, f"Horário {nova_hora.strftime('%H:%M')} não está disponível nesta data.", None

        # Atualizar a consulta
        consulta.data = nova_data
        consulta.hora = nova_hora
        self.db.salvar_consulta(consulta)

        return True, "Consulta reagendada com sucesso!", consulta

    def cancelar_consulta(self, consulta_id: int, motivo: str = "") -> Tuple[bool, str]:
        """Cancela uma consulta"""
        consulta = self.db.buscar_consulta_por_id(consulta_id)
        if not consulta:
            return False, "Consulta não encontrada."

        if consulta.status == StatusConsulta.CANCELADA:
            return False, "Esta consulta já está cancelada."

        if consulta.status == StatusConsulta.REALIZADA:
            return False, "Não é possível cancelar uma consulta já realizada."

        consulta.status = StatusConsulta.CANCELADA
        if motivo:
            consulta.observacoes += f"\nMotivo do cancelamento: {motivo}"
        self.db.salvar_consulta(consulta)

        return True, "Consulta cancelada com sucesso."

    def confirmar_consulta(self, consulta_id: int) -> Tuple[bool, str]:
        """Confirma uma consulta"""
        consulta = self.db.buscar_consulta_por_id(consulta_id)
        if not consulta:
            return False, "Consulta não encontrada."

        if consulta.status != StatusConsulta.AGENDADA:
            return False, f"Consulta não pode ser confirmada (status atual: {consulta.status.value})."

        consulta.status = StatusConsulta.CONFIRMADA
        self.db.salvar_consulta(consulta)

        return True, "Consulta confirmada com sucesso."

    def obter_proximos_dias_disponiveis(self, quantidade: int = 7, duracao_minutos: int = 30) -> List[date]:
        """Retorna os próximos dias com horários disponíveis"""
        dias_disponiveis = []
        data_atual = date.today()

        dias_verificados = 0
        while len(dias_disponiveis) < quantidade and dias_verificados < 60:
            data_verificar = data_atual + timedelta(days=dias_verificados)
            horarios = self.obter_horarios_disponiveis(data_verificar, duracao_minutos)
            if horarios:
                dias_disponiveis.append(data_verificar)
            dias_verificados += 1

        return dias_disponiveis

    def obter_agenda_do_dia(self, data: date) -> List[dict]:
        """Retorna a agenda completa de um dia"""
        consultas = self.db.buscar_consultas_por_data(data)
        agenda = []

        for consulta in consultas:
            paciente = self.db.buscar_paciente_por_id(consulta.paciente_id)
            agenda.append({
                'consulta': consulta,
                'paciente': paciente,
                'horario': consulta.hora.strftime('%H:%M'),
                'status': consulta.status.value
            })

        return sorted(agenda, key=lambda x: x['consulta'].hora)

    def verificar_conflitos(self, paciente_id: int, data: date) -> Optional[Consulta]:
        """Verifica se o paciente já tem consulta neste dia"""
        consultas = self.db.buscar_consultas_por_data(data)
        for consulta in consultas:
            if consulta.paciente_id == paciente_id and consulta.status != StatusConsulta.CANCELADA:
                return consulta
        return None
