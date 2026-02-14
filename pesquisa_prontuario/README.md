# Pesquisa de Prontuário Médico - iClinic

Programa para pesquisar pacientes no prontuário do iClinic que possuam:
- Tag **"NF"** ou **"Nota Fiscal"** no prontuário
- PDF de **bioimpedanciometria** anexado com data correspondente ao atendimento

## Instalação

```bash
# 1. Instalar dependências Python
pip install -r pesquisa_prontuario/requirements.txt

# 2. Instalar Google Chrome (necessário para modo automático)
# Ubuntu/Debian:
# sudo apt install google-chrome-stable
# Ou baixe em: https://www.google.com/chrome/
```

## Configuração

Edite o arquivo `pesquisa_prontuario/config.py`:

1. Preencha `ICLINIC_EMAIL` e `ICLINIC_SENHA` com suas credenciais
2. Ajuste os **seletores CSS** conforme a interface real do iClinic (veja instruções no arquivo)

### Como descobrir os seletores CSS corretos

1. Abra `app.iclinic.com.br` no Chrome
2. Pressione **F12** para abrir o DevTools
3. Clique no ícone de cursor (canto superior esquerdo do DevTools)
4. Clique no elemento desejado na página
5. No painel Elements, clique com botão direito no HTML → **Copy → Copy selector**
6. Atualize o dicionário `SELETORES` em `config.py`

## Uso

### Modo Automático (Selenium)

```bash
# Pesquisar uma data específica
python -m pesquisa_prontuario.main --data 14/02/2026

# Pesquisar intervalo de datas
python -m pesquisa_prontuario.main --de 01/02/2026 --ate 14/02/2026

# Incluir finais de semana
python -m pesquisa_prontuario.main --de 01/02/2026 --ate 14/02/2026 --incluir-fds

# Exportar apenas CSV
python -m pesquisa_prontuario.main --data 14/02/2026 --formato csv
```

### Modo Manual

Permite digitar os dados diretamente no terminal (sem Selenium):

```bash
python -m pesquisa_prontuario.main --manual
python -m pesquisa_prontuario.main --manual --formato excel
```

## Formatos de Saída

- **CSV**: Separado por `;`, compatível com Excel (encoding UTF-8-BOM)
- **Excel**: Planilha formatada com abas "Resultados" e "Resumo"

Os arquivos são salvos na pasta `relatorios/`.

## Estrutura dos Dados Coletados

| Campo | Descrição |
|-------|-----------|
| Nome Completo | Nome do paciente |
| CPF | Documento do paciente |
| Endereço | Endereço cadastrado |
| Data do Atendimento | Data em que foi atendido |
| Critério Atendido | NF/Nota Fiscal, Bioimpedanciometria, ou Ambos |

## Arquivos

```
pesquisa_prontuario/
├── __init__.py        # Inicializador do pacote
├── main.py            # Script principal com CLI
├── config.py          # Configurações e seletores CSS
├── models.py          # Modelos de dados
├── scraper.py         # Automação Selenium
├── relatorio.py       # Geração de CSV/Excel
└── requirements.txt   # Dependências Python
```

## Observações

- Os **seletores CSS** em `config.py` são estimativas e **precisam ser verificados** na interface real do iClinic usando o DevTools do navegador (F12)
- O iClinic não possui API REST pública documentada para consulta de dados, por isso o programa usa automação de navegador (Selenium)
- Mantenha `HEADLESS = False` em `config.py` durante os primeiros testes para visualizar o que o programa está fazendo
- Nunca compartilhe o arquivo `config.py` com suas credenciais preenchidas
