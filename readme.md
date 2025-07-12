# SIGAA Grade Scraper v2.0

Um scraper moderno e refatorado para verificar e notificar automaticamente quando novas notas são adicionadas ao SIGAA da UFCG. Este projeto utiliza automação de navegador com arquitetura modular e suporte a múltiplos métodos de extração.

## ✨ Novidades v2.0

- **Arquitetura completamente refatorada** seguindo melhores práticas
- **Estrutura modular** com separação clara de responsabilidades
- **Dois métodos de extração** configuráveis
- **Sistema de logging avançado** com diferentes níveis
- **Gerenciamento robusto de configurações**
- **Serviços independentes** para máxima flexibilidade
- **Testes automatizados** de configuração

## Funcionalidades

- Login automático no SIGAA da UFCG
- **Dois métodos de extração de notas:**
  - **Menu Ensino** (recomendado): Acessa via menu Ensino > Consultar Minhas Notas - mais rápido e direto
  - **Matéria Individual**: Método original que acessa cada matéria separadamente via menu lateral
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
   EXTRACTION_METHOD=menu_ensino
   TELEGRAM_BOT_TOKEN=seu_token
   TELEGRAM_GROUP_CHAT_ID=-1001234567890
   TELEGRAM_PRIVATE_CHAT_ID=1234567890
   ```

## Configuração de Método de Extração

O sistema oferece dois métodos para extrair notas, configuráveis via `EXTRACTION_METHOD`:

### Menu Ensino (Recomendado)
```
EXTRACTION_METHOD=menu_ensino
```
- **Vantagens**: Mais rápido, acesso direto via menu
- **Como funciona**: Navega para Ensino > Consultar Minhas Notas
- **Ideal para**: Uso regular e automação

### Matéria Individual (Método Original)
```
EXTRACTION_METHOD=materia_individual
```
- **Vantagens**: Mais detalhado, acessa cada matéria separadamente
- **Como funciona**: Clica em cada componente curricular e acessa via menu lateral
- **Ideal para**: Quando o método do menu não funcionar

## Uso Local

### Execução Normal
```bash
python main.py
```

### Modo Debug (logging detalhado)
```bash
python main.py --debug
```

### Modo Teste (verificar configuração)
```bash
python main.py --test
```

### Teste da Estrutura Modular
```bash
python test_structure.py
```

O script realizará login no SIGAA, extrairá as notas usando o método configurado, comparará com o cache anterior e enviará notificações caso detecte mudanças.

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

## Estrutura do Projeto v2.0

```
sigaa-grade-scraper/
├── .env                          # Variáveis de ambiente (não versionado)
├── .env.example                  # Template de configuração
├── main.py                       # Ponto de entrada principal
├── src/                          # Código fonte modular
│   ├── config/                   # Configurações centralizadas
│   │   ├── __init__.py
│   │   └── settings.py           # Classe Config com todas as configurações
│   ├── core/                     # Lógica principal
│   │   ├── __init__.py
│   │   └── sigaa_scraper.py      # Classe principal do scraper
│   ├── services/                 # Serviços especializados
│   │   ├── __init__.py
│   │   ├── auth_service.py       # Autenticação no SIGAA
│   │   ├── navigation_service.py # Navegação (ambos os métodos)
│   │   ├── grade_extractor.py    # Extração de notas
│   │   ├── cache_service.py      # Gerenciamento de cache
│   │   └── comparison_service.py # Comparação de mudanças
│   ├── notifications/            # Sistema de notificações
│   │   ├── __init__.py
│   │   └── telegram_notifier.py  # Notificações via Telegram
│   └── utils/                    # Utilitários
│       ├── __init__.py
│       ├── logger.py             # Sistema de logging avançado
│       └── env_loader.py         # Carregamento de ambiente
├── logs/                         # Arquivos de log (gerado automaticamente)
├── grades_cache.json             # Cache das notas (gerado automaticamente)
├── discipline_replacements.json  # Substituições de nomes de disciplinas
├── test_structure.py             # Teste da estrutura modular
├── test_config.py                # Teste de configuração
└── .github/
    └── workflows/
        └── sigaa-notifier.yml     # Workflow do GitHub Actions
```

## Dependências

### Principais
- `playwright`: Automação do navegador
- `beautifulsoup4`: Parseamento de HTML
- `lxml`: Parser rápido para BeautifulSoup
- `requests`: Comunicação HTTP (Telegram)
- `python-dotenv`: Carregamento de variáveis de ambiente

### Desenvolvimento
- `pytest`: Framework de testes (opcional)

Instale com:
```bash
pip install -r requirements.txt
playwright install chromium
```

## Arquitetura v2.0

### Princípios de Design
- **Separação de Responsabilidades**: Cada módulo tem uma função específica
- **Inversão de Dependência**: Serviços são injetados e testáveis
- **Configuração Centralizada**: Todas as configurações em um local
- **Logging Estruturado**: Sistema de logs com diferentes níveis
- **Tratamento de Erros Robusto**: Falhas graciosamente com recuperação

### Serviços Principais

#### AuthService
- Gerencia autenticação no SIGAA
- Validação de credenciais
- Detecção de estado de login

#### NavigationService
- Suporta ambos os métodos de navegação
- Navegação inteligente com fallbacks
- Retorno seguro para página principal

#### GradeExtractor
- Extração de dados de HTML
- Organização por períodos/disciplinas
- Identificação automática de notas

#### CacheService
- Persistência de dados com metadados
- Sistema de backup automático
- Validação de integridade

#### ComparisonService
- Detecção inteligente de mudanças
- Normalização de estruturas diferentes
- Descrições detalhadas de alterações

#### TelegramNotifier
- Formatação especializada por tipo de chat
- Tratamento de erros de rede
- Teste de conectividade

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