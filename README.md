# SIGAA Grade Scraper

Um scraper moderno e robusto para extrair notas do Sistema Integrado de Gestão de Atividades Acadêmicas (SIGAA) da UFCG.

## Funcionalidades

- **Duas estratégias de extração configuráveis**
  - `menu_ensino`: Acesso direto via menu "Ensino > Consultar Minhas Notas" (mais rápido)
  - `materia_individual`: Navegação matéria por matéria (método original)

- **Arquitetura modular e robusta**
  - Serviços especializados para cada funcionalidade
  - Sistema de logging avançado com medição de performance
  - Cache inteligente para evitar reprocessamento
  - Comparação automática de mudanças

- **Notificações inteligentes**
  - Integração com Telegram para alertas de novas notas
  - Detecção automática de mudanças
  - Formatação clara das notificações

- **Exportação flexível**
  - Formato JSON estruturado
  - Opção de exportação para CSV
  - Backup automático de dados

## Arquitetura

```
src/
├── config/          # Configurações centralizadas
│   └── settings.py  # Classe Config com todas as configurações
├── core/            # Lógica principal da aplicação
│   └── sigaa_scraper.py  # Orquestrador principal
├── services/        # Serviços especializados
│   ├── auth_service.py      # Autenticação no SIGAA
│   ├── navigation_service.py # Navegação entre páginas
│   ├── grade_extractor.py   # Extração de notas
│   ├── cache_service.py     # Gerenciamento de cache
│   └── comparison_service.py # Comparação de dados
├── notifications/   # Sistema de notificações
│   └── telegram_notifier.py # Notificações via Telegram
└── utils/          # Utilitários e helpers
    └── logger.py   # Sistema de logging avançado
```

## Instalação

### 1. Clone o repositório
```bash
git clone <url-do-repositorio>
cd ufcg-sigaa-scraper
```

### 2. Crie um ambiente virtual
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
# Credenciais do SIGAA (obrigatório)
SIGAA_USERNAME=seu_usuario
SIGAA_PASSWORD=sua_senha

# Configuração do Telegram (opcional)
TELEGRAM_BOT_TOKEN=seu_token_do_bot
TELEGRAM_CHAT_ID=seu_chat_id

# Método de extração (opcional)
EXTRACTION_METHOD=menu_ensino  # ou materia_individual
```

## Como usar

### Execução básica
```bash
python main.py
```

### Execução com método específico
```bash
# Via variável de ambiente
EXTRACTION_METHOD=materia_individual python main.py

# Ou editando o arquivo config.py
```

## ⚙️ Configuração

### Métodos de extração

#### menu_ensino (Recomendado)
- **Vantagem**: Mais rápido e direto
- **Como funciona**: Navega diretamente para "Ensino > Consultar Minhas Notas"
- **Ideal para**: Uso regular e automático

#### materia_individual
- **Vantagem**: Mais detalhado, acesso matéria por matéria
- **Como funciona**: Navega pelo menu lateral, entrando em cada disciplina
- **Ideal para**: Quando precisa de informações específicas por disciplina

### Configuração do Telegram

1. Crie um bot com o @BotFather no Telegram
2. Obtenha o token do bot
3. Encontre seu Chat ID (pode usar @userinfobot)
4. Configure no arquivo `.env`

## Testes

O projeto inclui uma suíte completa de testes:

```bash
# Executar todos os testes
python tests/run_tests.py

# Executar testes específicos
python tests/run_tests.py test_config
python tests/run_tests.py test_services
python tests/run_tests.py test_integration
```

### Estrutura dos testes

- `test_config.py`: Testes de configuração e estrutura do projeto
- `test_services.py`: Testes dos serviços principais
- `test_integration.py`: Testes de integração do fluxo completo

## Saída de dados

### Cache (grades_cache.json)
```json
{
  "Disciplina1": [
    {
      "Unidade": "1",
      "Nota": "8.5",
      "_timestamp": "2024-01-01T10:00:00",
      "_disciplina": "Disciplina1"
    }
  ]
}
```

### Logs estruturados
```
2024-01-01 10:00:00 | INFO     | auth_service         | login               :45   | Realizando login no SIGAA
2024-01-01 10:00:02 | INFO     | grade_extractor      | extract_grades      :67   | Iniciando extração de notas
```

## Limitações e considerações

- O scraper depende da estrutura HTML do SIGAA, que pode mudar
- Requer credenciais válidas da UFCG
- Taxa de requisições limitada para evitar sobrecarga do servidor
- Testado especificamente com SIGAA da UFCG
