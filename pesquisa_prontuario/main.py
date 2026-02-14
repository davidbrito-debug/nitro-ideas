#!/usr/bin/env python3
"""
Programa de Pesquisa de Prontuário Médico - iClinic

Pesquisa pacientes na agenda do iClinic por data e verifica se possuem:
  - Tag "NF" ou "Nota Fiscal" no prontuário
  - PDF de bioimpedanciometria com data correspondente ao atendimento

Uso:
  python -m pesquisa_prontuario.main --data 14/02/2026
  python -m pesquisa_prontuario.main --de 01/02/2026 --ate 14/02/2026
  python -m pesquisa_prontuario.main --manual
"""

import argparse
import logging
import sys
from datetime import date, datetime, timedelta

from pesquisa_prontuario.models import Criterio, PacienteRegistro, ResultadoPesquisa
from pesquisa_prontuario.relatorio import gerar_csv, gerar_excel, imprimir_resumo

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def parse_data(texto: str) -> date:
    """Converte texto para data."""
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(texto.strip(), fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Formato de data inválido: '{texto}'. Use DD/MM/AAAA.")


def gerar_datas(args) -> list[date]:
    """Gera lista de datas a pesquisar a partir dos argumentos."""
    if args.data:
        return [parse_data(args.data)]
    elif args.de and args.ate:
        inicio = parse_data(args.de)
        fim = parse_data(args.ate)
        if inicio > fim:
            inicio, fim = fim, inicio
        datas = []
        atual = inicio
        while atual <= fim:
            # Pular finais de semana (opcional)
            if not args.incluir_fds and atual.weekday() >= 5:
                atual += timedelta(days=1)
                continue
            datas.append(atual)
            atual += timedelta(days=1)
        return datas
    else:
        return [date.today()]


# ----------------------------------------------------------------
# MODO AUTOMÁTICO (SELENIUM)
# ----------------------------------------------------------------

def executar_automatico(datas: list[date], formato: str) -> None:
    """Executa pesquisa automática via Selenium."""
    from pesquisa_prontuario.scraper import IClinicScraper

    scraper = IClinicScraper()
    resultados = []

    try:
        scraper.iniciar_navegador()

        if not scraper.fazer_login():
            logger.error("Não foi possível fazer login. Abortando.")
            return

        for data_pesq in datas:
            logger.info(f"\nPesquisando data: {data_pesq.strftime('%d/%m/%Y')}")
            resultado = scraper.pesquisar_data(data_pesq)
            resultados.append(resultado)
            logger.info(resultado.resumo())

    except KeyboardInterrupt:
        logger.info("\nPesquisa interrompida pelo usuário.")
    except Exception as e:
        logger.error(f"Erro durante a pesquisa: {e}")
    finally:
        scraper.encerrar()

    if resultados:
        _exportar(resultados, formato)


# ----------------------------------------------------------------
# MODO MANUAL (ENTRADA VIA TERMINAL)
# ----------------------------------------------------------------

def executar_manual(formato: str) -> None:
    """Modo de entrada manual para registro dos dados."""
    print("\n" + "=" * 60)
    print("  MODO MANUAL - Pesquisa de Prontuário")
    print("  Digite os dados conforme encontrados no iClinic")
    print("=" * 60)

    resultados = []
    continuar_datas = True

    while continuar_datas:
        data_texto = input("\nData do atendimento (DD/MM/AAAA): ").strip()
        try:
            data_pesq = parse_data(data_texto)
        except ValueError as e:
            print(f"  Erro: {e}")
            continue

        resultado = ResultadoPesquisa(data_pesquisa=data_pesq)
        total_str = input("Quantos pacientes foram atendidos nesta data? ").strip()
        try:
            resultado.total_pacientes_agenda = int(total_str)
        except ValueError:
            resultado.total_pacientes_agenda = 0

        continuar_pacientes = True
        while continuar_pacientes:
            print(f"\n{'─' * 40}")
            print("  Novo paciente com critério atendido")
            print(f"{'─' * 40}")

            nome = input("  Nome completo: ").strip()
            if not nome:
                continuar_pacientes = False
                continue

            cpf = input("  CPF: ").strip()
            endereco = input("  Endereço: ").strip()

            print("  Critério atendido:")
            print("    1 - NF/Nota Fiscal")
            print("    2 - Bioimpedanciometria")
            print("    3 - Ambos")
            criterio_input = input("  Opção (1/2/3): ").strip()

            criterio_map = {
                "1": Criterio.NOTA_FISCAL,
                "2": Criterio.BIOIMPEDANCIA,
                "3": Criterio.AMBOS,
            }
            criterio = criterio_map.get(criterio_input, Criterio.NOTA_FISCAL)

            registro = PacienteRegistro(
                nome_completo=nome,
                cpf=cpf,
                endereco=endereco,
                data_atendimento=data_pesq,
                criterio=criterio,
            )
            resultado.pacientes_encontrados.append(registro)
            print(f"  Registrado: {nome} ({criterio.value})")

            resp = input("\n  Mais pacientes nesta data? (s/n): ").strip().lower()
            if resp != "s":
                continuar_pacientes = False

        resultados.append(resultado)

        resp = input("\nPesquisar outra data? (s/n): ").strip().lower()
        if resp != "s":
            continuar_datas = False

    if resultados:
        _exportar(resultados, formato)


# ----------------------------------------------------------------
# EXPORTAÇÃO
# ----------------------------------------------------------------

def _exportar(resultados: list[ResultadoPesquisa], formato: str) -> None:
    """Exporta os resultados no formato escolhido."""
    imprimir_resumo(resultados)

    if formato == "excel":
        caminho = gerar_excel(resultados)
    elif formato == "csv":
        caminho = gerar_csv(resultados)
    else:
        caminho_csv = gerar_csv(resultados)
        caminho_xlsx = gerar_excel(resultados)
        print(f"  Arquivos gerados:")
        print(f"    CSV:   {caminho_csv}")
        print(f"    Excel: {caminho_xlsx}")
        return

    print(f"  Arquivo gerado: {caminho}")


# ----------------------------------------------------------------
# CLI
# ----------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Pesquisa de Prontuário Médico - iClinic",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  %(prog)s --data 14/02/2026                    # Pesquisa uma data
  %(prog)s --de 01/02/2026 --ate 14/02/2026     # Pesquisa intervalo
  %(prog)s --manual                              # Entrada manual
  %(prog)s --manual --formato excel              # Manual + exporta Excel
        """,
    )

    grupo_data = parser.add_argument_group("Datas")
    grupo_data.add_argument(
        "--data", "-d",
        help="Data específica para pesquisar (DD/MM/AAAA)",
    )
    grupo_data.add_argument(
        "--de",
        help="Data inicial do intervalo (DD/MM/AAAA)",
    )
    grupo_data.add_argument(
        "--ate",
        help="Data final do intervalo (DD/MM/AAAA)",
    )
    grupo_data.add_argument(
        "--incluir-fds",
        action="store_true",
        default=False,
        help="Incluir finais de semana no intervalo",
    )

    parser.add_argument(
        "--manual", "-m",
        action="store_true",
        help="Modo manual: digitar dados manualmente via terminal",
    )

    parser.add_argument(
        "--formato", "-f",
        choices=["csv", "excel", "ambos"],
        default="ambos",
        help="Formato do relatório (padrão: ambos)",
    )

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("  PESQUISA DE PRONTUÁRIO MÉDICO - iClinic")
    print("=" * 60)

    if args.manual:
        executar_manual(args.formato)
    else:
        datas = gerar_datas(args)
        if not datas:
            print("Nenhuma data para pesquisar.")
            sys.exit(1)

        print(f"\n  Datas a pesquisar: {len(datas)}")
        for d in datas:
            print(f"    - {d.strftime('%d/%m/%Y')} ({d.strftime('%A')})")

        executar_automatico(datas, args.formato)


if __name__ == "__main__":
    main()
