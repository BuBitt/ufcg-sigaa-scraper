# SIGAA Grade Scraper

Um scraper para verificar e notificar quando novas notas forem adicionadas ao SIGAA da UFCG. Este projeto usa automação de navegador pra extrair notas do SIGAA e envia notificações via Telegram quando há mudanças, rodando automaticamente no GitHub Actions.

## Funcionalidades
- Faz login no SIGAA da UFCG.
- Extrai notas de todos os semestres disponíveis.
- Compara com um cache pra detectar novas notas ou alterações.
- Envia notificações pro Telegram (grupo e chat privado) com as mudanças.

## Pré-requisitos
- **Python 3.10+**
- Conta no SIGAA UFCG (usuário e senha).
- Bot do Telegram configurado com token e IDs de chat.

## Instalação
1. Clone o repositório

2. Instale as dependências:
   ```bash
   pip install playwright beautifulsoup4 lxml requests python-dotenv
   playwright install chromium
   ```

3. Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:
   ```
   SIGAA_USERNAME=seu_usuario
   SIGAA_PASSWORD=sua_senha
   TELEGRAM_BOT_TOKEN=seu_token
   TELEGRAM_GROUP_CHAT_ID=-123456789
   TELEGRAM_PRIVATE_CHAT_ID=987654321
   ```

## Uso Local
Rode o script manualmente:
```bash
python sigaa-scraper.py
```
O script vai fazer login no SIGAA, extrair as notas, comparar com o `grades_cache.json` e enviar notificações pro Telegram se houver mudanças.

## Uso no GitHub Actions
O projeto tá configurado pra rodar automaticamente no GitHub Actions.

1. Faça push do repositório pro GitHub.
2. Configure os **Secrets** no GitHub:
   - Vá em **Settings > Secrets and variables > Actions > Secrets**.
   - Adicione:
     - `SIGAA_USERNAME`
     - `SIGAA_PASSWORD`
     - `TELEGRAM_BOT_TOKEN`
     - `TELEGRAM_GROUP_CHAT_ID`
     - `TELEGRAM_PRIVATE_CHAT_ID`

3. O workflow roda todo dia às 12:00 UTC (veja `.github/workflows/main.yml`). Pra rodar manualmente, vá na aba **Actions** e clique em "Run workflow".

## Estrutura do Projeto
```
sigaa-grade-scraper/
├── .env              # Variáveis de ambiente (não versionado)
├── config.py         # Configurações gerais
├── sigaa-scraper.py  # Script principal
├── telegram_notifier.py  # Lógica de notificação pro Telegram
├── grades_cache.json  # Cache das notas (gerado automaticamente)
└── .github/
    └── workflows/
        └── main.yml  # Workflow do GitHub Actions
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
- **Chat Privado:** Mostra as disciplinas e as notas em negrito.

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

---

### **Instruções pra Adicionar**
1. Crie um arquivo chamado `README.md` na raiz do teu repositório.
2. Copie e cole o conteúdo acima.
3. Ajuste o link do `git clone` pra refletir o teu repositório real (`https://github.com/seu-usuario/seu-repositorio.git`).
4. Faça commit e push:
   ```bash
   git add README.md
   git commit -m "Adiciona README ao projeto"
   git push
   ```
