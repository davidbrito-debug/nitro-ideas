"""
Chatbot conversacional para atendimento de pacientes
"""

import re
from datetime import datetime, date, time, timedelta
from typing import Optional, Tuple, List, Dict, Any
from enum import Enum

from models import Paciente, Consulta, StatusConsulta
from database import Database
from scheduler import Agendador


class EstadoConversa(Enum):
    INICIO = "inicio"
    MENU_PRINCIPAL = "menu_principal"
    AGUARDANDO_NOME = "aguardando_nome"
    AGUARDANDO_TELEFONE = "aguardando_telefone"
    AGUARDANDO_EMAIL = "aguardando_email"
    ESCOLHENDO_DATA = "escolhendo_data"
    ESCOLHENDO_HORARIO = "escolhendo_horario"
    CONFIRMANDO_AGENDAMENTO = "confirmando_agendamento"
    BUSCANDO_CONSULTA = "buscando_consulta"
    CONFIRMANDO_CANCELAMENTO = "confirmando_cancelamento"
    AGUARDANDO_CPF = "aguardando_cpf"


class Chatbot:
    def __init__(self, db: Database):
        self.db = db
        self.agendador = Agendador(db)
        self.config = db.carregar_configuracao()
        self.sessoes: Dict[str, Dict[str, Any]] = {}

    def _obter_sessao(self, session_id: str) -> Dict[str, Any]:
        """Obtém ou cria uma sessão para o usuário"""
        if session_id not in self.sessoes:
            self.sessoes[session_id] = {
                'estado': EstadoConversa.INICIO,
                'paciente': None,
                'dados_temp': {},
                'ultima_interacao': datetime.now()
            }
        return self.sessoes[session_id]

    def processar_mensagem(self, session_id: str, mensagem: str) -> str:
        """Processa uma mensagem do usuário e retorna a resposta"""
        sessao = self._obter_sessao(session_id)
        sessao['ultima_interacao'] = datetime.now()
        mensagem = mensagem.strip()

        # Comandos globais
        if mensagem.lower() in ['sair', 'cancelar', 'voltar', 'menu']:
            sessao['estado'] = EstadoConversa.MENU_PRINCIPAL
            sessao['dados_temp'] = {}
            return self._menu_principal()

        if mensagem.lower() in ['ajuda', 'help', '?']:
            return self._ajuda()

        # Processar baseado no estado atual
        estado = sessao['estado']

        if estado == EstadoConversa.INICIO:
            return self._iniciar_conversa(sessao)

        elif estado == EstadoConversa.MENU_PRINCIPAL:
            return self._processar_menu_principal(sessao, mensagem)

        elif estado == EstadoConversa.AGUARDANDO_NOME:
            return self._processar_nome(sessao, mensagem)

        elif estado == EstadoConversa.AGUARDANDO_TELEFONE:
            return self._processar_telefone(sessao, mensagem)

        elif estado == EstadoConversa.AGUARDANDO_CPF:
            return self._processar_cpf(sessao, mensagem)

        elif estado == EstadoConversa.ESCOLHENDO_DATA:
            return self._processar_escolha_data(sessao, mensagem)

        elif estado == EstadoConversa.ESCOLHENDO_HORARIO:
            return self._processar_escolha_horario(sessao, mensagem)

        elif estado == EstadoConversa.CONFIRMANDO_AGENDAMENTO:
            return self._processar_confirmacao_agendamento(sessao, mensagem)

        elif estado == EstadoConversa.BUSCANDO_CONSULTA:
            return self._processar_busca_consulta(sessao, mensagem)

        elif estado == EstadoConversa.CONFIRMANDO_CANCELAMENTO:
            return self._processar_confirmacao_cancelamento(sessao, mensagem)

        return self._menu_principal()

    def _iniciar_conversa(self, sessao: Dict) -> str:
        """Inicia a conversa com mensagem de boas-vindas"""
        sessao['estado'] = EstadoConversa.MENU_PRINCIPAL
        return f"""
{self.config.mensagem_boas_vindas}

Bem-vindo(a) ao {self.config.nome_consultorio}!
{self.config.nome_profissional} - {self.config.especialidade}

{self._menu_principal()}
"""

    def _menu_principal(self) -> str:
        """Retorna o menu principal"""
        return """
Como posso ajudá-lo(a)?

1️⃣  Agendar uma consulta
2️⃣  Consultar minhas consultas
3️⃣  Cancelar uma consulta
4️⃣  Informações do consultório
5️⃣  Falar com atendente

Digite o número da opção desejada:
"""

    def _ajuda(self) -> str:
        """Retorna mensagem de ajuda"""
        return """
📋 AJUDA - Comandos disponíveis:

• Digite um NÚMERO para escolher uma opção
• Digite "menu" para voltar ao menu principal
• Digite "sair" para encerrar a conversa
• Digite "ajuda" para ver esta mensagem

Se precisar de atendimento humano, escolha a opção 5.
"""

    def _processar_menu_principal(self, sessao: Dict, mensagem: str) -> str:
        """Processa escolha do menu principal"""
        opcao = mensagem.strip()

        if opcao == '1' or 'agendar' in mensagem.lower():
            return self._iniciar_agendamento(sessao)

        elif opcao == '2' or 'consultar' in mensagem.lower() or 'minhas' in mensagem.lower():
            return self._iniciar_consulta_agendamentos(sessao)

        elif opcao == '3' or 'cancelar' in mensagem.lower():
            return self._iniciar_cancelamento(sessao)

        elif opcao == '4' or 'informaç' in mensagem.lower():
            return self._informacoes_consultorio()

        elif opcao == '5' or 'atendente' in mensagem.lower():
            return self._solicitar_atendente()

        else:
            return f"Desculpe, não entendi. Por favor, escolha uma opção de 1 a 5.\n{self._menu_principal()}"

    def _iniciar_agendamento(self, sessao: Dict) -> str:
        """Inicia processo de agendamento"""
        sessao['estado'] = EstadoConversa.AGUARDANDO_NOME
        sessao['dados_temp'] = {'acao': 'agendar'}
        return """
📅 AGENDAMENTO DE CONSULTA

Para agendar sua consulta, preciso de algumas informações.

Por favor, digite seu NOME COMPLETO:
"""

    def _processar_nome(self, sessao: Dict, mensagem: str) -> str:
        """Processa o nome do paciente"""
        nome = mensagem.strip()

        if len(nome) < 3:
            return "Por favor, digite seu nome completo:"

        # Verificar se já existe paciente com este nome
        pacientes = self.db.buscar_pacientes(nome)

        if pacientes:
            # Encontrou possíveis matches
            sessao['dados_temp']['pacientes_encontrados'] = pacientes
            sessao['dados_temp']['nome'] = nome
            sessao['estado'] = EstadoConversa.AGUARDANDO_CPF

            lista = "\n".join([f"• {p.nome} - Tel: {p.telefone}" for p in pacientes[:5]])
            return f"""
Encontrei alguns cadastros similares:

{lista}

Para confirmar sua identidade, por favor digite seu CPF (apenas números):
(Se você é um novo paciente, digite "novo")
"""

        sessao['dados_temp']['nome'] = nome
        sessao['estado'] = EstadoConversa.AGUARDANDO_TELEFONE
        return f"""
Olá, {nome.split()[0]}! Prazer em conhecê-lo(a)!

Para seu cadastro, por favor informe seu TELEFONE (com DDD):
"""

    def _processar_cpf(self, sessao: Dict, mensagem: str) -> str:
        """Processa o CPF para identificação"""
        cpf = re.sub(r'\D', '', mensagem.strip())

        if mensagem.lower() == 'novo':
            sessao['estado'] = EstadoConversa.AGUARDANDO_TELEFONE
            return f"""
Sem problemas! Vamos fazer seu cadastro.

Por favor, informe seu TELEFONE (com DDD):
"""

        if len(cpf) < 11:
            return "CPF inválido. Por favor, digite os 11 números do seu CPF:"

        # Buscar paciente pelo CPF
        pacientes = self.db.buscar_pacientes(cpf)

        if pacientes:
            paciente = pacientes[0]
            sessao['paciente'] = paciente
            sessao['estado'] = EstadoConversa.ESCOLHENDO_DATA
            return self._mostrar_datas_disponiveis(sessao, paciente.nome.split()[0])

        # CPF não encontrado, criar novo cadastro
        sessao['dados_temp']['cpf'] = cpf
        sessao['estado'] = EstadoConversa.AGUARDANDO_TELEFONE
        return f"""
Não encontrei seu cadastro. Vamos criá-lo!

Por favor, informe seu TELEFONE (com DDD):
"""

    def _processar_telefone(self, sessao: Dict, mensagem: str) -> str:
        """Processa o telefone do paciente"""
        telefone = re.sub(r'\D', '', mensagem.strip())

        if len(telefone) < 10:
            return "Telefone inválido. Por favor, digite seu telefone com DDD (ex: 11999998888):"

        # Criar novo paciente
        paciente = Paciente(
            nome=sessao['dados_temp'].get('nome', ''),
            telefone=telefone,
            cpf=sessao['dados_temp'].get('cpf', '')
        )
        paciente.id = self.db.salvar_paciente(paciente)
        sessao['paciente'] = paciente

        sessao['estado'] = EstadoConversa.ESCOLHENDO_DATA
        return f"""
Cadastro realizado com sucesso!

{self._mostrar_datas_disponiveis(sessao, paciente.nome.split()[0])}
"""

    def _mostrar_datas_disponiveis(self, sessao: Dict, nome: str) -> str:
        """Mostra as datas disponíveis para agendamento"""
        dias = self.agendador.obter_proximos_dias_disponiveis(7)

        if not dias:
            sessao['estado'] = EstadoConversa.MENU_PRINCIPAL
            return """
Infelizmente não há horários disponíveis nos próximos dias.
Por favor, entre em contato por telefone para verificar disponibilidade.

""" + self._menu_principal()

        sessao['dados_temp']['datas_disponiveis'] = dias

        opcoes = []
        for i, d in enumerate(dias, 1):
            dia_semana = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo'][d.weekday()]
            opcoes.append(f"{i}️⃣  {dia_semana}, {d.strftime('%d/%m/%Y')}")

        return f"""
{nome}, escolha uma data para sua consulta:

{chr(10).join(opcoes)}

Digite o número da data desejada:
"""

    def _processar_escolha_data(self, sessao: Dict, mensagem: str) -> str:
        """Processa a escolha da data"""
        try:
            opcao = int(mensagem.strip())
            datas = sessao['dados_temp'].get('datas_disponiveis', [])

            if 1 <= opcao <= len(datas):
                data_escolhida = datas[opcao - 1]
                sessao['dados_temp']['data_escolhida'] = data_escolhida

                return self._mostrar_horarios_disponiveis(sessao, data_escolhida)
            else:
                return f"Opção inválida. Digite um número de 1 a {len(datas)}:"

        except ValueError:
            # Tentar interpretar como data
            try:
                data = datetime.strptime(mensagem.strip(), '%d/%m/%Y').date()
                if data >= date.today():
                    sessao['dados_temp']['data_escolhida'] = data
                    return self._mostrar_horarios_disponiveis(sessao, data)
            except:
                pass

            return "Por favor, digite o número da opção desejada:"

    def _mostrar_horarios_disponiveis(self, sessao: Dict, data: date) -> str:
        """Mostra os horários disponíveis para uma data"""
        horarios = self.agendador.obter_horarios_disponiveis(data)

        if not horarios:
            sessao['estado'] = EstadoConversa.ESCOLHENDO_DATA
            return f"""
Não há horários disponíveis para {data.strftime('%d/%m/%Y')}.
Por favor, escolha outra data.

{self._mostrar_datas_disponiveis(sessao, sessao['paciente'].nome.split()[0] if sessao['paciente'] else 'você')}
"""

        sessao['dados_temp']['horarios_disponiveis'] = horarios
        sessao['estado'] = EstadoConversa.ESCOLHENDO_HORARIO

        # Agrupar por período
        manha = [h for h in horarios if h.hour < 12]
        tarde = [h for h in horarios if 12 <= h.hour < 18]

        texto = f"📅 {data.strftime('%d/%m/%Y')} - Horários disponíveis:\n\n"

        if manha:
            texto += "🌅 Manhã: " + " | ".join([h.strftime('%H:%M') for h in manha]) + "\n"
        if tarde:
            texto += "🌆 Tarde: " + " | ".join([h.strftime('%H:%M') for h in tarde]) + "\n"

        texto += "\nDigite o horário desejado (ex: 14:30):"

        return texto

    def _processar_escolha_horario(self, sessao: Dict, mensagem: str) -> str:
        """Processa a escolha do horário"""
        try:
            # Tentar parsear o horário
            hora_str = mensagem.strip().replace('.', ':')
            if ':' not in hora_str:
                if len(hora_str) <= 2:
                    hora_str += ':00'
                elif len(hora_str) == 4:
                    hora_str = hora_str[:2] + ':' + hora_str[2:]

            partes = hora_str.split(':')
            hora = time(int(partes[0]), int(partes[1]))

            horarios_disponiveis = sessao['dados_temp'].get('horarios_disponiveis', [])

            if hora in horarios_disponiveis:
                sessao['dados_temp']['hora_escolhida'] = hora
                sessao['estado'] = EstadoConversa.CONFIRMANDO_AGENDAMENTO

                data = sessao['dados_temp']['data_escolhida']
                paciente = sessao['paciente']
                dia_semana = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo'][data.weekday()]

                return f"""
📋 CONFIRMAÇÃO DE AGENDAMENTO

👤 Paciente: {paciente.nome}
📅 Data: {dia_semana}, {data.strftime('%d/%m/%Y')}
⏰ Horário: {hora.strftime('%H:%M')}
🏥 Local: {self.config.endereco}

Confirma o agendamento? (sim/não)
"""
            else:
                horarios_str = ", ".join([h.strftime('%H:%M') for h in horarios_disponiveis])
                return f"Horário não disponível. Escolha entre: {horarios_str}"

        except (ValueError, IndexError):
            return "Formato inválido. Digite o horário no formato HH:MM (ex: 14:30):"

    def _processar_confirmacao_agendamento(self, sessao: Dict, mensagem: str) -> str:
        """Processa confirmação do agendamento"""
        resposta = mensagem.lower().strip()

        if resposta in ['sim', 's', 'yes', 'y', 'confirmar', 'ok']:
            paciente = sessao['paciente']
            data = sessao['dados_temp']['data_escolhida']
            hora = sessao['dados_temp']['hora_escolhida']

            sucesso, msg, consulta = self.agendador.agendar_consulta(
                paciente_id=paciente.id,
                data=data,
                hora=hora
            )

            sessao['estado'] = EstadoConversa.MENU_PRINCIPAL
            sessao['dados_temp'] = {}

            if sucesso:
                dia_semana = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo'][data.weekday()]
                return f"""
✅ CONSULTA AGENDADA COM SUCESSO!

{self.config.mensagem_confirmacao}

📋 Detalhes:
• Código: #{consulta.id}
• Data: {dia_semana}, {data.strftime('%d/%m/%Y')}
• Horário: {hora.strftime('%H:%M')}
• Endereço: {self.config.endereco}

⚠️ Lembre-se de chegar com 15 minutos de antecedência.

{self._menu_principal()}
"""
            else:
                return f"""
❌ Não foi possível agendar: {msg}

{self._menu_principal()}
"""

        elif resposta in ['não', 'nao', 'n', 'no', 'cancelar']:
            sessao['estado'] = EstadoConversa.ESCOLHENDO_DATA
            return f"""
Agendamento cancelado.

Deseja escolher outra data/horário?

{self._mostrar_datas_disponiveis(sessao, sessao['paciente'].nome.split()[0])}
"""

        else:
            return "Por favor, responda 'sim' para confirmar ou 'não' para cancelar:"

    def _iniciar_consulta_agendamentos(self, sessao: Dict) -> str:
        """Inicia consulta de agendamentos"""
        sessao['estado'] = EstadoConversa.BUSCANDO_CONSULTA
        sessao['dados_temp'] = {'acao': 'consultar'}
        return """
📋 CONSULTAR AGENDAMENTOS

Para buscar suas consultas, informe seu CPF ou telefone:
"""

    def _processar_busca_consulta(self, sessao: Dict, mensagem: str) -> str:
        """Processa busca de consultas"""
        termo = re.sub(r'\D', '', mensagem.strip())

        if len(termo) < 10:
            return "Por favor, informe seu CPF (11 dígitos) ou telefone (10-11 dígitos):"

        pacientes = self.db.buscar_pacientes(termo)

        if not pacientes:
            sessao['estado'] = EstadoConversa.MENU_PRINCIPAL
            return f"""
Não encontrei nenhum cadastro com esse dado.

{self._menu_principal()}
"""

        paciente = pacientes[0]
        consultas = self.db.buscar_consultas_por_paciente(paciente.id)
        proximas = [c for c in consultas if c.data >= date.today() and c.status in [StatusConsulta.AGENDADA, StatusConsulta.CONFIRMADA]]

        if not proximas:
            sessao['estado'] = EstadoConversa.MENU_PRINCIPAL
            return f"""
Olá, {paciente.nome.split()[0]}!

Você não possui consultas agendadas no momento.

{self._menu_principal()}
"""

        sessao['estado'] = EstadoConversa.MENU_PRINCIPAL
        sessao['paciente'] = paciente

        lista_consultas = []
        for c in proximas[:5]:
            dia_semana = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'][c.data.weekday()]
            lista_consultas.append(f"• #{c.id} - {dia_semana} {c.data.strftime('%d/%m')} às {c.hora.strftime('%H:%M')} ({c.status.value})")

        return f"""
👤 {paciente.nome}

📅 Suas próximas consultas:

{chr(10).join(lista_consultas)}

{self._menu_principal()}
"""

    def _iniciar_cancelamento(self, sessao: Dict) -> str:
        """Inicia processo de cancelamento"""
        sessao['estado'] = EstadoConversa.BUSCANDO_CONSULTA
        sessao['dados_temp'] = {'acao': 'cancelar'}
        return """
❌ CANCELAR CONSULTA

Para cancelar uma consulta, informe seu CPF ou telefone:
"""

    def _processar_confirmacao_cancelamento(self, sessao: Dict, mensagem: str) -> str:
        """Processa confirmação de cancelamento"""
        resposta = mensagem.lower().strip()

        if resposta in ['sim', 's', 'yes', 'y', 'confirmar']:
            consulta_id = sessao['dados_temp'].get('consulta_cancelar')
            sucesso, msg = self.agendador.cancelar_consulta(consulta_id)

            sessao['estado'] = EstadoConversa.MENU_PRINCIPAL
            sessao['dados_temp'] = {}

            if sucesso:
                return f"""
✅ Consulta cancelada com sucesso!

{self._menu_principal()}
"""
            else:
                return f"""
❌ Erro ao cancelar: {msg}

{self._menu_principal()}
"""

        elif resposta in ['não', 'nao', 'n', 'no']:
            sessao['estado'] = EstadoConversa.MENU_PRINCIPAL
            sessao['dados_temp'] = {}
            return f"""
Cancelamento não realizado.

{self._menu_principal()}
"""

        return "Por favor, responda 'sim' para confirmar ou 'não' para manter a consulta:"

    def _informacoes_consultorio(self) -> str:
        """Retorna informações do consultório"""
        horarios = self.db.buscar_horarios_atendimento()
        horarios_ativos = [h for h in horarios if h.ativo]

        dias_func = []
        for h in horarios_ativos:
            dia = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo'][h.dia_semana.value]
            dias_func.append(f"• {dia}: {h.hora_inicio.strftime('%H:%M')} às {h.hora_fim.strftime('%H:%M')}")

        return f"""
🏥 INFORMAÇÕES DO CONSULTÓRIO

📍 {self.config.nome_consultorio}
👨‍⚕️ {self.config.nome_profissional}
🩺 {self.config.especialidade}

📞 Telefone: {self.config.telefone}
📍 Endereço: {self.config.endereco}

⏰ Horários de Atendimento:
{chr(10).join(dias_func) if dias_func else "Horários não configurados"}

{self._menu_principal()}
"""

    def _solicitar_atendente(self) -> str:
        """Informa sobre atendimento humano"""
        return f"""
📞 ATENDIMENTO HUMANO

Para falar com nossa equipe, utilize um dos canais:

📞 Telefone: {self.config.telefone}
⏰ Horário: Segunda a Sexta, das 8h às 18h

Sua solicitação foi registrada e entraremos em contato em breve.

{self._menu_principal()}
"""
