#!/usr/bin/env python3
"""
Servidor Webhook para receber mensagens do WhatsApp

Suporta:
- Twilio Webhooks
- Evolution API Webhooks
- Meta Cloud API Webhooks

Uso:
    python webhook_server.py [porta]

Exemplo:
    python webhook_server.py 5000
"""

import json
import os
import sys
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

# Adicionar diretório ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import Database
from chatbot import Chatbot
from whatsapp import WhatsAppService, ProvedorWhatsApp


class WebhookHandler(BaseHTTPRequestHandler):
    """Handler para requisições do webhook"""

    db: Database = None
    chatbot: Chatbot = None
    whatsapp: WhatsAppService = None
    sessoes: Dict[str, str] = {}  # telefone -> session_id

    @classmethod
    def inicializar(cls, db_path: str = "consultorio.db"):
        """Inicializa as dependências"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(script_dir, db_path)

        cls.db = Database(full_path)
        cls.chatbot = Chatbot(cls.db)
        cls.whatsapp = WhatsAppService(cls.db)

    def _enviar_resposta(self, status: int, body: str, content_type: str = "application/json"):
        """Envia resposta HTTP"""
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', len(body.encode()))
        self.end_headers()
        self.wfile.write(body.encode())

    def _obter_session_id(self, telefone: str) -> str:
        """Obtém ou cria session_id para um telefone"""
        if telefone not in self.sessoes:
            self.sessoes[telefone] = f"whatsapp_{telefone}_{datetime.now().timestamp()}"
        return self.sessoes[telefone]

    def _processar_mensagem(self, telefone: str, mensagem: str) -> str:
        """Processa mensagem através do chatbot e retorna resposta"""
        session_id = self._obter_session_id(telefone)

        # Processar através do chatbot
        resposta = self.chatbot.processar_mensagem(session_id, mensagem)

        # Remover emojis de número que não funcionam bem no WhatsApp
        resposta = re.sub(r'(\d)️⃣', r'\1.', resposta)

        return resposta

    def do_GET(self):
        """Trata requisições GET (verificação de webhook)"""
        parsed_path = urlparse(self.path)
        params = parse_qs(parsed_path.query)

        # Verificação do webhook Meta/Facebook
        if parsed_path.path == '/webhook':
            mode = params.get('hub.mode', [''])[0]
            token = params.get('hub.verify_token', [''])[0]
            challenge = params.get('hub.challenge', [''])[0]

            # Token de verificação (configurável)
            verify_token = os.environ.get('WEBHOOK_VERIFY_TOKEN', 'secretaria_consultorio')

            if mode == 'subscribe' and token == verify_token:
                print(f"[WEBHOOK] Verificação Meta bem-sucedida")
                self._enviar_resposta(200, challenge, "text/plain")
            else:
                self._enviar_resposta(403, "Forbidden")

        # Health check
        elif parsed_path.path == '/health':
            status = {
                "status": "ok",
                "whatsapp": self.whatsapp.verificar_conexao()[0] if self.whatsapp else False,
                "timestamp": datetime.now().isoformat()
            }
            self._enviar_resposta(200, json.dumps(status))

        else:
            self._enviar_resposta(404, json.dumps({"error": "Not found"}))

    def do_POST(self):
        """Trata requisições POST (mensagens recebidas)"""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')

        parsed_path = urlparse(self.path)

        try:
            # Determinar o tipo de webhook baseado no path ou conteúdo
            if parsed_path.path == '/webhook/twilio':
                self._processar_twilio(body)

            elif parsed_path.path == '/webhook/evolution':
                self._processar_evolution(body)

            elif parsed_path.path in ['/webhook', '/webhook/meta']:
                self._processar_meta(body)

            else:
                # Tentar detectar automaticamente
                if 'From' in body and 'Body' in body:
                    self._processar_twilio(body)
                elif 'entry' in body:
                    self._processar_meta(body)
                else:
                    self._processar_evolution(body)

            self._enviar_resposta(200, json.dumps({"status": "ok"}))

        except Exception as e:
            print(f"[WEBHOOK] Erro: {str(e)}")
            self._enviar_resposta(500, json.dumps({"error": str(e)}))

    def _processar_twilio(self, body: str):
        """Processa webhook do Twilio"""
        params = parse_qs(body)

        telefone = params.get('From', [''])[0]
        mensagem = params.get('Body', [''])[0]

        # Limpar formato do Twilio (whatsapp:+5511999998888)
        telefone = re.sub(r'whatsapp:\+?', '', telefone)

        if telefone and mensagem:
            print(f"[TWILIO] Mensagem de {telefone}: {mensagem}")

            resposta = self._processar_mensagem(telefone, mensagem)

            # Enviar resposta
            sucesso, msg = self.whatsapp.enviar_mensagem(telefone, resposta)
            print(f"[TWILIO] Resposta enviada: {sucesso} - {msg}")

    def _processar_evolution(self, body: str):
        """Processa webhook do Evolution API"""
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return

        # Evolution pode enviar diferentes tipos de eventos
        event = data.get('event', '')

        if event in ['messages.upsert', 'message']:
            messages = data.get('data', {}).get('messages', [data.get('data', {})])

            for msg_data in messages:
                # Extrair telefone e mensagem
                key = msg_data.get('key', {})
                telefone = key.get('remoteJid', '').split('@')[0]
                mensagem = msg_data.get('message', {}).get('conversation', '')

                # Também pode vir em extendedTextMessage
                if not mensagem:
                    mensagem = msg_data.get('message', {}).get('extendedTextMessage', {}).get('text', '')

                if telefone and mensagem and not key.get('fromMe', False):
                    print(f"[EVOLUTION] Mensagem de {telefone}: {mensagem}")

                    resposta = self._processar_mensagem(telefone, mensagem)

                    sucesso, msg = self.whatsapp.enviar_mensagem(telefone, resposta)
                    print(f"[EVOLUTION] Resposta enviada: {sucesso} - {msg}")

    def _processar_meta(self, body: str):
        """Processa webhook do Meta Cloud API"""
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return

        # Estrutura do webhook Meta
        entries = data.get('entry', [])

        for entry in entries:
            changes = entry.get('changes', [])

            for change in changes:
                value = change.get('value', {})
                messages = value.get('messages', [])

                for msg in messages:
                    telefone = msg.get('from', '')
                    msg_type = msg.get('type', '')

                    mensagem = ''
                    if msg_type == 'text':
                        mensagem = msg.get('text', {}).get('body', '')
                    elif msg_type == 'interactive':
                        # Respostas de botões
                        interactive = msg.get('interactive', {})
                        if interactive.get('type') == 'button_reply':
                            mensagem = interactive.get('button_reply', {}).get('title', '')
                        elif interactive.get('type') == 'list_reply':
                            mensagem = interactive.get('list_reply', {}).get('title', '')

                    if telefone and mensagem:
                        print(f"[META] Mensagem de {telefone}: {mensagem}")

                        resposta = self._processar_mensagem(telefone, mensagem)

                        sucesso, msg_result = self.whatsapp.enviar_mensagem(telefone, resposta)
                        print(f"[META] Resposta enviada: {sucesso} - {msg_result}")

    def log_message(self, format, *args):
        """Customiza log de requisições"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]}")


def executar_servidor(porta: int = 5000, db_path: str = "consultorio.db"):
    """Inicia o servidor webhook"""
    WebhookHandler.inicializar(db_path)

    server = HTTPServer(('0.0.0.0', porta), WebhookHandler)

    print("=" * 60)
    print("  SERVIDOR WEBHOOK - SECRETÁRIA ELETRÔNICA")
    print("=" * 60)
    print(f"\n  Rodando em: http://0.0.0.0:{porta}")
    print(f"\n  Endpoints:")
    print(f"    POST /webhook/twilio    - Webhook Twilio")
    print(f"    POST /webhook/evolution - Webhook Evolution API")
    print(f"    POST /webhook/meta      - Webhook Meta Cloud API")
    print(f"    GET  /webhook           - Verificação Meta")
    print(f"    GET  /health            - Health check")
    print(f"\n  Pressione Ctrl+C para parar\n")
    print("=" * 60 + "\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\nServidor encerrado.")
        server.shutdown()


if __name__ == "__main__":
    porta = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    executar_servidor(porta)
