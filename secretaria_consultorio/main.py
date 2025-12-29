#!/usr/bin/env python3
"""
Secretária Eletrônica de Consultório
=====================================

Sistema completo para gerenciamento de consultório médico com:
- Agendamento de consultas
- Chatbot para atendimento de pacientes
- Gerenciamento de pacientes
- Configuração de horários de atendimento

Uso:
    python main.py              # Inicia a interface CLI
    python main.py --chat       # Inicia apenas o modo chatbot
    python main.py --config     # Configuração inicial
"""

import sys
import os

# Adicionar o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cli import CLI
from database import Database
from chatbot import Chatbot


def configuracao_inicial(db: Database):
    """Executa configuração inicial do consultório"""
    from models import ConfiguracaoConsultorio

    print("\n" + "=" * 60)
    print("  CONFIGURAÇÃO INICIAL DO CONSULTÓRIO")
    print("=" * 60 + "\n")

    config = ConfiguracaoConsultorio()

    config.nome_consultorio = input("Nome do consultório: ").strip() or "Meu Consultório"
    config.nome_profissional = input("Nome do profissional (ex: Dr. João Silva): ").strip() or "Dr(a). Nome"
    config.especialidade = input("Especialidade: ").strip() or ""
    config.telefone = input("Telefone do consultório: ").strip() or ""
    config.endereco = input("Endereço completo: ").strip() or ""

    print("\nMensagens personalizadas (ENTER para usar padrão):")
    msg = input("Mensagem de boas-vindas: ").strip()
    if msg:
        config.mensagem_boas_vindas = msg

    msg = input("Mensagem de confirmação de consulta: ").strip()
    if msg:
        config.mensagem_confirmacao = msg

    db.salvar_configuracao(config)

    print("\n✅ Configuração salva com sucesso!")
    print("\nVocê pode alterar essas configurações a qualquer momento no menu de configurações.")


def modo_chatbot_simples(db: Database):
    """Executa apenas o chatbot em modo simples"""
    from datetime import datetime

    chatbot = Chatbot(db)
    config = db.carregar_configuracao()

    print("\n" + "=" * 60)
    print(f"  {config.nome_consultorio}")
    print(f"  {config.nome_profissional}")
    print("=" * 60)
    print("\nDigite 'sair' para encerrar\n")

    session_id = f"simple_{datetime.now().timestamp()}"

    # Mensagem inicial
    resposta = chatbot.processar_mensagem(session_id, "")
    print(resposta)

    while True:
        try:
            mensagem = input("\nVocê: ").strip()

            if mensagem.lower() in ['sair', 'exit', 'quit']:
                print("\nObrigado por utilizar nosso serviço! Até logo!")
                break

            resposta = chatbot.processar_mensagem(session_id, mensagem)
            print(f"\n{resposta}")

        except KeyboardInterrupt:
            print("\n\nEncerrando...")
            break
        except EOFError:
            break


def main():
    """Função principal"""
    # Determinar o caminho do banco de dados
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, "consultorio.db")

    db = Database(db_path)

    # Verificar argumentos
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()

        if arg in ['--config', '-c', 'config']:
            configuracao_inicial(db)
            return

        elif arg in ['--chat', '-t', 'chat']:
            modo_chatbot_simples(db)
            return

        elif arg in ['--help', '-h', 'help']:
            print(__doc__)
            return

    # Verificar se é primeira execução
    config = db.carregar_configuracao()
    if config.nome_consultorio == "Meu Consultório" and config.nome_profissional == "Dr(a). Nome":
        print("\nParece que é sua primeira vez usando o sistema.")
        resp = input("Deseja fazer a configuração inicial? (s/n): ").strip().lower()
        if resp == 's':
            configuracao_inicial(db)

    # Iniciar CLI
    cli = CLI(db_path)

    try:
        cli.menu_principal()
    except KeyboardInterrupt:
        print("\n\nEncerrando...")
    except Exception as e:
        print(f"\nErro: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
