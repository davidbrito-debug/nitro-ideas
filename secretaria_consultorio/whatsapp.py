"""
Módulo de integração com WhatsApp

Suporta múltiplos provedores:
- Twilio (API paga, mais confiável)
- Evolution API (gratuito, self-hosted)
- WhatsApp Business Cloud API (oficial Meta)

Configuração via variáveis de ambiente ou arquivo .env
"""

import os
import json
import re
from abc import ABC, abstractmethod
from datetime import datetime, date, time, timedelta
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class ProvedorWhatsApp(Enum):
    TWILIO = "twilio"
    EVOLUTION = "evolution"
    META_CLOUD = "meta_cloud"
    MOCK = "mock"  # Para testes


@dataclass
class ConfiguracaoWhatsApp:
    provedor: ProvedorWhatsApp = ProvedorWhatsApp.MOCK

    # Twilio
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_number: str = ""  # Ex: whatsapp:+14155238886

    # Evolution API
    evolution_api_url: str = ""  # Ex: http://localhost:8080
    evolution_api_key: str = ""
    evolution_instance: str = ""

    # Meta Cloud API
    meta_access_token: str = ""
    meta_phone_number_id: str = ""
    meta_business_account_id: str = ""

    # Configurações gerais
    webhook_url: str = ""
    lembrete_horas_antes: int = 24
    ativo: bool = False


@dataclass
class MensagemWhatsApp:
    telefone: str
    mensagem: str
    tipo: str = "text"  # text, template, media
    template_name: str = ""
    template_params: List[str] = None
    media_url: str = ""

    def __post_init__(self):
        if self.template_params is None:
            self.template_params = []


class ProvedorBase(ABC):
    """Classe base para provedores de WhatsApp"""

    @abstractmethod
    def enviar_mensagem(self, msg: MensagemWhatsApp) -> Tuple[bool, str]:
        """Envia uma mensagem. Retorna (sucesso, mensagem_ou_erro)"""
        pass

    @abstractmethod
    def verificar_conexao(self) -> bool:
        """Verifica se a conexão está ativa"""
        pass

    def formatar_telefone(self, telefone: str, codigo_pais: str = "55") -> str:
        """Formata o telefone para o padrão internacional"""
        # Remove tudo que não é número
        apenas_numeros = re.sub(r'\D', '', telefone)

        # Se não começar com código do país, adiciona
        if not apenas_numeros.startswith(codigo_pais):
            apenas_numeros = codigo_pais + apenas_numeros

        return apenas_numeros


class ProvedorMock(ProvedorBase):
    """Provedor de teste que simula envio"""

    def __init__(self, config: ConfiguracaoWhatsApp):
        self.config = config
        self.mensagens_enviadas: List[MensagemWhatsApp] = []

    def enviar_mensagem(self, msg: MensagemWhatsApp) -> Tuple[bool, str]:
        self.mensagens_enviadas.append(msg)
        print(f"[MOCK] WhatsApp para {msg.telefone}: {msg.mensagem[:50]}...")
        return True, "Mensagem simulada com sucesso"

    def verificar_conexao(self) -> bool:
        return True


class ProvedorTwilio(ProvedorBase):
    """Provedor usando Twilio API"""

    def __init__(self, config: ConfiguracaoWhatsApp):
        self.config = config
        self.base_url = "https://api.twilio.com/2010-04-01"

    def enviar_mensagem(self, msg: MensagemWhatsApp) -> Tuple[bool, str]:
        if not REQUESTS_AVAILABLE:
            return False, "Biblioteca 'requests' não instalada. Execute: pip install requests"

        telefone = self.formatar_telefone(msg.telefone)

        url = f"{self.base_url}/Accounts/{self.config.twilio_account_sid}/Messages.json"

        data = {
            "From": self.config.twilio_whatsapp_number,
            "To": f"whatsapp:+{telefone}",
            "Body": msg.mensagem
        }

        try:
            response = requests.post(
                url,
                data=data,
                auth=(self.config.twilio_account_sid, self.config.twilio_auth_token)
            )

            if response.status_code in [200, 201]:
                return True, response.json().get('sid', 'Enviado')
            else:
                return False, f"Erro Twilio: {response.text}"

        except Exception as e:
            return False, f"Erro de conexão: {str(e)}"

    def verificar_conexao(self) -> bool:
        if not REQUESTS_AVAILABLE:
            return False
        try:
            url = f"{self.base_url}/Accounts/{self.config.twilio_account_sid}.json"
            response = requests.get(
                url,
                auth=(self.config.twilio_account_sid, self.config.twilio_auth_token)
            )
            return response.status_code == 200
        except:
            return False


class ProvedorEvolution(ProvedorBase):
    """Provedor usando Evolution API (self-hosted, gratuito)"""

    def __init__(self, config: ConfiguracaoWhatsApp):
        self.config = config

    def enviar_mensagem(self, msg: MensagemWhatsApp) -> Tuple[bool, str]:
        if not REQUESTS_AVAILABLE:
            return False, "Biblioteca 'requests' não instalada. Execute: pip install requests"

        telefone = self.formatar_telefone(msg.telefone)

        url = f"{self.config.evolution_api_url}/message/sendText/{self.config.evolution_instance}"

        headers = {
            "Content-Type": "application/json",
            "apikey": self.config.evolution_api_key
        }

        data = {
            "number": telefone,
            "text": msg.mensagem
        }

        try:
            response = requests.post(url, json=data, headers=headers)

            if response.status_code in [200, 201]:
                return True, "Mensagem enviada"
            else:
                return False, f"Erro Evolution: {response.text}"

        except Exception as e:
            return False, f"Erro de conexão: {str(e)}"

    def verificar_conexao(self) -> bool:
        if not REQUESTS_AVAILABLE:
            return False
        try:
            url = f"{self.config.evolution_api_url}/instance/connectionState/{self.config.evolution_instance}"
            headers = {"apikey": self.config.evolution_api_key}
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                return data.get('state') == 'open'
            return False
        except:
            return False


class ProvedorMetaCloud(ProvedorBase):
    """Provedor usando WhatsApp Business Cloud API (oficial Meta)"""

    def __init__(self, config: ConfiguracaoWhatsApp):
        self.config = config
        self.base_url = "https://graph.facebook.com/v18.0"

    def enviar_mensagem(self, msg: MensagemWhatsApp) -> Tuple[bool, str]:
        if not REQUESTS_AVAILABLE:
            return False, "Biblioteca 'requests' não instalada. Execute: pip install requests"

        telefone = self.formatar_telefone(msg.telefone)

        url = f"{self.base_url}/{self.config.meta_phone_number_id}/messages"

        headers = {
            "Authorization": f"Bearer {self.config.meta_access_token}",
            "Content-Type": "application/json"
        }

        if msg.tipo == "template" and msg.template_name:
            data = {
                "messaging_product": "whatsapp",
                "to": telefone,
                "type": "template",
                "template": {
                    "name": msg.template_name,
                    "language": {"code": "pt_BR"},
                    "components": [
                        {
                            "type": "body",
                            "parameters": [{"type": "text", "text": p} for p in msg.template_params]
                        }
                    ] if msg.template_params else []
                }
            }
        else:
            data = {
                "messaging_product": "whatsapp",
                "to": telefone,
                "type": "text",
                "text": {"body": msg.mensagem}
            }

        try:
            response = requests.post(url, json=data, headers=headers)

            if response.status_code in [200, 201]:
                return True, response.json().get('messages', [{}])[0].get('id', 'Enviado')
            else:
                return False, f"Erro Meta: {response.text}"

        except Exception as e:
            return False, f"Erro de conexão: {str(e)}"

    def verificar_conexao(self) -> bool:
        if not REQUESTS_AVAILABLE:
            return False
        try:
            url = f"{self.base_url}/{self.config.meta_phone_number_id}"
            headers = {"Authorization": f"Bearer {self.config.meta_access_token}"}
            response = requests.get(url, headers=headers)
            return response.status_code == 200
        except:
            return False


class WhatsAppService:
    """Serviço principal de WhatsApp"""

    def __init__(self, db):
        self.db = db
        self.config = self._carregar_config()
        self.provedor = self._criar_provedor()

    def _carregar_config(self) -> ConfiguracaoWhatsApp:
        """Carrega configuração do banco ou variáveis de ambiente"""
        config = ConfiguracaoWhatsApp()

        # Tentar carregar do banco de dados
        try:
            with self.db._conexao() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT chave, valor FROM configuracoes WHERE chave LIKE 'whatsapp_%'")
                for row in cursor.fetchall():
                    chave = row['chave'].replace('whatsapp_', '')
                    valor = row['valor']
                    if hasattr(config, chave):
                        if chave == 'provedor':
                            try:
                                setattr(config, chave, ProvedorWhatsApp(valor))
                            except ValueError:
                                pass
                        elif chave in ['lembrete_horas_antes']:
                            setattr(config, chave, int(valor))
                        elif chave == 'ativo':
                            setattr(config, chave, valor.lower() == 'true')
                        else:
                            setattr(config, chave, valor)
        except:
            pass

        # Override com variáveis de ambiente se existirem
        env_mappings = {
            'TWILIO_ACCOUNT_SID': 'twilio_account_sid',
            'TWILIO_AUTH_TOKEN': 'twilio_auth_token',
            'TWILIO_WHATSAPP_NUMBER': 'twilio_whatsapp_number',
            'EVOLUTION_API_URL': 'evolution_api_url',
            'EVOLUTION_API_KEY': 'evolution_api_key',
            'EVOLUTION_INSTANCE': 'evolution_instance',
            'META_ACCESS_TOKEN': 'meta_access_token',
            'META_PHONE_NUMBER_ID': 'meta_phone_number_id',
            'WHATSAPP_PROVIDER': 'provedor',
        }

        for env_var, config_key in env_mappings.items():
            value = os.environ.get(env_var)
            if value:
                if config_key == 'provedor':
                    try:
                        config.provedor = ProvedorWhatsApp(value.lower())
                    except ValueError:
                        pass
                else:
                    setattr(config, config_key, value)

        return config

    def _criar_provedor(self) -> ProvedorBase:
        """Cria o provedor apropriado baseado na configuração"""
        if self.config.provedor == ProvedorWhatsApp.TWILIO:
            return ProvedorTwilio(self.config)
        elif self.config.provedor == ProvedorWhatsApp.EVOLUTION:
            return ProvedorEvolution(self.config)
        elif self.config.provedor == ProvedorWhatsApp.META_CLOUD:
            return ProvedorMetaCloud(self.config)
        else:
            return ProvedorMock(self.config)

    def salvar_config(self, config: ConfiguracaoWhatsApp):
        """Salva configuração no banco de dados"""
        self.config = config
        self.provedor = self._criar_provedor()

        with self.db._conexao() as conn:
            cursor = conn.cursor()

            configs = {
                'whatsapp_provedor': config.provedor.value,
                'whatsapp_twilio_account_sid': config.twilio_account_sid,
                'whatsapp_twilio_auth_token': config.twilio_auth_token,
                'whatsapp_twilio_whatsapp_number': config.twilio_whatsapp_number,
                'whatsapp_evolution_api_url': config.evolution_api_url,
                'whatsapp_evolution_api_key': config.evolution_api_key,
                'whatsapp_evolution_instance': config.evolution_instance,
                'whatsapp_meta_access_token': config.meta_access_token,
                'whatsapp_meta_phone_number_id': config.meta_phone_number_id,
                'whatsapp_lembrete_horas_antes': str(config.lembrete_horas_antes),
                'whatsapp_ativo': str(config.ativo).lower(),
            }

            for chave, valor in configs.items():
                cursor.execute("""
                    INSERT OR REPLACE INTO configuracoes (chave, valor) VALUES (?, ?)
                """, (chave, valor))

    def verificar_conexao(self) -> Tuple[bool, str]:
        """Verifica se a conexão com WhatsApp está ativa"""
        if not self.config.ativo:
            return False, "WhatsApp não está ativo"

        if self.provedor.verificar_conexao():
            return True, f"Conectado via {self.config.provedor.value}"
        else:
            return False, "Falha na conexão"

    def enviar_mensagem(self, telefone: str, mensagem: str) -> Tuple[bool, str]:
        """Envia uma mensagem de texto simples"""
        if not self.config.ativo:
            return False, "WhatsApp não está ativo"

        msg = MensagemWhatsApp(telefone=telefone, mensagem=mensagem)
        return self.provedor.enviar_mensagem(msg)

    def enviar_confirmacao_agendamento(
        self,
        telefone: str,
        nome_paciente: str,
        data: date,
        hora: time,
        nome_profissional: str,
        endereco: str
    ) -> Tuple[bool, str]:
        """Envia confirmação de agendamento"""
        dia_semana = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo'][data.weekday()]

        mensagem = f"""✅ *Consulta Agendada!*

Olá, {nome_paciente.split()[0]}!

Sua consulta foi confirmada:

📅 *Data:* {dia_semana}, {data.strftime('%d/%m/%Y')}
⏰ *Horário:* {hora.strftime('%H:%M')}
👨‍⚕️ *Profissional:* {nome_profissional}
📍 *Local:* {endereco}

⚠️ Por favor, chegue com 15 minutos de antecedência.

Para remarcar ou cancelar, responda esta mensagem."""

        return self.enviar_mensagem(telefone, mensagem)

    def enviar_lembrete_consulta(
        self,
        telefone: str,
        nome_paciente: str,
        data: date,
        hora: time,
        nome_profissional: str,
        endereco: str
    ) -> Tuple[bool, str]:
        """Envia lembrete de consulta"""
        dia_semana = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo'][data.weekday()]

        # Calcular se é amanhã ou hoje
        hoje = date.today()
        if data == hoje:
            quando = "HOJE"
        elif data == hoje + timedelta(days=1):
            quando = "AMANHÃ"
        else:
            quando = f"em {dia_semana}, {data.strftime('%d/%m')}"

        mensagem = f"""⏰ *Lembrete de Consulta*

Olá, {nome_paciente.split()[0]}!

Lembramos que você tem consulta marcada para *{quando}*:

📅 {dia_semana}, {data.strftime('%d/%m/%Y')}
⏰ {hora.strftime('%H:%M')}
👨‍⚕️ {nome_profissional}
📍 {endereco}

✅ Responda *SIM* para confirmar
❌ Responda *CANCELAR* para desmarcar"""

        return self.enviar_mensagem(telefone, mensagem)

    def enviar_cancelamento(
        self,
        telefone: str,
        nome_paciente: str,
        data: date,
        hora: time
    ) -> Tuple[bool, str]:
        """Notifica cancelamento de consulta"""
        mensagem = f"""❌ *Consulta Cancelada*

Olá, {nome_paciente.split()[0]}!

Sua consulta do dia {data.strftime('%d/%m/%Y')} às {hora.strftime('%H:%M')} foi cancelada.

Para reagendar, responda esta mensagem ou acesse nosso sistema de agendamento."""

        return self.enviar_mensagem(telefone, mensagem)

    def obter_consultas_para_lembrete(self) -> List[Dict]:
        """Obtém consultas que precisam receber lembrete"""
        from models import StatusConsulta

        horas_antes = self.config.lembrete_horas_antes
        agora = datetime.now()
        limite = agora + timedelta(hours=horas_antes)

        consultas_lembrete = []

        with self.db._conexao() as conn:
            cursor = conn.cursor()

            # Buscar consultas próximas que ainda não receberam lembrete
            cursor.execute("""
                SELECT c.*, p.nome as paciente_nome, p.telefone as paciente_telefone
                FROM consultas c
                JOIN pacientes p ON c.paciente_id = p.id
                WHERE c.status IN ('agendada', 'confirmada')
                AND c.data >= date('now')
                AND c.id NOT IN (
                    SELECT CAST(valor AS INTEGER) FROM configuracoes
                    WHERE chave LIKE 'lembrete_enviado_%'
                )
            """)

            for row in cursor.fetchall():
                data_consulta = date.fromisoformat(row['data'])
                hora_parts = row['hora'].split(':')
                hora_consulta = time(int(hora_parts[0]), int(hora_parts[1]))

                data_hora_consulta = datetime.combine(data_consulta, hora_consulta)

                # Verificar se está dentro do período de lembrete
                if agora < data_hora_consulta <= limite:
                    consultas_lembrete.append({
                        'id': row['id'],
                        'data': data_consulta,
                        'hora': hora_consulta,
                        'paciente_nome': row['paciente_nome'],
                        'paciente_telefone': row['paciente_telefone']
                    })

        return consultas_lembrete

    def marcar_lembrete_enviado(self, consulta_id: int):
        """Marca que o lembrete foi enviado para uma consulta"""
        with self.db._conexao() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO configuracoes (chave, valor)
                VALUES (?, ?)
            """, (f"lembrete_enviado_{consulta_id}", str(consulta_id)))

    def processar_lembretes(self) -> List[Dict]:
        """Processa e envia todos os lembretes pendentes"""
        if not self.config.ativo:
            return []

        config_consultorio = self.db.carregar_configuracao()
        consultas = self.obter_consultas_para_lembrete()
        resultados = []

        for consulta in consultas:
            sucesso, msg = self.enviar_lembrete_consulta(
                telefone=consulta['paciente_telefone'],
                nome_paciente=consulta['paciente_nome'],
                data=consulta['data'],
                hora=consulta['hora'],
                nome_profissional=config_consultorio.nome_profissional,
                endereco=config_consultorio.endereco
            )

            if sucesso:
                self.marcar_lembrete_enviado(consulta['id'])

            resultados.append({
                'consulta_id': consulta['id'],
                'paciente': consulta['paciente_nome'],
                'sucesso': sucesso,
                'mensagem': msg
            })

        return resultados
