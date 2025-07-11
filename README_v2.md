# UFCG SIGAA Scraper - Versão 2.0

Um scraper automatizado para extrair e monitorar notas do sistema SIGAA da UFCG, agora com arquitetura modular e organizada.

## 🚀 Funcionalidades

- **Extração automatizada** de notas do SIGAA
- **Detecção inteligente** de mudanças nas notas
- **Notificações via Telegram** (grupo e privado)
- **Cache local** para otimização de performance
- **Arquitetura modular** para fácil manutenção
- **Logging detalhado** para debug e monitoramento

## 📁 Estrutura do Projeto

```
ufcg-sigaa-scraper/
├── main.py                          # Ponto de entrada principal
├── requirements.txt                 # Dependências do projeto
├── .env                            # Variáveis de ambiente (não incluído no git)
├── grades_cache.json              # Cache das notas (gerado automaticamente)
├── script.log                     # Arquivo de logs
├── old_files/                     # Arquivos da versão anterior (backup)
│   ├── config.py
│   ├── sigaa-scraper.py
│   └── telegram_notifier.py
└── src/                           # Código fonte modularizado
    ├── __init__.py                # Inicialização do pacote
    ├── config/                    # Configurações
    │   ├── __init__.py
    │   └── settings.py           # Configurações centralizadas
    ├── core/                      # Núcleo da aplicação
    │   ├── __init__.py
    │   └── sigaa_scraper.py      # Classe principal do scraper
    ├── services/                  # Serviços especializados
    │   ├── __init__.py
    │   ├── auth_service.py       # Autenticação no SIGAA
    │   ├── navigation_service.py # Navegação no sistema
    │   ├── grade_extractor.py    # Extração de notas
    │   ├── cache_service.py      # Gerenciamento de cache
    │   └── comparison_service.py # Comparação de notas
    ├── notifications/             # Sistema de notificações
    │   ├── __init__.py
    │   └── telegram_notifier.py  # Notificações via Telegram
    └── utils/                     # Utilitários
        ├── __init__.py
        ├── env_loader.py         # Carregamento de variáveis de ambiente
        └── logger.py             # Configuração de logging
```

## 🛠️ Instalação

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/seu-usuario/ufcg-sigaa-scraper.git
   cd ufcg-sigaa-scraper
   ```

2. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Instale o driver do Playwright:**
   ```bash
   playwright install chromium
   ```

4. **Configure as variáveis de ambiente:**
   ```bash
   cp .env.example .env
   # Edite o arquivo .env com suas credenciais
   ```

## ⚙️ Configuração

### Arquivo `.env`

```env
# Credenciais do SIGAA
SIGAA_USERNAME=seu_usuario
SIGAA_PASSWORD=sua_senha

# Configurações do Telegram Bot
TELEGRAM_BOT_TOKEN=seu_bot_token
TELEGRAM_GROUP_CHAT_ID=id_do_grupo
TELEGRAM_PRIVATE_CHAT_ID=seu_chat_id
```

### Configurações Principais

As configurações estão centralizadas em `src/config/settings.py`:

- **Navegador**: Modo headless, timeouts, viewport
- **Logging**: Nível de log, arquivo de saída
- **Cache**: Nome do arquivo de cache
- **Telegram**: Habilitação de notificações

## 🚀 Uso

### Execução Simples
```bash
python main.py
```

### Execução com Logging Detalhado
O sistema já inclui logging automático no arquivo `script.log` e no terminal.

## 📋 Módulos e Responsabilidades

### Core (`src/core/`)
- **SIGAAScraper**: Classe principal que coordena todo o processo

### Services (`src/services/`)
- **AuthService**: Gerencia autenticação no SIGAA
- **NavigationService**: Navega pelas páginas do sistema
- **GradeExtractor**: Extrai dados das notas do HTML
- **CacheService**: Gerencia cache local
- **ComparisonService**: Detecta mudanças entre extrações

### Notifications (`src/notifications/`)
- **TelegramNotifier**: Envia notificações via Telegram

### Utils (`src/utils/`)
- **env_loader**: Carrega variáveis de ambiente
- **logger**: Configura sistema de logging

## 🔧 Customização

### Adicionando Novos Serviços

1. Crie um novo arquivo em `src/services/`
2. Implemente a funcionalidade desejada
3. Importe e integre no `SIGAAScraper`

### Modificando Configurações

Edite `src/config/settings.py` para ajustar:
- Timeouts
- URLs
- Configurações de notificação
- Nível de logging

## 🐛 Problemas Conhecidos

- **Parser lxml**: Se não estiver disponível, o sistema usa `html.parser` (mais lento)
- **Modais do SIGAA**: Alguns modais podem aparecer ocasionalmente e são tratados automaticamente

## 📝 Logs

Os logs são salvos em:
- **Terminal**: Saída em tempo real
- **Arquivo**: `script.log` (sobrescrito a cada execução)

Níveis de log configurados em `Config.LOG_LEVEL`.

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 🔄 Changelog

### Versão 2.0.0
- ✨ **Arquitetura completamente modularizada**
- 🏗️ **Separação clara de responsabilidades**
- 📁 **Organização em módulos especializados**
- 🔧 **Configurações centralizadas**
- 📝 **Documentação atualizada**
- 🧹 **Código mais limpo e manutenível**

### Versão 1.x
- Funcionalidade básica de scraping
- Notificações via Telegram
- Sistema de cache simples

---

**Desenvolvido para a comunidade UFCG** 🎓
