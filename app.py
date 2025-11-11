from flask import Flask, jsonify, request
from dotenv import load_dotenv
import os
import google.generativeai as genai
import json
from flask_cors import CORS

# Carrega variáveis do arquivo .env
load_dotenv()
app = Flask(__name__)
CORS(app)  # Para requisições externas


"""
Configuração da API Gemini. Certifique-se de definir a variável de ambiente
GOOGLE_API_KEY com sua chave de API do Google Cloud antes de executar o aplicativo.
"""
try:
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model = genai.GenerativeModel("gemini-2.5-flash")

except AttributeError as e:
    print(f"Erro: {e}")
    print("Erro: A variável de ambiente GOOGLE_API_KEY não foi encontrada.")
    exit()


# Prompt principal usado para classificar e gerar resposta automática de emails
PROMPT = """
Você é um assistente especializado em classificação e resposta de emails. Sua tarefa é: (1) Classificar o email recebido como Produtivo ou Improdutivo, e (2) Gerar uma resposta automática apropriada à classificação.

Definições:
Produtivo: O email exige ação, tomada de decisão ou resposta específica. Exemplos: dúvidas sobre sistema, solicitações de suporte, pedidos de status, envio de documentos, reclamações.
Improdutivo: O email não exige ação ou resposta obrigatória. Exemplos: agradecimentos, mensagens motivacionais, cumprimentos, avisos informativos sem solicitação.

Formato de Resposta (retorne exatamente em JSON):
{
"classificacao": "Produtivo ou Improdutivo",
"resposta_automatica": "Texto da resposta sugerida ou vazio"
}

Regras:
Se a classificação for Produtivo, gere uma resposta educada e direta, solicitando informações ou oferecendo solução.
Se for Improdutivo, a resposta pode ser curta ou até vazia.
Não inclua explicações fora do JSON.
Não acrescente nada além do JSON.

Email para análise: [email_aqui]
"""


@app.route('/api/classificar', methods=['POST'])
def classificarEmail():
    """
    Classifica o texto de um email como 'Produtivo' ou 'Improdutivo',
    e retorna uma resposta gerada automaticamente.

    Retorno:
        JSON contendo:
        - categoria (str): Classificação do email.
        - resposta (str): Texto sugerido para resposta automática.
    """

    # Obtém o JSON enviado pelo frontend
    dados = request.json
    if not dados:
        return jsonify({'error': 'Requisição deve conter JSON (verifique o Content-Type)'}), 400

    # Extrai o texto do email
    texto_do_email = dados.get('email_texto')
    if not texto_do_email:
        return jsonify({'error': 'A chave "email_texto" é obrigatória.'}), 400

    print(f"Email recebido: {texto_do_email}")

    try:
        # Prepara o prompt para o modelo
        promptFinal = PROMPT.replace("[email_aqui]", texto_do_email)
        response = model.generate_content(promptFinal)

        # Limpeza do retorno da IA
        textoIA = response.text
        textoJson = textoIA.strip().replace("```json", "").replace("```", "").strip()

        print(f"Resposta da IA: {textoJson}")

        resultadoJson = json.loads(textoJson)

        # Retorno formatado para o frontend
        return jsonify({
            "categoria": resultadoJson.get("classificacao"),
            "resposta": resultadoJson.get("resposta_automatica")
        })

    except Exception as e:
        print(f"Erro ao processar o email: {e}")
        return jsonify({
            'categoria': 'Erro',
            'resposta': f'Erro ao processar: {str(e)}'
        }), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
