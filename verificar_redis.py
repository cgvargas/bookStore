# Arquivo: verificar_redis.py

import redis


def verificar_conexao_redis(host='localhost', port=6379, password=None):
    """
    Tenta conectar a um servidor Redis e envia um comando PING.

    Args:
        host (str): O host do servidor Redis.
        port (int): A porta do servidor Redis.
        password (str, optional): A senha para o servidor Redis, se houver.

    Returns:
        bool: True se a conexão for bem-sucedida e o PING retornar PONG, False caso contrário.
        str: Uma mensagem indicando o status da conexão.
    """
    try:
        # Tenta criar uma instância do cliente Redis
        r = redis.Redis(host=host, port=port, password=password, socket_connect_timeout=1)  # Timeout de 1 segundo

        # Tenta enviar um comando PING para o servidor
        # O comando ping() levanta redis.exceptions.ConnectionError se não conseguir conectar
        r.ping()
        return True, f"Conexão com Redis em {host}:{port} bem-sucedida! PING respondido com PONG."

    except redis.exceptions.ConnectionError as e:
        return False, f"Falha ao conectar ao Redis em {host}:{port}. Erro: {e}"
    except ImportError:
        return False, ("A biblioteca 'redis' não está instalada. "
                       "Por favor, instale-a com: pip install redis")
    except Exception as e:
        return False, f"Ocorreu um erro inesperado: {e}"


if __name__ == "__main__":
    # Você pode alterar os parâmetros de host, porta e senha conforme necessário
    conectado, mensagem = verificar_conexao_redis()

    print(mensagem)

    if conectado:
        print("O servidor Redis está acessível a partir do Python.")
    else:
        print("O servidor Redis não está acessível ou a biblioteca 'redis' não está instalada.")