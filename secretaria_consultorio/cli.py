"""
Interface de Linha de Comando para a Secretária Eletrônica
"""

import os
import sys
from datetime import datetime, date, time
from typing import Optional

from models import (
    Paciente, Consulta, HorarioAtendimento, ConfiguracaoConsultorio,
    StatusConsulta, DiaSemana
)
from database import Database
from scheduler import Agendador
from chatbot import Chatbot


class CLI:
    def __init__(self, db_path: str = "consultorio.db"):
        self.db = Database(db_path)
        self.agendador = Agendador(self.db)
        self.chatbot = Chatbot(self.db)
        self.config = self.db.carregar_configuracao()

    def limpar_tela(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def cabecalho(self, titulo: str):
        print("\n" + "=" * 60)
        print(f"  {titulo}")
        print("=" * 60 + "\n")

    def pausar(self):
        input("\nPressione ENTER para continuar...")

    def menu_principal(self):
        while True:
            self.limpar_tela()
            self.cabecalho(f"SECRETÁRIA ELETRÔNICA - {self.config.nome_consultorio}")

            print("  1. Modo Atendimento (Chatbot)")
            print("  2. Gerenciar Pacientes")
            print("  3. Gerenciar Consultas")
            print("  4. Ver Agenda do Dia")
            print("  5. Configurações")
            print("  0. Sair")
            print()

            opcao = input("Escolha uma opção: ").strip()

            if opcao == '1':
                self.modo_chatbot()
            elif opcao == '2':
                self.menu_pacientes()
            elif opcao == '3':
                self.menu_consultas()
            elif opcao == '4':
                self.ver_agenda_dia()
            elif opcao == '5':
                self.menu_configuracoes()
            elif opcao == '0':
                print("\nAté logo!")
                sys.exit(0)

    def modo_chatbot(self):
        """Modo de atendimento via chatbot"""
        self.limpar_tela()
        self.cabecalho("MODO ATENDIMENTO - CHATBOT")
        print("Digite 'sair' para voltar ao menu principal\n")
        print("-" * 50)

        session_id = f"cli_{datetime.now().timestamp()}"

        # Mensagem inicial
        resposta = self.chatbot.processar_mensagem(session_id, "")
        print(resposta)

        while True:
            try:
                mensagem = input("\nVocê: ").strip()

                if mensagem.lower() == 'sair':
                    break

                resposta = self.chatbot.processar_mensagem(session_id, mensagem)
                print(f"\nSecretária: {resposta}")

            except KeyboardInterrupt:
                break

    # ========== PACIENTES ==========

    def menu_pacientes(self):
        while True:
            self.limpar_tela()
            self.cabecalho("GERENCIAR PACIENTES")

            print("  1. Listar Pacientes")
            print("  2. Buscar Paciente")
            print("  3. Cadastrar Novo Paciente")
            print("  4. Editar Paciente")
            print("  5. Excluir Paciente")
            print("  0. Voltar")
            print()

            opcao = input("Escolha uma opção: ").strip()

            if opcao == '1':
                self.listar_pacientes()
            elif opcao == '2':
                self.buscar_paciente()
            elif opcao == '3':
                self.cadastrar_paciente()
            elif opcao == '4':
                self.editar_paciente()
            elif opcao == '5':
                self.excluir_paciente()
            elif opcao == '0':
                break

    def listar_pacientes(self):
        self.limpar_tela()
        self.cabecalho("LISTA DE PACIENTES")

        pacientes = self.db.buscar_pacientes()

        if not pacientes:
            print("Nenhum paciente cadastrado.")
        else:
            print(f"{'ID':<5} {'Nome':<30} {'Telefone':<15} {'CPF':<15}")
            print("-" * 65)
            for p in pacientes:
                print(f"{p.id:<5} {p.nome:<30} {p.telefone:<15} {p.cpf:<15}")

        self.pausar()

    def buscar_paciente(self):
        self.limpar_tela()
        self.cabecalho("BUSCAR PACIENTE")

        termo = input("Digite nome, telefone ou CPF: ").strip()
        pacientes = self.db.buscar_pacientes(termo)

        if not pacientes:
            print("\nNenhum paciente encontrado.")
        else:
            print(f"\n{len(pacientes)} paciente(s) encontrado(s):\n")
            for p in pacientes:
                print(f"ID: {p.id}")
                print(f"Nome: {p.nome}")
                print(f"Telefone: {p.telefone}")
                print(f"CPF: {p.cpf}")
                print(f"Email: {p.email}")
                if p.data_nascimento:
                    print(f"Nascimento: {p.data_nascimento.strftime('%d/%m/%Y')} ({p.idade()} anos)")
                print("-" * 30)

        self.pausar()

    def cadastrar_paciente(self):
        self.limpar_tela()
        self.cabecalho("CADASTRAR PACIENTE")

        nome = input("Nome completo: ").strip()
        telefone = input("Telefone (com DDD): ").strip()
        cpf = input("CPF: ").strip()
        email = input("Email (opcional): ").strip()
        nascimento_str = input("Data de nascimento (DD/MM/AAAA, opcional): ").strip()

        data_nascimento = None
        if nascimento_str:
            try:
                data_nascimento = datetime.strptime(nascimento_str, "%d/%m/%Y").date()
            except ValueError:
                print("Data inválida, ignorando...")

        paciente = Paciente(
            nome=nome,
            telefone=telefone,
            cpf=cpf,
            email=email,
            data_nascimento=data_nascimento
        )

        paciente.id = self.db.salvar_paciente(paciente)
        print(f"\nPaciente cadastrado com sucesso! ID: {paciente.id}")
        self.pausar()

    def editar_paciente(self):
        self.limpar_tela()
        self.cabecalho("EDITAR PACIENTE")

        id_str = input("ID do paciente: ").strip()
        try:
            paciente = self.db.buscar_paciente_por_id(int(id_str))
        except ValueError:
            print("ID inválido.")
            self.pausar()
            return

        if not paciente:
            print("Paciente não encontrado.")
            self.pausar()
            return

        print(f"\nEditando: {paciente.nome}")
        print("(Deixe em branco para manter o valor atual)\n")

        nome = input(f"Nome [{paciente.nome}]: ").strip() or paciente.nome
        telefone = input(f"Telefone [{paciente.telefone}]: ").strip() or paciente.telefone
        cpf = input(f"CPF [{paciente.cpf}]: ").strip() or paciente.cpf
        email = input(f"Email [{paciente.email}]: ").strip() or paciente.email

        paciente.nome = nome
        paciente.telefone = telefone
        paciente.cpf = cpf
        paciente.email = email

        self.db.salvar_paciente(paciente)
        print("\nPaciente atualizado com sucesso!")
        self.pausar()

    def excluir_paciente(self):
        self.limpar_tela()
        self.cabecalho("EXCLUIR PACIENTE")

        id_str = input("ID do paciente: ").strip()
        try:
            paciente = self.db.buscar_paciente_por_id(int(id_str))
        except ValueError:
            print("ID inválido.")
            self.pausar()
            return

        if not paciente:
            print("Paciente não encontrado.")
            self.pausar()
            return

        print(f"\nPaciente: {paciente.nome}")
        confirma = input("Tem certeza que deseja excluir? (s/n): ").strip().lower()

        if confirma == 's':
            self.db.excluir_paciente(paciente.id)
            print("Paciente excluído com sucesso!")
        else:
            print("Operação cancelada.")

        self.pausar()

    # ========== CONSULTAS ==========

    def menu_consultas(self):
        while True:
            self.limpar_tela()
            self.cabecalho("GERENCIAR CONSULTAS")

            print("  1. Agendar Consulta")
            print("  2. Buscar Consultas de Paciente")
            print("  3. Próximas Consultas")
            print("  4. Cancelar Consulta")
            print("  5. Confirmar Consulta")
            print("  0. Voltar")
            print()

            opcao = input("Escolha uma opção: ").strip()

            if opcao == '1':
                self.agendar_consulta()
            elif opcao == '2':
                self.buscar_consultas_paciente()
            elif opcao == '3':
                self.proximas_consultas()
            elif opcao == '4':
                self.cancelar_consulta()
            elif opcao == '5':
                self.confirmar_consulta()
            elif opcao == '0':
                break

    def agendar_consulta(self):
        self.limpar_tela()
        self.cabecalho("AGENDAR CONSULTA")

        # Buscar paciente
        termo = input("Buscar paciente (nome, telefone ou CPF): ").strip()
        pacientes = self.db.buscar_pacientes(termo)

        if not pacientes:
            print("Nenhum paciente encontrado.")
            self.pausar()
            return

        print("\nPacientes encontrados:")
        for i, p in enumerate(pacientes, 1):
            print(f"  {i}. {p.nome} - {p.telefone}")

        try:
            escolha = int(input("\nEscolha o paciente (número): ").strip())
            paciente = pacientes[escolha - 1]
        except (ValueError, IndexError):
            print("Escolha inválida.")
            self.pausar()
            return

        # Mostrar datas disponíveis
        print(f"\nAgendando para: {paciente.nome}")
        print("\nDatas disponíveis:")

        datas = self.agendador.obter_proximos_dias_disponiveis(7)
        for i, d in enumerate(datas, 1):
            dia = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'][d.weekday()]
            print(f"  {i}. {dia}, {d.strftime('%d/%m/%Y')}")

        try:
            escolha_data = int(input("\nEscolha a data (número): ").strip())
            data = datas[escolha_data - 1]
        except (ValueError, IndexError):
            print("Escolha inválida.")
            self.pausar()
            return

        # Mostrar horários disponíveis
        print(f"\nHorários disponíveis para {data.strftime('%d/%m/%Y')}:")
        horarios = self.agendador.obter_horarios_disponiveis(data)

        for i, h in enumerate(horarios, 1):
            print(f"  {i}. {h.strftime('%H:%M')}")

        try:
            escolha_hora = int(input("\nEscolha o horário (número): ").strip())
            hora = horarios[escolha_hora - 1]
        except (ValueError, IndexError):
            print("Escolha inválida.")
            self.pausar()
            return

        # Agendar
        sucesso, msg, consulta = self.agendador.agendar_consulta(
            paciente_id=paciente.id,
            data=data,
            hora=hora
        )

        if sucesso:
            print(f"\n✅ {msg}")
            print(f"Consulta #{consulta.id} agendada para {data.strftime('%d/%m/%Y')} às {hora.strftime('%H:%M')}")
        else:
            print(f"\n❌ {msg}")

        self.pausar()

    def buscar_consultas_paciente(self):
        self.limpar_tela()
        self.cabecalho("CONSULTAS DO PACIENTE")

        termo = input("Buscar paciente (nome, telefone ou CPF): ").strip()
        pacientes = self.db.buscar_pacientes(termo)

        if not pacientes:
            print("Nenhum paciente encontrado.")
            self.pausar()
            return

        paciente = pacientes[0]
        consultas = self.db.buscar_consultas_por_paciente(paciente.id)

        print(f"\nPaciente: {paciente.nome}")
        print("-" * 50)

        if not consultas:
            print("Nenhuma consulta encontrada.")
        else:
            for c in consultas:
                dia = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'][c.data.weekday()]
                print(f"#{c.id} - {dia}, {c.data.strftime('%d/%m/%Y')} às {c.hora.strftime('%H:%M')} - {c.status.value}")

        self.pausar()

    def proximas_consultas(self):
        self.limpar_tela()
        self.cabecalho("PRÓXIMAS CONSULTAS")

        consultas = self.db.buscar_proximas_consultas(20)

        if not consultas:
            print("Não há consultas agendadas.")
        else:
            for c in consultas:
                paciente = self.db.buscar_paciente_por_id(c.paciente_id)
                dia = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'][c.data.weekday()]
                print(f"#{c.id} - {dia}, {c.data.strftime('%d/%m/%Y')} {c.hora.strftime('%H:%M')}")
                print(f"    Paciente: {paciente.nome if paciente else 'N/A'} - {c.status.value}")
                print()

        self.pausar()

    def cancelar_consulta(self):
        self.limpar_tela()
        self.cabecalho("CANCELAR CONSULTA")

        id_str = input("ID da consulta: ").strip()
        try:
            consulta_id = int(id_str)
        except ValueError:
            print("ID inválido.")
            self.pausar()
            return

        consulta = self.db.buscar_consulta_por_id(consulta_id)
        if not consulta:
            print("Consulta não encontrada.")
            self.pausar()
            return

        paciente = self.db.buscar_paciente_por_id(consulta.paciente_id)
        print(f"\nConsulta #{consulta.id}")
        print(f"Paciente: {paciente.nome if paciente else 'N/A'}")
        print(f"Data: {consulta.data.strftime('%d/%m/%Y')} às {consulta.hora.strftime('%H:%M')}")

        confirma = input("\nConfirmar cancelamento? (s/n): ").strip().lower()
        if confirma == 's':
            sucesso, msg = self.agendador.cancelar_consulta(consulta_id)
            print(f"\n{'✅' if sucesso else '❌'} {msg}")
        else:
            print("\nOperação cancelada.")

        self.pausar()

    def confirmar_consulta(self):
        self.limpar_tela()
        self.cabecalho("CONFIRMAR CONSULTA")

        id_str = input("ID da consulta: ").strip()
        try:
            consulta_id = int(id_str)
        except ValueError:
            print("ID inválido.")
            self.pausar()
            return

        sucesso, msg = self.agendador.confirmar_consulta(consulta_id)
        print(f"\n{'✅' if sucesso else '❌'} {msg}")
        self.pausar()

    def ver_agenda_dia(self):
        self.limpar_tela()
        self.cabecalho("AGENDA DO DIA")

        data_str = input("Data (DD/MM/AAAA) ou ENTER para hoje: ").strip()

        if data_str:
            try:
                data = datetime.strptime(data_str, "%d/%m/%Y").date()
            except ValueError:
                print("Data inválida.")
                self.pausar()
                return
        else:
            data = date.today()

        dia = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo'][data.weekday()]
        print(f"\n{dia}, {data.strftime('%d/%m/%Y')}")
        print("-" * 50)

        agenda = self.agendador.obter_agenda_do_dia(data)

        if not agenda:
            print("\nNenhuma consulta agendada para este dia.")
        else:
            for item in agenda:
                c = item['consulta']
                p = item['paciente']
                status_icon = '✅' if c.status == StatusConsulta.CONFIRMADA else '📋'
                print(f"{status_icon} {item['horario']} - {p.nome if p else 'N/A'}")
                print(f"   Tel: {p.telefone if p else 'N/A'} | Status: {c.status.value}")
                print()

        self.pausar()

    # ========== CONFIGURAÇÕES ==========

    def menu_configuracoes(self):
        while True:
            self.limpar_tela()
            self.cabecalho("CONFIGURAÇÕES")

            print("  1. Dados do Consultório")
            print("  2. Horários de Atendimento")
            print("  3. Mensagens Personalizadas")
            print("  0. Voltar")
            print()

            opcao = input("Escolha uma opção: ").strip()

            if opcao == '1':
                self.config_consultorio()
            elif opcao == '2':
                self.config_horarios()
            elif opcao == '3':
                self.config_mensagens()
            elif opcao == '0':
                break

    def config_consultorio(self):
        self.limpar_tela()
        self.cabecalho("DADOS DO CONSULTÓRIO")

        print("Dados atuais:")
        print(f"  Nome: {self.config.nome_consultorio}")
        print(f"  Profissional: {self.config.nome_profissional}")
        print(f"  Especialidade: {self.config.especialidade}")
        print(f"  Telefone: {self.config.telefone}")
        print(f"  Endereço: {self.config.endereco}")

        print("\n(Deixe em branco para manter o valor atual)\n")

        self.config.nome_consultorio = input(f"Nome do consultório [{self.config.nome_consultorio}]: ").strip() or self.config.nome_consultorio
        self.config.nome_profissional = input(f"Nome do profissional [{self.config.nome_profissional}]: ").strip() or self.config.nome_profissional
        self.config.especialidade = input(f"Especialidade [{self.config.especialidade}]: ").strip() or self.config.especialidade
        self.config.telefone = input(f"Telefone [{self.config.telefone}]: ").strip() or self.config.telefone
        self.config.endereco = input(f"Endereço [{self.config.endereco}]: ").strip() or self.config.endereco

        self.db.salvar_configuracao(self.config)
        print("\nConfigurações salvas com sucesso!")
        self.pausar()

    def config_horarios(self):
        self.limpar_tela()
        self.cabecalho("HORÁRIOS DE ATENDIMENTO")

        horarios = self.db.buscar_horarios_atendimento()
        dias = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']

        print("Horários atuais:")
        for h in horarios:
            status = "✅" if h.ativo else "❌"
            print(f"  {status} {dias[h.dia_semana.value]}: {h.hora_inicio.strftime('%H:%M')} às {h.hora_fim.strftime('%H:%M')}")

        print("\n1. Ativar/Desativar dia")
        print("2. Alterar horário de um dia")
        print("0. Voltar")

        opcao = input("\nEscolha: ").strip()

        if opcao == '1':
            dia_num = int(input("Número do dia (0=Seg, 6=Dom): ").strip())
            for h in horarios:
                if h.dia_semana.value == dia_num:
                    h.ativo = not h.ativo
                    self.db.salvar_horario_atendimento(h)
                    print(f"{'Ativado' if h.ativo else 'Desativado'} {dias[dia_num]}")
                    break

        elif opcao == '2':
            dia_num = int(input("Número do dia (0=Seg, 6=Dom): ").strip())
            for h in horarios:
                if h.dia_semana.value == dia_num:
                    inicio = input(f"Hora início (atual: {h.hora_inicio.strftime('%H:%M')}): ").strip()
                    fim = input(f"Hora fim (atual: {h.hora_fim.strftime('%H:%M')}): ").strip()

                    if inicio:
                        partes = inicio.split(':')
                        h.hora_inicio = time(int(partes[0]), int(partes[1]))
                    if fim:
                        partes = fim.split(':')
                        h.hora_fim = time(int(partes[0]), int(partes[1]))

                    self.db.salvar_horario_atendimento(h)
                    print("Horário atualizado!")
                    break

        self.pausar()

    def config_mensagens(self):
        self.limpar_tela()
        self.cabecalho("MENSAGENS PERSONALIZADAS")

        print("Mensagens atuais:\n")
        print(f"Boas-vindas: {self.config.mensagem_boas_vindas}")
        print(f"\nConfirmação: {self.config.mensagem_confirmacao}")

        print("\n(Deixe em branco para manter)\n")

        msg = input("Nova mensagem de boas-vindas: ").strip()
        if msg:
            self.config.mensagem_boas_vindas = msg

        msg = input("Nova mensagem de confirmação: ").strip()
        if msg:
            self.config.mensagem_confirmacao = msg

        self.db.salvar_configuracao(self.config)
        print("\nMensagens atualizadas!")
        self.pausar()
