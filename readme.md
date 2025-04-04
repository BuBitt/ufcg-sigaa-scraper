# SIGAA Grade Scraper

Um scraper para verificar e notificar automaticamente quando novas notas são adicionadas ao SIGAA da UFCG. Este projeto utiliza automação de navegador para extrair notas e envia notificações via Telegram quando mudanças são detectadas.

## Funcionalidades

- Login automático no SIGAA da UFCG
- Extração de notas de todos os componentes curriculares e turmas
- Sistema de cache para detectar novas notas ou alterações
- Notificações via Telegram (grupo e chat privado) com formato customizado
- Suporte a múltiplas turmas por componente curricular
- Tratamento de erros robusto para garantir execução contínua
- Execução automatizada via GitHub Actions

## Pré-requisitos

- **Python 3.10+**
- Conta no SIGAA UFCG (usuário e senha)
- Bot do Telegram configurado com token e IDs de chat

## Instalação

1. Clone o repositório:
   ```bash
   git clone https://github.com/seu-usuario/ufcg-sigaa-scraper.git
   cd ufcg-sigaa-scraper
   ```

2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

3. Configure o arquivo `.env` na raiz do projeto:
   ```
   SIGAA_USERNAME=seu_usuario
   SIGAA_PASSWORD=sua_senha
   TELEGRAM_BOT_TOKEN=seu_token
   TELEGRAM_GROUP_CHAT_ID=-1001234567890
   TELEGRAM_PRIVATE_CHAT_ID=1234567890
   ```

## Uso Local

Execute o script principal:
```bash
python main.py
```

O script realizará login no SIGAA, extrairá as notas, comparará com o cache anterior e enviará notificações caso detecte mudanças.

## Execução Automática (GitHub Actions)

O projeto está configurado para executar automaticamente no GitHub Actions:

1. Faça push do repositório para o GitHub
2. Configure os **Secrets** necessários no GitHub:
   - Acesse **Settings > Secrets and variables > Actions > Secrets**
   - Adicione os seguintes secrets:
     - `SIGAA_USERNAME`
     - `SIGAA_PASSWORD`
     - `TELEGRAM_BOT_TOKEN`
     - `TELEGRAM_GROUP_CHAT_ID`
     - `TELEGRAM_PRIVATE_CHAT_ID`

3. O workflow está configurado para executar a cada 10 minutos durante o horário comercial (6:00-23:59).
   Para executar manualmente, acesse a aba **Actions** e clique em "Run workflow".

## Estrutura do Projeto
```
sigaa-grade-scraper/
├── .env                      # Variáveis de ambiente (não versionado)
├── config.py                 # Configurações gerais
├── main.py                   # Script principal
├── scraper/                  # Lógica de extração e processamento
│   ├── browser.py            # Automação do navegador
│   ├── processor.py          # Processamento de componentes e turmas
│   └── extractor.py          # Extração de tabelas de notas
├── notification/             # Sistema de notificações
│   └── telegram.py           # Notificações via Telegram
├── utils/                    # Utilitários
│   ├── logger.py             # Configuração de logs
│   └── file_handler.py       # Manipulação de arquivos e cache
├── grades_cache.json         # Cache das notas (gerado automaticamente)
├── discipline_replacements.json # Substituições de nomes de disciplinas
└── .github/
    └── workflows/
        └── sigaa-notifier.yml # Workflow do GitHub Actions
```

## Dependências
- `playwright`: Automação do navegador.
- `beautifulsoup4`: Parseamento de HTML.
- `lxml`: Parser rápido pro BeautifulSoup (opcional, mas recomendado).
- `requests`: Envio de mensagens pro Telegram.
- `python-dotenv`: Carregamento do `.env`.

Instale com:
```bash
pip install -r requirements.txt
playwright install chromium
```

## Notificações
- **Grupo Telegram:** Lista os nomes das disciplinas com novas notas.
- **Chat Privado:** Mostra as disciplinas e as notas detalhadas.

Exemplo:
- Grupo:
  ```
  *Novas notas foram adicionadas ao SIGAA:*
  1. SAÚDE COLETIVA I
  2. SISTEMA DIGESTÓRIO
  ```
- Privado:
  ```
  *Novas notas foram adicionadas ao SIGAA:*
  1. SAÚDE COLETIVA I: *10*
  2. SISTEMA DIGESTÓRIO: *10*
  ```

## Contribuição
Sinta-se à vontade pra abrir issues ou pull requests com melhorias!

## Licença
Esse projeto é de código aberto e não tem licença formal definida ainda. Use como quiser!