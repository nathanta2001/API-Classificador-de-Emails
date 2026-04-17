# 📧 Email Classifier API

Uma API para a classificação e processamento de e-mails. Este projeto foi desenvolvido com foco em performance, manutenibilidade e padrões de design modernos, servindo como uma solução eficiente para triagem automática de mensagens.

## 🚀 Tecnologias Utilizadas

* **Runtime:** Node.js
* **Linguagem:** TypeScript
* **Framework:** Express
* **Validação:** Zod / Joi
* **Documentação:** Swagger UI (OpenAPI)
* **Testes:** Vitest / Jest

## ✨ Funcionalidades

* [ ] **Classificação Automática:** Identificação de categorias de e-mail (Spam, Importante, Comercial, etc).
* [ ] **Parsing de Dados:** Extração inteligente de metadados de corpos de e-mail complexos.
* [ ] **Segurança:** Middlewares de autenticação e sanitização de inputs.
* [ ] **Logs e Monitoramento:** Rastreabilidade de requisições e erros.

## 🏗️ Estrutura do Projeto

O projeto segue princípios de **Clean Architecture**, dividindo responsabilidades entre:
* `src/entities`: Regras de negócio puras.
* `src/use-cases`: Fluxos de aplicação.
* `src/http`: Adaptadores de entrada (Controllers e Routes).

## 🛠️ Como Executar o Projeto

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/Nathanta2001/API-Classificador-de-Emails.git](https://github.com/Nathanta2001/API-Classificador-de-Emails.git)
    ```
2.  **Instale as dependências:**
    ```bash
    npm install
    # ou
    yarn install
    ```
3.  **Configure as variáveis de ambiente:**
    Crie um arquivo `.env` seguindo o modelo do `.env.example`.
4.  **Inicie a aplicação:**
    ```bash
    npm run dev
    ```

## 📖 Documentação (Swagger)

Com a API rodando, você pode acessar a documentação interativa em:
`http://localhost:3333/docs`

---
Desenvolvido por [Nathan](https://github.com/Nathanta2001) 🚀
