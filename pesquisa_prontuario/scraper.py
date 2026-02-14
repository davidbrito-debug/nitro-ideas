"""
Módulo de automação web para pesquisa no iClinic via Selenium.

Este módulo interage com a interface web do iClinic para:
1. Fazer login
2. Navegar até a agenda de uma data específica
3. Abrir o prontuário de cada paciente
4. Verificar tags (NF/Nota Fiscal) e anexos (bioimpedanciometria)
5. Coletar dados dos pacientes que atendem aos critérios
"""

import time
import logging
from datetime import date, datetime
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    StaleElementReferenceException,
)

try:
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    ChromeDriverManager = None

from pesquisa_prontuario.config import (
    ICLINIC_EMAIL,
    ICLINIC_SENHA,
    ICLINIC_URL,
    HEADLESS,
    TIMEOUT_ESPERA,
    INTERVALO_ACOES,
    TAGS_NOTA_FISCAL,
    TERMOS_BIOIMPEDANCIA,
    SELETORES,
)
from pesquisa_prontuario.models import Criterio, PacienteRegistro, ResultadoPesquisa

logger = logging.getLogger(__name__)


class IClinicScraper:
    """Automatiza a pesquisa de prontuários no iClinic."""

    def __init__(self):
        self.driver: Optional[webdriver.Chrome] = None

    def iniciar_navegador(self) -> None:
        """Inicia o Chrome com as configurações definidas."""
        options = ChromeOptions()
        if HEADLESS:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        # Evitar detecção de automação
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])

        if ChromeDriverManager:
            service = ChromeService(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
        else:
            self.driver = webdriver.Chrome(options=options)

        self.driver.implicitly_wait(TIMEOUT_ESPERA)
        logger.info("Navegador iniciado")

    def encerrar(self) -> None:
        """Encerra o navegador."""
        if self.driver:
            self.driver.quit()
            self.driver = None
            logger.info("Navegador encerrado")

    def _esperar_elemento(self, seletor_css: str, timeout: int = None) -> Optional[object]:
        """Espera um elemento aparecer na página."""
        timeout = timeout or TIMEOUT_ESPERA
        # Tenta cada seletor separado por vírgula
        seletores = [s.strip() for s in seletor_css.split(",")]
        for sel in seletores:
            try:
                elemento = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, sel))
                )
                return elemento
            except TimeoutException:
                continue
        return None

    def _encontrar_elementos(self, seletor_css: str) -> list:
        """Encontra todos os elementos que correspondem ao seletor."""
        seletores = [s.strip() for s in seletor_css.split(",")]
        for sel in seletores:
            try:
                elementos = self.driver.find_elements(By.CSS_SELECTOR, sel)
                if elementos:
                    return elementos
            except NoSuchElementException:
                continue
        return []

    def _pausa(self) -> None:
        """Pausa entre ações para simular comportamento humano."""
        time.sleep(INTERVALO_ACOES)

    # ----------------------------------------------------------------
    # LOGIN
    # ----------------------------------------------------------------

    def fazer_login(self) -> bool:
        """Realiza login no iClinic."""
        if not ICLINIC_EMAIL or not ICLINIC_SENHA:
            logger.error(
                "Credenciais não configuradas. Edite config.py com seu e-mail e senha."
            )
            return False

        logger.info("Acessando página de login...")
        self.driver.get(f"{ICLINIC_URL}/login")
        self._pausa()

        # Preencher e-mail
        campo_email = self._esperar_elemento(SELETORES["campo_email"])
        if not campo_email:
            logger.error("Campo de e-mail não encontrado. Verifique o seletor.")
            return False
        campo_email.clear()
        campo_email.send_keys(ICLINIC_EMAIL)

        # Preencher senha
        campo_senha = self._esperar_elemento(SELETORES["campo_senha"])
        if not campo_senha:
            logger.error("Campo de senha não encontrado. Verifique o seletor.")
            return False
        campo_senha.clear()
        campo_senha.send_keys(ICLINIC_SENHA)

        # Clicar no botão de login
        botao = self._esperar_elemento(SELETORES["botao_login"])
        if botao:
            botao.click()
        else:
            # Tentar submit via Enter
            campo_senha.send_keys(Keys.RETURN)

        self._pausa()
        self._pausa()  # Espera extra para carregamento pós-login

        # Verificar se o login foi bem-sucedido
        if "login" in self.driver.current_url.lower():
            logger.error("Falha no login. Verifique suas credenciais.")
            return False

        logger.info("Login realizado com sucesso")
        return True

    # ----------------------------------------------------------------
    # NAVEGAÇÃO NA AGENDA
    # ----------------------------------------------------------------

    def navegar_agenda(self, data: date) -> bool:
        """Navega até a agenda do dia especificado."""
        # Tentar acessar a agenda via URL direta
        data_formatada = data.strftime("%Y-%m-%d")
        urls_possiveis = [
            f"{ICLINIC_URL}/agenda?date={data_formatada}",
            f"{ICLINIC_URL}/schedule?date={data_formatada}",
            f"{ICLINIC_URL}/#/agenda?date={data_formatada}",
        ]

        for url in urls_possiveis:
            logger.info(f"Tentando acessar agenda: {url}")
            self.driver.get(url)
            self._pausa()

            pacientes = self._encontrar_elementos(SELETORES["lista_pacientes_agenda"])
            if pacientes:
                logger.info(f"Agenda encontrada com {len(pacientes)} pacientes")
                return True

        # Se URL direta não funcionou, tentar navegar pelo menu
        logger.info("Tentando navegar pelo menu...")
        link_agenda = self._esperar_elemento(SELETORES["link_agenda"])
        if link_agenda:
            link_agenda.click()
            self._pausa()

            # Definir a data
            seletor_data = self._esperar_elemento(SELETORES["seletor_data"])
            if seletor_data:
                seletor_data.clear()
                seletor_data.send_keys(data.strftime("%d/%m/%Y"))
                seletor_data.send_keys(Keys.RETURN)
                self._pausa()
                return True

        logger.warning(f"Não foi possível navegar até a agenda de {data_formatada}")
        return False

    def listar_pacientes_agenda(self) -> list[dict]:
        """Lista os pacientes da agenda atual."""
        pacientes = []
        elementos = self._encontrar_elementos(SELETORES["lista_pacientes_agenda"])

        for i, elem in enumerate(elementos):
            try:
                nome_elem = elem.find_elements(
                    By.CSS_SELECTOR,
                    SELETORES["nome_paciente_agenda"].split(",")[0].strip(),
                )
                nome = nome_elem[0].text.strip() if nome_elem else f"Paciente #{i+1}"

                pacientes.append({
                    "indice": i,
                    "nome": nome,
                    "elemento": elem,
                })
            except StaleElementReferenceException:
                logger.warning(f"Elemento do paciente #{i+1} ficou obsoleto")
                continue

        logger.info(f"Encontrados {len(pacientes)} pacientes na agenda")
        return pacientes

    # ----------------------------------------------------------------
    # VERIFICAÇÃO DO PRONTUÁRIO
    # ----------------------------------------------------------------

    def abrir_prontuario(self, paciente_elem) -> bool:
        """Abre o prontuário de um paciente a partir do elemento da agenda."""
        try:
            # Tentar clicar diretamente no elemento
            link = paciente_elem.find_elements(
                By.CSS_SELECTOR, SELETORES["link_prontuario"].split(",")[0].strip()
            )
            if link:
                link[0].click()
            else:
                paciente_elem.click()

            self._pausa()
            return True
        except Exception as e:
            logger.warning(f"Erro ao abrir prontuário: {e}")
            return False

    def verificar_tag_nota_fiscal(self) -> bool:
        """Verifica se o prontuário possui tag NF/Nota Fiscal."""
        area_tags = self._esperar_elemento(SELETORES["area_tags"], timeout=5)
        if not area_tags:
            return False

        tags = self._encontrar_elementos(SELETORES["tag_individual"])
        for tag in tags:
            texto = tag.text.strip().upper()
            for tag_nf in TAGS_NOTA_FISCAL:
                if tag_nf.upper() in texto:
                    logger.info(f"  Tag encontrada: '{tag.text.strip()}'")
                    return True

        return False

    def verificar_bioimpedancia(self, data_atendimento: date) -> bool:
        """Verifica se há PDF de bioimpedanciometria com data correspondente."""
        area_anexos = self._esperar_elemento(SELETORES["area_anexos"], timeout=5)
        if not area_anexos:
            return False

        anexos = self._encontrar_elementos(SELETORES["item_anexo"])
        for anexo in anexos:
            try:
                # Verificar nome do anexo
                nome_elems = anexo.find_elements(
                    By.CSS_SELECTOR,
                    SELETORES["nome_anexo"].split(",")[0].strip(),
                )
                nome = nome_elems[0].text.strip().lower() if nome_elems else ""

                # Verificar se é bioimpedância
                eh_bio = any(
                    termo.lower() in nome or termo.lower() in anexo.text.lower()
                    for termo in TERMOS_BIOIMPEDANCIA
                )
                if not eh_bio:
                    continue

                # Verificar data do anexo
                data_elems = anexo.find_elements(
                    By.CSS_SELECTOR,
                    SELETORES["data_anexo"].split(",")[0].strip(),
                )
                if data_elems:
                    texto_data = data_elems[0].text.strip()
                    if self._data_corresponde(texto_data, data_atendimento):
                        logger.info(f"  Bioimpedância encontrada: '{nome}' - {texto_data}")
                        return True
                else:
                    # Verificar data no texto completo do anexo
                    texto_completo = anexo.text.lower()
                    data_fmt1 = data_atendimento.strftime("%d/%m/%Y")
                    data_fmt2 = data_atendimento.strftime("%d/%m/%y")
                    if data_fmt1 in texto_completo or data_fmt2 in texto_completo:
                        logger.info(f"  Bioimpedância encontrada com data no texto")
                        return True

            except StaleElementReferenceException:
                continue

        return False

    def _data_corresponde(self, texto_data: str, data_esperada: date) -> bool:
        """Verifica se um texto de data corresponde à data esperada."""
        formatos = ["%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d", "%d-%m-%Y"]
        for fmt in formatos:
            try:
                data_anexo = datetime.strptime(texto_data[:10], fmt).date()
                if data_anexo == data_esperada:
                    return True
            except ValueError:
                continue

        # Tentar extrair data de texto livre (ex: "14/02/2026 às 14:41")
        import re
        padrao = r"(\d{2}/\d{2}/\d{4})"
        match = re.search(padrao, texto_data)
        if match:
            try:
                data_extraida = datetime.strptime(match.group(1), "%d/%m/%Y").date()
                return data_extraida == data_esperada
            except ValueError:
                pass

        return False

    def coletar_dados_paciente(self) -> dict:
        """Coleta nome, CPF e endereço do paciente do prontuário aberto."""
        dados = {"nome": "", "cpf": "", "endereco": ""}

        # Tentar coletar do prontuário atual
        nome_elem = self._esperar_elemento(SELETORES["campo_nome_completo"], timeout=5)
        if nome_elem:
            dados["nome"] = nome_elem.text.strip()

        cpf_elem = self._esperar_elemento(SELETORES["campo_cpf"], timeout=3)
        if cpf_elem:
            dados["cpf"] = cpf_elem.text.strip()

        endereco_elem = self._esperar_elemento(SELETORES["campo_endereco"], timeout=3)
        if endereco_elem:
            dados["endereco"] = endereco_elem.text.strip()

        # Se CPF ou endereço não encontrados, tentar abrir dados do paciente
        if not dados["cpf"] or not dados["endereco"]:
            link_dados = self._esperar_elemento(SELETORES["link_dados_paciente"], timeout=3)
            if link_dados:
                link_dados.click()
                self._pausa()

                cpf_elem = self._esperar_elemento(SELETORES["campo_cpf"], timeout=5)
                if cpf_elem:
                    dados["cpf"] = cpf_elem.text.strip()

                endereco_elem = self._esperar_elemento(SELETORES["campo_endereco"], timeout=3)
                if endereco_elem:
                    dados["endereco"] = endereco_elem.text.strip()

                # Voltar ao prontuário
                self.driver.back()
                self._pausa()

        return dados

    def voltar_agenda(self) -> None:
        """Volta para a agenda após verificar um prontuário."""
        botao = self._esperar_elemento(SELETORES["botao_voltar"], timeout=3)
        if botao:
            botao.click()
        else:
            self.driver.back()
        self._pausa()

    # ----------------------------------------------------------------
    # FLUXO PRINCIPAL DE PESQUISA
    # ----------------------------------------------------------------

    def pesquisar_data(self, data: date) -> ResultadoPesquisa:
        """Executa a pesquisa completa para uma data específica."""
        resultado = ResultadoPesquisa(data_pesquisa=data)

        # Navegar até a agenda
        if not self.navegar_agenda(data):
            resultado.erros.append(f"Não foi possível acessar a agenda de {data}")
            return resultado

        # Listar pacientes
        pacientes_agenda = self.listar_pacientes_agenda()
        resultado.total_pacientes_agenda = len(pacientes_agenda)

        if not pacientes_agenda:
            logger.info(f"Nenhum paciente encontrado na agenda de {data}")
            return resultado

        # Para cada paciente, verificar critérios
        for pac in pacientes_agenda:
            logger.info(f"Verificando paciente: {pac['nome']}")

            try:
                if not self.abrir_prontuario(pac["elemento"]):
                    resultado.erros.append(
                        f"Não foi possível abrir prontuário de {pac['nome']}"
                    )
                    continue

                tem_nf = self.verificar_tag_nota_fiscal()
                tem_bio = self.verificar_bioimpedancia(data)

                if tem_nf or tem_bio:
                    # Determinar critério
                    if tem_nf and tem_bio:
                        criterio = Criterio.AMBOS
                    elif tem_nf:
                        criterio = Criterio.NOTA_FISCAL
                    else:
                        criterio = Criterio.BIOIMPEDANCIA

                    # Coletar dados
                    dados = self.coletar_dados_paciente()
                    nome = dados["nome"] or pac["nome"]

                    registro = PacienteRegistro(
                        nome_completo=nome,
                        cpf=dados["cpf"],
                        endereco=dados["endereco"],
                        data_atendimento=data,
                        criterio=criterio,
                    )
                    resultado.pacientes_encontrados.append(registro)
                    logger.info(f"  ✓ Paciente registrado: {nome} ({criterio.value})")
                else:
                    logger.info(f"  ✗ Nenhum critério atendido")

                self.voltar_agenda()

            except Exception as e:
                logger.error(f"Erro ao processar {pac['nome']}: {e}")
                resultado.erros.append(f"Erro com {pac['nome']}: {str(e)}")
                # Tentar voltar para a agenda
                try:
                    self.voltar_agenda()
                except Exception:
                    self.navegar_agenda(data)

        return resultado
