# Google Maps Business Scraper

Ferramenta automatizada para coletar informações de negócios (nome, telefone e WhatsApp) no Google Maps para múltiplas cidades.

## Descrição

Este script Python utiliza Selenium para navegar automaticamente no Google Maps, buscar estabelecimentos de um tipo específico em várias cidades e extrair dados de contato, salvando em formato CSV e gerando links do WhatsApp.

## Funcionalidades

- Busca automatizada no Google Maps
- Suporte para múltiplas cidades
- Extração inteligente de números de telefone
- Geração automática de links do WhatsApp (formato 55XXXXXXXXXXX)
- Sistema anti-duplicação
- Salvamento incremental (a cada 50 registros)
- Exportação em CSV
- Geração de arquivo de configuração (.cfg)

## Requisitos

### Dependências Python

```bash
pip install selenium webdriver-manager
```

### Bibliotecas necessárias

- Python 3.6+
- Selenium
- WebDriver Manager
- Google Chrome instalado

## Instalação

1. Clone ou baixe o repositório
2. Instale as dependências:

```bash
pip install selenium webdriver-manager
```

3. Certifique-se de ter o Google Chrome instalado

## Configuração

Edite as seguintes variáveis no início do script:

```python
TIPO_NEGOCIO = "exemplo"              # Tipo de negócio a buscar (ex: "pizzaria", "dentista")
ARQUIVO_CSV = "resultados.csv"        # Nome do arquivo de saída
CFG_FILE = "lista.cfg"                # Arquivo com links do WhatsApp
MAX_RESULTS_POR_CIDADE = 1000         # Máximo de resultados por cidade
```

## Como Usar

1. Execute o script:

```bash
python script.py
```

2. Cadastre as cidades quando solicitado:
   - Digite o nome de cada cidade
   - Pressione ENTER após cada cidade
   - Digite `0` quando terminar

3. Confirme a execução digitando `S`

4. Aguarde o processamento (pode levar vários minutos por cidade)

## Arquivos Gerados

### `resultados.csv`
Contém as informações coletadas:
- Nome/LinkLocal
- Telefone
- Link WhatsApp
- Cidade

### `lista.cfg`
Lista com todos os links do WhatsApp no formato:
```
55XXXXXXXXXXX
55XXXXXXXXXXX
```

## Parâmetros Avançados

```python
SCROLL_ITER_BLOCK = 10        # Iterações de scroll por tentativa
MAX_EXPAND_TRIES = 120        # Tentativas máximas de expansão
SAVE_EVERY = 50               # Salvar a cada N registros
WAIT_SHORT = 1.0              # Espera curta (segundos)
WAIT_LONG = 3.0               # Espera longa (segundos)
NO_NEW_LIMIT = 3              # Limite de tentativas sem novos links
```

## Sistema Anti-Duplicação

O script verifica automaticamente:
- Números já existentes no CSV
- Links já cadastrados no arquivo .cfg
- Evita processamento redundante

## Tempo de Execução

O tempo varia conforme:
- Número de cidades
- Quantidade de resultados por cidade
- Velocidade da internet
- Tempo de resposta do Google Maps

**Estimativa**: 5-15 minutos por cidade (dependendo da quantidade de resultados)

## Avisos Importantes

1. **Uso Responsável**: Respeite os termos de serviço do Google
2. **Rate Limiting**: O script inclui delays para evitar bloqueios
3. **Conexão**: Mantenha uma conexão estável durante a execução
4. **Interrupções**: Caso interrompido, o script retoma de onde parou (evita duplicações)

## Solução de Problemas

### "Telefone não encontrado"
- Alguns estabelecimentos não possuem telefone público
- Normal em 20-40% dos casos

### "Erro ao abrir link"
- Verifique sua conexão com a internet
- O Google Maps pode estar temporariamente indisponível

### Script trava durante scroll
- Aumente os valores de `WAIT_SHORT` e `WAIT_LONG`
- Reduza `SCROLL_ITER_BLOCK`

## Estatísticas ao Final

O script exibe:
- Cidades processadas
- Total de números salvos
- Duplicados ignorados
- Localização dos arquivos gerados

## Contribuições

Sugestões e melhorias são bem-vindas! 

## Licença

Este projeto é fornecido "como está" para fins educacionais.

## Formato de Telefone

O script aceita e normaliza diversos formatos:
- (11) 98765-4321
- 11 98765-4321
- 1198765-4321
- 11987654321

Todos são convertidos para: `5511987654321` (formato WhatsApp)

---

**Desenvolvido com Python e Selenium**
