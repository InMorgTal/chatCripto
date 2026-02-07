import socket
import threading
import json

# Dizionari principali
utenti = {}          # username → connessione
gruppi = {}          # nome_gruppo → {membri:[], messaggi:[]}
chatPrivate = {}     # (utente1,utente2) → {membri:[], messaggi:[]}


# -------------------------
# Funzioni utili
# -------------------------

def creaChiaveChatPrivata(a, b):
    """Restituisce una tupla ordinata per identificare una chat privata."""
    return tuple(sorted([a, b]))


def riceviMsg(conn):
    """Riceve un messaggio JSON terminato da newline."""
    buffer = ""
    while True:
        data = conn.recv(2048).decode()
        if not data:
            return None
        buffer += data
        while "\n" in buffer:
            msg_str, buffer = buffer.split("\n", 1)
            try:
                return json.loads(msg_str)
            except:
                continue


def inviaMsg(conn, msg):
    """Invia un messaggio JSON con newline finale."""
    conn.sendall((json.dumps(msg) + "\n").encode())


# -------------------------
# Gestione messaggi
# -------------------------

def messaggio(msg):
    sorg = msg["sorgente"]
    dest = msg["destinazione"]

    # Caso GRUPPO
    if isinstance(dest, str) and dest in gruppi:
        gruppi[dest]["messaggi"].append(msg)
        for u in gruppi[dest]["membri"]:
            if u != sorg and u in utenti:
                inviaMsg(utenti[u], msg)
        return

    # Caso PRIVATO
    if isinstance(dest, str):
        dest = eval(dest)  # converte "('a','b')" → ('a','b')

    key = creaChiaveChatPrivata(dest[0], dest[1])

    if key not in chatPrivate:
        chatPrivate[key] = {"membri": list(key), "messaggi": []}

    chatPrivate[key]["messaggi"].append(msg)

    for u in key:
        if u != sorg and u in utenti:
            inviaMsg(utenti[u], msg)


def creaGruppo(msg):
    nome = msg["destinazione"]
    if nome not in gruppi:
        gruppi[nome] = {
            "membri": msg["membri"],
            "messaggi": []
        }


def iniziaConversazione(msg):
    a, b = msg["membri"]
    key = creaChiaveChatPrivata(a, b)
    if key not in chatPrivate:
        chatPrivate[key] = {
            "membri": [a, b],
            "messaggi": []
        }


def caricaChat(conn, msg):
    user = msg["sorgente"]
    lista = []

    # gruppi
    for nome, info in gruppi.items():
        if user in info["membri"]:
            lista.append(nome)

    # chat private
    for key, info in chatPrivate.items():
        if user in info["membri"]:
            lista.append(str(key))

    inviaMsg(conn, {"tipo": "caricaChat", "chat": lista})


def apriChat(conn, msg):
    nome = msg["chat"]

    # privata
    if nome.startswith("("):
        key = eval(nome)
        mess = chatPrivate[key]["messaggi"]
    else:
        mess = gruppi[nome]["messaggi"]

    inviaMsg(conn, {"tipo": "chatAperta", "messaggi": mess})


# -------------------------
# Gestione client
# -------------------------

def gestisciClient(conn):
    # Primo messaggio: username
    while True:
        msg = riceviMsg(conn)
        if msg is None:
            return
        username = msg["username"]
        if username not in utenti:
            break
        inviaMsg(conn, {"testo": "Username occupato"})

    utenti[username] = conn

    # Loop principale
    while True:
        msg = riceviMsg(conn)
        if msg is None:
            del utenti[username]
            return

        tipo = msg["tipo"]

        if tipo == "messaggio":
            messaggio(msg)
        elif tipo == "creaGruppo":
            creaGruppo(msg)
        elif tipo == "iniziaConv":
            iniziaConversazione(msg)
        elif tipo == "caricaChat":
            caricaChat(conn, msg)
        elif tipo == "apriChat":
            apriChat(conn, msg)


# -------------------------
# MAIN SERVER
# -------------------------

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('localhost', 5000))
    server.listen(20)

    print("Server attivo su porta 5000...")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=gestisciClient, args=(conn,), daemon=True).start()


if __name__ == "__main__":
    main()
