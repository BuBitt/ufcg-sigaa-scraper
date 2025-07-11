# 🎓 UFCG SIGAA Grade Scraper

Um sistema automatizado de monitoramento de notas para a plataforma SIGAA da UFCG. Este projeto usa automação de navegador para extrair notas e envia notificações via Telegram quando mudanças são detectadas, com execução automática via GitHub Actions.

## ✨ Funcionalidades

- **Login Automatizado no SIGAA**: Autenticação segura com o sistema SIGAA da UFCG
- **Extração de Notas**: Extração abrangente de notas de todos os semestres disponíveis
- **Detecção de Mudanças**: Comparação inteligente com dados em cache para identificar notas novas ou modificadas
- **Notificações Telegram**: Sistema duplo de notificação (grupo e chat privado) com mensagens formatadas
- **Integração GitHub Actions**: Execução automatizada a cada 15 minutos
- **Tratamento Robusto de Erros**: Logging abrangente e mecanismos de recuperação de erros

## 📋 Pré-requisitos

- **Python 3.10+**
- Conta do SIGAA UFCG (usuário e senha)
- Bot do Telegram com token e IDs de chat configurados
- Conta no GitHub (para execução automatizada)

## 🚀 Instalação

### 1. Clonar o Repositório

```bash
git clone <url-do-repositorio>
cd ufcg-sigaa-scraper
```

### 2. Instalar Dependências

```bash
pip install playwright beautifulsoup4 lxml requests python-dotenv
playwright install chromium
```

### 3. Configuração do Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
# Credenciais do SIGAA
SIGAA_USERNAME=seu_usuario
SIGAA_PASSWORD=sua_senha

# Configuração do Telegram
TELEGRAM_BOT_TOKEN=seu_token_do_bot
TELEGRAM_GROUP_CHAT_ID=-123456789
TELEGRAM_PRIVATE_CHAT_ID=987654321
```

#### Obtendo Credenciais do Telegram

1. **Token do Bot**: Envie mensagem para [@BotFather](https://t.me/botfather) no Telegram e crie um novo bot
2. **IDs dos Chats**: 
   - Para grupos: Adicione seu bot ao grupo e use [@userinfobot](https://t.me/userinfobot)
   - Para chats privados: Envie mensagem para seu bot e use a API do Telegram

## 💻 Uso Local

Execute o scraper manualmente:

```bash
python sigaa-scraper.py
```

A aplicação irá:
1. Fazer login no SIGAA usando suas credenciais
2. Extrair notas de todos os semestres disponíveis
3. Comparar com dados em cache (`grades_cache.json`)
4. Enviar notificações do Telegram para quaisquer mudanças detectadas
5. Atualizar o cache com novos dados

## ☁️ Implantação no GitHub Actions

### 1. Configuração do Repositório

1. Faça push do seu código para o GitHub
2. Navegue para **Settings → Secrets and variables → Actions → Secrets**

### 2. Configurar Secrets

Adicione os seguintes secrets do repositório:

| Nome do Secret | Descrição |
|----------------|-----------|
| `SIGAA_USERNAME` | Seu usuário do SIGAA |
| `SIGAA_PASSWORD` | Sua senha do SIGAA |
| `TELEGRAM_BOT_TOKEN` | Token do seu bot do Telegram |
| `TELEGRAM_GROUP_CHAT_ID` | ID do chat do grupo para notificações |
| `TELEGRAM_PRIVATE_CHAT_ID` | ID do chat privado para notificações |

### 3. Execução Automatizada

- **Automática**: Executa a cada 15 minutos (configurável em `.github/workflows/main.yml`)
- **Manual**: Vá para a aba **Actions** e clique em "Run workflow"

## 📁 Estrutura do Projeto

```
ufcg-sigaa-scraper/
├── 📄 .env                    # Variáveis de ambiente (não versionado)
├── ⚙️ config.py              # Constantes de configuração da aplicação
├── 🤖 sigaa-scraper.py       # Aplicação principal do scraper
├── 📱 telegram_notifier.py   # Manipulador de notificações do Telegram
├── 💾 grades_cache.json      # Cache de notas (gerado automaticamente)
├── 📝 script.log            # Logs da aplicação
├── 📋 requirements.txt       # Dependências do Python
├── 📖 README.md             # Este arquivo
└── 🔄 .github/
    └── workflows/
        └── main.yml          # Workflow do GitHub Actions
```

## 📦 Dependências

| Pacote | Propósito |
|--------|-----------|
| `playwright` | Framework de automação de navegador |
| `beautifulsoup4` | Análise de HTML e extração de dados |
| `lxml` | Parser XML/HTML rápido (opcional mas recomendado) |
| `requests` | Cliente HTTP para API do Telegram |
| `python-dotenv` | Gerenciamento de variáveis de ambiente |

Instale todas as dependências:

```bash
pip install -r requirements.txt
playwright install chromium
```

## 📱 Exemplos de Notificação

### Notificação do Chat em Grupo
```
*Novas notas foram adicionadas ao SIGAA:*

1. SAÚDE COLETIVA I
2. SISTEMA DIGESTÓRIO
3. METODOLOGIA CIENTÍFICA
```

### Notificação do Chat Privado
```
*Novas notas foram adicionadas ao SIGAA:*

1. SAÚDE COLETIVA I: *9.5*
2. SISTEMA DIGESTÓRIO: *9.7*, *9.2*
3. METODOLOGIA CIENTÍFICA: *10.0*
```

## 🔧 Opções de Configuração

### Configurações do Navegador
- `HEADLESS_BROWSER`: Executar navegador sem interface gráfica (padrão: `True`)
- `TIMEOUT_DEFAULT`: Timeout padrão para operações (padrão: `30000ms`)
- `VIEWPORT_WIDTH/HEIGHT`: Dimensões da janela do navegador

### Configurações de Notificação
- `SEND_TELEGRAM_GROUP`: Habilitar notificações do grupo
- `SEND_TELEGRAM_PRIVATE`: Habilitar notificações do chat privado

### Caminhos de Arquivos
- `CACHE_FILENAME`: Localização do arquivo de cache de notas
- `LOG_FILENAME`: Localização do arquivo de log da aplicação

## 🐛 Solução de Problemas

### Problemas Comuns

1. **Falhas de Login**
   - Verifique as credenciais do SIGAA no `.env`
   - Verifique se o SIGAA está acessível
   - Revise os logs para mensagens de erro específicas

2. **Notificações do Telegram Não Enviadas**
   - Valide o token do bot e IDs dos chats
   - Certifique-se de que o bot tem permissão para enviar mensagens
   - Verifique a conectividade de rede

3. **Nenhuma Nota Extraída**
   - Verifique se a estrutura da página do SIGAA não mudou
   - Verifique por CAPTCHA ou medidas de segurança adicionais
   - Revise a lógica de análise do HTML

### Modo de Debug

Habilite logging detalhado definindo `LOG_LEVEL = logging.DEBUG` em `config.py`.

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para enviar issues, solicitações de funcionalidades ou pull requests.

### Configuração de Desenvolvimento

1. Faça fork do repositório
2. Crie uma branch de funcionalidade
3. Faça suas mudanças com documentação adequada
4. Adicione testes se aplicável
5. Envie um pull request

## 📄 Licença

Este projeto é de código aberto. Sinta-se livre para usar, modificar e distribuir conforme necessário.

## ⚠️ Aviso Legal

Esta ferramenta é apenas para uso educacional e pessoal. Certifique-se de estar em conformidade com os termos de serviço da UFCG e use de forma responsável.
