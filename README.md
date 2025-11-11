# 📧 Classificador Inteligente de Emails (IA)

Este projeto oferece uma API em Python para **classificação automática de emails** usando **IA** 
  
O sistema analisa o conteúdo da mensagem, identifica se o email é **Produtivo** (requer ação) ou **Improdutivo** (sem necessidade de resposta), e pode gerar automaticamente uma **resposta apropriada**.

---

## 🚀 Tecnologias Utilizadas

| Tecnologia | Função |
|---|---|
| Python | Linguagem principal |
| Flask | API REST |
| Google Gemini (Generative AI) | Modelo de IA para interpretação de texto |
| CORS | Permite integração com frontend (React, etc.) |
| dotenv | Gestão de variáveis de ambiente |

---

## 🧠 Funcionamento da Classificação

| Classificação | Significado |
|---|---|
| **Produtivo** | Exige ação, solicitação, dúvida, reclamação, pedido, etc. |
| **Improdutivo** | Não exige retorno. Ex: agradecimentos, frase motivacional, aviso geral. |

---

## 📡 Endpoint da API

### `POST /api/classificar`

#### Corpo da Requisição:
```json
{
  "email_texto": "Olá, gostaria de saber o status da minha solicitação."
}
