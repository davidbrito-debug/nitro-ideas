"""
Configurações do programa de pesquisa de prontuário iClinic.

IMPORTANTE: Antes de usar, preencha suas credenciais abaixo.
Nunca compartilhe este arquivo com credenciais preenchidas.
"""

# ============================================================
# CREDENCIAIS DE ACESSO AO ICLINIC
# ============================================================
ICLINIC_EMAIL = ""  # Seu e-mail de login no iClinic
ICLINIC_SENHA = ""  # Sua senha do iClinic

# URL base do iClinic
ICLINIC_URL = "https://app.iclinic.com.br"

# ============================================================
# CONFIGURAÇÃO DO NAVEGADOR
# ============================================================
# Executar navegador em modo invisível (sem janela)
HEADLESS = False

# Tempo máximo de espera por elementos na página (segundos)
TIMEOUT_ESPERA = 15

# Intervalo entre ações para evitar bloqueio (segundos)
INTERVALO_ACOES = 2

# ============================================================
# CRITÉRIOS DE BUSCA
# ============================================================
# Tags que indicam Nota Fiscal no prontuário
TAGS_NOTA_FISCAL = ["NF", "Nota Fiscal"]

# Termos que identificam PDF de bioimpedância nos anexos
TERMOS_BIOIMPEDANCIA = [
    "bioimpedância",
    "bioimpedanciometria",
    "bioimpedancia",
    "composição corporal",
    "composicao corporal",
    "InBody",
]

# ============================================================
# SELETORES CSS DO ICLINIC (AJUSTAR CONFORME NECESSÁRIO)
# ============================================================
# Estes seletores são estimativas baseadas em padrões comuns.
# Você PRECISA verificar e ajustar usando o Inspecionar Elemento
# do navegador (F12) na interface real do iClinic.
#
# Para descobrir os seletores corretos:
# 1. Abra app.iclinic.com.br no Chrome
# 2. Pressione F12 para abrir o DevTools
# 3. Use a ferramenta de seleção (ícone de cursor no canto
#    superior esquerdo do DevTools)
# 4. Clique no elemento desejado na página
# 5. No painel Elements, clique com botão direito no HTML
#    destacado → Copy → Copy selector

SELETORES = {
    # Login
    "campo_email": 'input[type="email"], input[name="email"], #email',
    "campo_senha": 'input[type="password"], input[name="password"], #password',
    "botao_login": 'button[type="submit"], .btn-login, .login-btn',

    # Agenda
    "link_agenda": 'a[href*="agenda"], a[href*="schedule"], .menu-agenda',
    "seletor_data": 'input[type="date"], .date-picker input, .datepicker',
    "lista_pacientes_agenda": '.appointment-item, .schedule-item, tr.patient-row',
    "nome_paciente_agenda": '.patient-name, .appointment-patient, td.patient',
    "link_prontuario": 'a[href*="prontuario"], a[href*="record"], .open-record',

    # Prontuário
    "area_tags": '.tags, .patient-tags, .tag-list, .badges',
    "tag_individual": '.tag, .badge, .label, .chip',
    "area_anexos": '.attachments, .documents, .files, .anexos',
    "item_anexo": '.attachment-item, .document-item, .file-item',
    "nome_anexo": '.attachment-name, .file-name, .document-title',
    "data_anexo": '.attachment-date, .file-date, .document-date',

    # Dados do paciente
    "campo_nome_completo": '.patient-name, .full-name, h1.name, h2.name',
    "campo_cpf": '.cpf, [data-field="cpf"], .document-number',
    "campo_endereco": '.address, .endereco, [data-field="address"]',
    "link_dados_paciente": 'a[href*="patient"], a[href*="paciente"], .patient-profile',

    # Navegação
    "botao_voltar": '.btn-back, .back-button, a.back',
}
