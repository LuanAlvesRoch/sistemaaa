from flask import Flask, jsonify, request  # Importa os módulos necessários do Flask para criar o servidor web, lidar com requisições e respostas em JSON
from flask_cors import CORS  # Importa o CORS para permitir requisições de outros domínios, como do front-end Angular
import mysql.connector  # Importa o conector MySQL para se conectar ao banco de dados

app = Flask(__name__)  # Inicializa a aplicação Flask
print("Servidor Flask iniciado.")
CORS(app, resources={r"/*": {"origins": "http://localhost:4200"}})  # Permite todas as origens e métodos

# Configurações de conexão com o banco de dados MySQL
db_config_estoque = {
    'host': 'localhost',
    'user': 'root',
    'password': 'admin',
    'database': 'estoque'
}


# Função para conectar ao banco de dados
def get_db_connection():
    conn = mysql.connector.connect(**db_config_estoque)  # Cria a conexão usando as configurações definidas no 'db_config'
    return conn   # Retorna a conexão aberta

# ---------------------------------CRUD PRODUTOS----------------------------------------
@app.route('/produtos', methods=['GET'])
def list_produtos():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT 
            p.id,
            c.nome AS categoria_nome,
            p.nome AS produto_nome,
            p.descricao,
            p.quantidade_em_estoque,
            CONCAT('R$', FORMAT(p.preco, 2)) AS preco,
            p.imposto,
            CONCAT('R$', FORMAT(p.preco_final, 2)) AS preco_final
        FROM 
            produtos p
         
        LEFT JOIN categoria c ON p.categoria_id = c.id;
    """
    cursor.execute(query)
    produtos = cursor.fetchall()
    cursor.close()
    conn.close()
    print(produtos)
    return jsonify(produtos), 200

@app.route('/produtos/<int:id>', methods=['GET'])                   #GET COM ID
def get_produto(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    query = """
        SELECT 
            p.id,
            c.nome AS categoria_nome,
            p.nome AS produto_nome,
            p.descricao,
            p.quantidade_em_estoque,
            p.preco,  -- Retornar como número
            p.imposto,
            p.preco_final  -- Retornar como número
        FROM 
            produtos p
        LEFT JOIN categoria c ON p.categoria_id = c.id
        WHERE p.id = %s;  -- Filtrando pelo ID do produto
    """
    
    cursor.execute(query, (id,))  # Passando o ID como parâmetro
    produto = cursor.fetchone()  # Usando fetchone para obter um único produto
    cursor.close()
    conn.close()
    
    if produto is None:
        return jsonify({"error": "Produto não encontrado."}), 404

    # Formatar os preços apenas ao enviar a resposta, se necessário
    produto['preco'] = f'R${produto["preco"]:.2f}'
    produto['preco_final'] = f'R${produto["preco_final"]:.2f}'
    
    return jsonify(produto), 200


@app.route('/produtos', methods=['POST'])
def create_produto():
    data = request.get_json()
    nome = data.get('nome')
    descricao = data.get('descricao')
    preco = data.get('preco')
    imposto = data.get('imposto')
    quantidade_em_estoque = data.get('quantidade_em_estoque', 0)
    categoria_id = data.get('categoria_id')
    if not all([nome, preco, imposto, categoria_id]):
        return jsonify({'erro': 'Os campos nome, preco, imposto e categoria_id são obrigatórios'}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """INSERT INTO produtos 
               (nome, descricao, preco, imposto, quantidade_em_estoque, categoria_id) 
               VALUES (%s, %s, %s, %s, %s, %s)"""
    cursor.execute(query, (nome, descricao, preco, imposto, quantidade_em_estoque, categoria_id))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'mensagem': 'Produto criado com sucesso!'}), 201

@app.route('/produtos/<int:id>', methods=['PUT'])
def update_produto(id):
    data = request.get_json()
    nome = data.get('nome')
    descricao = data.get('descricao')
    preco = data.get('preco')
    imposto = data.get('imposto')
    quantidade_em_estoque = data.get('quantidade_em_estoque', 0)
    categoria_id = data.get('categoria_id')

    if not all([nome, preco, imposto, categoria_id]):
        return jsonify({'erro': 'Os campos nome, preco, imposto e categoria_id são obrigatórios'}), 400

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Verificar se o produto existe
        cursor.execute("SELECT * FROM produtos WHERE id = %s", (id,))
        produto = cursor.fetchone()
        if produto is None:
            return jsonify({'erro': 'Produto não encontrado'}), 404

        query = """UPDATE produtos SET 
                   nome = %s, descricao = %s, preco = %s, imposto = %s,  
                   quantidade_em_estoque = %s, categoria_id = %s 
                   WHERE id = %s"""
        cursor.execute(query, (nome, descricao, preco, imposto, quantidade_em_estoque, categoria_id, id))
        conn.commit()

        return jsonify({'mensagem': 'Produto atualizado com sucesso!'}), 200

    except mysql.connector.Error as e:
        print(f"Erro: {e}")
        return jsonify({'erro': 'Erro ao atualizar o produto. Tente novamente.'}), 500

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

@app.route('/produtos/<int:id>', methods=['DELETE'])
def delete_produto(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "DELETE FROM produtos WHERE id = %s"
    cursor.execute(query, (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'mensagem': 'Produto deletado com sucesso!'}), 200

# ---------------------------------CRUD CATEGORIAS----------------------------------------

@app.route('/categoria', methods=['GET'])  # Define a rota '/categoria' que será acessada via o método GET
def list_categoria():  # Define a função que será executada quando a rota '/categoria' for acessada
    conn = get_db_connection()  # Chama a função para abrir uma conexão com o banco de dados
    cursor = conn.cursor(dictionary=True)  # Cria um cursor para executar comandos SQL; 'dictionary=True' faz com que os resultados sejam retornados como dicionários
    query = "SELECT * FROM categoria"  # Define a query SQL que seleciona todos os registros da tabela 'categoria'
    cursor.execute(query)  # Executa a query no banco de dados
    categoria = cursor.fetchall()  # Busca todos os resultados da query e armazena na variável 'categoria'
    cursor.close()  # Fecha o cursor para liberar os recursos
    conn.close()  # Fecha a conexão com o banco de dados
    return jsonify(categoria), 200  # Retorna os resultados da query em formato JSON e com status HTTP 200 (sucesso)


@app.route('/categoria/<int:id>', methods=['GET'])
def get_categoria(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM categoria WHERE id = %s"
    cursor.execute(query, (id,))
    categoria = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if categoria is None:
        return jsonify({"error": "Categoria não encontrada"}), 404
    
    return jsonify(categoria), 200

@app.route('/categoria', methods=['POST'])
def create_categoria():
    data = request.get_json()  # Extrai os dados da requisição no formato JSON
    nome = data.get('nome')  # Busca o valor do campo 'nome' dentro do JSON recebido
    if not nome: 
        return jsonify({'erro': 'O campo nome é obrigatório'}), 400   # Verifica se o nome foi enviado na requisição, se não, retorna um erro 400 (Bad Request)
    conn = get_db_connection()  # Abre a conexão com o banco de dados
    cursor = conn.cursor()  # Cria um cursor para executar comandos SQL
    query = "INSERT INTO categoria (nome) VALUES (%s)"  # Query SQL que insere o nome da nova categoria na tabela 'categoria'
    cursor.execute(query, (nome,))  # Executa a query substituindo o '%s' pelo valor da variável 'nome'
    conn.commit()  # Confirma (commit) a transação no banco de dados para salvar as mudanças
    cursor.close()  # Fecha o cursor
    conn.close()   # Fecha a conexão com o banco de dados
    return jsonify({'mensagem': 'Categoria criada com sucesso!'}), 201   # Retorna uma resposta em JSON com uma mensagem de sucesso e o status HTTP 201 (Created)

@app.route('/categoria/<int:id>', methods=['PUT'])
def update_categoria(id):
    data = request.get_json()  # Extrai os dados da requisição no formato JSON
    nome = data.get('nome')  # Busca o valor do campo 'nome' dentro do JSON recebido
    if not nome:
        return jsonify({'erro': 'O campo nome é obrigatório'}), 400  # Verifica se o nome foi enviado na requisição, se não, retorna um erro 400 (Bad Request)
    conn = get_db_connection()  # Abre a conexão com o banco de dados
    cursor = conn.cursor()  # Cria um cursor para executar comandos SQL
    query = "UPDATE categoria SET nome = %s WHERE id = %s"  # Query SQL que atualiza o nome da categoria na tabela 'categoria'
    cursor.execute(query, (nome, id))  # Executa a query substituindo o '%s'
    conn.commit()  # Confirma (commit) a transação no banco de dados para salvar as mudanças
    cursor.close()  # Fecha o cursor
    conn.close()   # Fecha a conexão com o banco de dados
    return jsonify({'mensagem': 'Categoria atualizado com sucesso!'}), 200

@app.route('/categoria/<int:id>', methods=['DELETE'])
def delete_categoria(id):
    conn = get_db_connection()  # Abre a conexão com o banco de dados
    cursor = conn.cursor()  # Cria um cursor para executar comandos SQL
    query = "DELETE FROM categoria WHERE id = %s"  # Query SQL que deleta a categoria na tabela 'categoria'
    cursor.execute(query, (id,))  # Executa a query substituindo o '%s'
    conn.commit()  # Confirma (commit) a transação no banco de dados para salvar as mudanças
    cursor.close()  # Fecha o cursor
    conn.close()   # Fecha a conexão com o banco de dados
    return jsonify({'mensagem': 'Categoria deletada com sucesso!'}), 200


if __name__ == '__main__':  # Iniciar o servidor Flask
    app.run(debug=True)

