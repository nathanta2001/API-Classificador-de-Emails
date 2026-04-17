# 📧 Email Classifier AI API

Uma API desenvolvida para automatizar a triagem, classificação e resposta de e-mails, com foco especial no setor financeiro. O projeto utiliza o modelo **Gemini Flash** da Google para processamento de linguagem natural (NLP).

## 🚀 Tecnologias Utilizadas

* **Linguagem:** Python 3.x
* **Framework:** Flask
* **IA/LLM:** Google Generative AI (Gemini SDK)
* **Segurança & CORS:** Flask-CORS e Python-dotenv
* **Deployment Ready:** Configurado com Gunicorn para ambientes como Render ou Heroku.

## ✨ Funcionalidades Principais

* **Classificação Inteligente:** Categoriza e-mails automaticamente entre "Produtivo" (assuntos financeiros, suporte, compliance) e "Improdutivo" (spam, agradecimentos, newsletters).
* **Sugestão de Resposta:** Gera automaticamente uma resposta profissional em Português (BR) adaptada ao contexto do e-mail recebido.
* **Revisão de Texto:** Endpoint dedicado para edição e melhoria de textos com base em ações específicas.
* **Bot Keep-Alive:** Sistema integrado para manter a API ativa em serviços de hospedagem gratuita (como o Render).

## 🏗️ Como Funciona a IA

A API utiliza engenharia de prompt avançada para garantir que as respostas sigam regras rígidas de negócio:
* Identificação de termos-chave (faturas, chargeback, KYC, fraude).
* Saída estruturada estritamente em **JSON**.
* Uso de placeholders para protocolos e documentos.

## 🛠️ Instalação e Execução

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/nathanta2001/API-Classificador-de-Emails.git](https://github.com/nathanta2001/API-Classificador-de-Emails.git)
    ```

2.  **Crie e ative um ambiente virtual:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/Mac
    # ou
    venv\Scripts\activate     # Windows
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure as variáveis de ambiente:**
    Crie um arquivo `.env` na raiz e adicione sua chave:
    ```env
    GOOGLE_API_KEY=sua_chave_aqui
    ```

5.  **Inicie a aplicação:**
    ```bash
    python app.py
    ```

## 🔌 Endpoints da API

| Método | Endpoint | Descrição |
| :--- | :--- | :--- |
| `POST` | `/api/classificar` | Recebe um e-mail e retorna categoria e sugestão de resposta. |
| `POST` | `/api/revisar` | Altera um texto baseado em uma ação (ex: "tornar mais formal"). |
| `GET` | `/api/ping` | Endpoint de verificação de status (Health Check). |

---
Desenvolvido por [Nathan](https://github.com/nathanta2001) 🚀
