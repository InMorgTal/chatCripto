import socket
import threading
import json
import cittografiaServer as cs

# Dizionari principali
utenti = {}          # username → connessione
gruppi = {}          # nome_gruppo → {membri:[], messaggi:[]}
chatPrivate = {}     # "user1_user2" → {membri:[], messaggi:[]}


# -------------------------
# Funzioni utili
# -------------------------

def creaIdChatPrivata(utente1, utente2):
    #"""Crea un ID ordinato per identificare una chat privata tra due utenti."""
    # Mette i nomi in ordine alfabetico e li unisce con _
    # Esempio: "mario" e "alice" → "alice_mario"
    if utente1 < utente2:
        return f"{utente1}_{utente2}"
    else:
        return f"{utente2}_{utente1}"


def riceviMsg(conn, key):
    #"""Riceve un messaggio JSON terminato da newline."""
    buffer = ""
    while True:
        try:
            tag = cs.recv_exact(conn, 16)
            nonce = cs.recv_exact(conn, 12)
            msg_len = int.from_bytes(cs.recv_exact(conn, 4), 'big')
            encrypted_msg = cs.recv_exact(conn, msg_len)  # Assicurati di leggere l'intera risposta cifrata
            data = key.decriptare(encrypted_msg, tag, nonce)
        except:
            # Errore nella ricezione (client disconnesso)
            return None
            
        if not data:
            return None
            
        buffer += data
        while "\n" in buffer:
            msg_str, buffer = buffer.split("\n", 1)
            try:
                return json.loads(msg_str)
            except:
                continue


def inviaMsg(conn, msg, key):
    #"""Invia un messaggio JSON con newline finale."""
    try:
        data = json.dumps(msg).encode()
        encrypted_text, tag, nonce = key.criptare(data)
        conn.sendall(tag)
        conn.sendall(nonce)
        conn.sendall(len(encrypted_text).to_bytes(4, 'big'))
        conn.sendall(encrypted_text)
    except:
        pass  # Client disconnesso, ignora


# -------------------------
# Gestione messaggi
# -------------------------

def messaggio(msg, key):
    mittente = msg["mittente"]
    destinazione = msg["destinazione"]
    tipo_chat = msg["tipo_chat"]  # "gruppo" o "privata"

    # Caso GRUPPO
    if tipo_chat == "gruppo":
        # Salva il messaggio nello storico del gruppo
        gruppi[destinazione]["messaggi"].append(msg)
        
        # Invia il messaggio a tutti i membri del gruppo (tranne il mittente)
        for utente in gruppi[destinazione]["membri"]:
            if utente != mittente and utente in utenti:
                inviaMsg(utenti[utente], msg, key)

    # Caso CHAT PRIVATA
    else:
        # Crea l'ID della chat privata
        chat_id = creaIdChatPrivata(mittente, destinazione)
        
        # Se la chat non esiste ancora, creala
        if chat_id not in chatPrivate:
            chatPrivate[chat_id] = {
                "membri": [mittente, destinazione],
                "messaggi": []
            }
        
        # Salva il messaggio
        chatPrivate[chat_id]["messaggi"].append(msg)
        
        # Invia il messaggio al destinatario
        if destinazione in utenti:
            inviaMsg(utenti[destinazione], msg)


def creaGruppo(msg):
    nome = msg["nome"]
    membri = msg["membri"]
    
    if nome not in gruppi:
        gruppi[nome] = {
            "membri": membri,
            "messaggi": []
        }
        print(f"[SERVER] Gruppo '{nome}' creato con membri: {membri}")


def iniziaConversazione(msg):
    utente1 = msg["utente1"]
    utente2 = msg["utente2"]
    
    chat_id = creaIdChatPrivata(utente1, utente2)
    
    if chat_id not in chatPrivate:
        chatPrivate[chat_id] = {
            "membri": [utente1, utente2],
            "messaggi": []
        }
        print(f"[SERVER] Chat privata creata tra '{utente1}' e '{utente2}'")


def caricaChat(conn, msg):
    utente = msg["utente"]
    lista = []

    # Aggiungi tutti i gruppi di cui fa parte
    for nome, info in gruppi.items():
        if utente in info["membri"]:
            lista.append({
                "nome": nome,
                "tipo": "gruppo"
            })

    # Aggiungi tutte le chat private
    for chat_id, info in chatPrivate.items():
        if utente in info["membri"]:
            # Trova l'altro utente nella chat
            altro_utente = info["membri"][0] if info["membri"][1] == utente else info["membri"][1]
            lista.append({
                "nome": altro_utente,
                "tipo": "privata"
            })

    inviaMsg(conn, {"tipo": "caricaChat", "chat": lista})


def apriChat(conn, msg):
    utente = msg["utente"]
    nome_chat = msg["nome_chat"]
    tipo_chat = msg["tipo_chat"]

    if tipo_chat == "gruppo":
        messaggi = gruppi[nome_chat]["messaggi"]
    else:
        # Crea l'ID della chat privata
        chat_id = creaIdChatPrivata(utente, nome_chat)
        messaggi = chatPrivate[chat_id]["messaggi"]

    inviaMsg(conn, {"tipo": "chatAperta", "messaggi": messaggi})


# -------------------------
# Gestione client
# -------------------------

def gestisciClient(conn, key):
    username = None
    try:
        # Primo messaggio: username
        while True:
            try:
                username = conn.recv(2048).decode()
                if not username:
                    # Client disconnesso prima di inviare username
                    return
            except:
                # Errore nella ricezione
                return
            
            if username not in utenti:
                try:
                    conn.sendall("OK".encode())
                    print(f"[SERVER] Utente '{username}' connesso")
                    break
                except:
                    # Errore nell'invio
                    return
            
            try:
                conn.sendall("Username occupato".encode())
            except:
                # Client disconnesso
                return

        utenti[username] = conn
        print(f"[SERVER] Utenti connessi: {len(utenti)} - {list(utenti.keys())}")

        # Loop principale: ricevi ed esegui comandi
        while True:
            msg = riceviMsg(conn, key)
            if msg is None:
                break

            tipo = msg["tipo"]

            if tipo == "messaggio":
                messaggio(msg, key)
            elif tipo == "creaGruppo":
                creaGruppo(msg)
            elif tipo == "iniziaConv":
                iniziaConversazione(msg)
            elif tipo == "caricaChat":
                caricaChat(conn, msg)
            elif tipo == "apriChat":
                apriChat(conn, msg)
                
    finally:
        # Quando il client si disconnette, pulisci tutto
        if username and username in utenti:
            del utenti[username]
            print(f"[SERVER] Utente '{username}' disconnesso")
            print(f"[SERVER] Utenti connessi: {len(utenti)} - {list(utenti.keys())}")
        try:
            conn.close()
        except:
            pass


# -------------------------
# MAIN SERVER
# -------------------------

def main():
    # Crea il socket del server
    cs.genera_RSAkeys()  # Genera le chiavi RSA all'avvio del server
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('localhost', 5000))
    server.listen(20)

    print("Server attivo su porta 5000...")

    # Accetta connessioni in loop infinito
    while True:
        conn, addr = server.accept()
        cs.sendPublicKeyToClient(conn)
        encrypted_key = cs.receiveEncryptedAESFromClient(conn)
        key = cs.decryptMessageRSA(encrypted_key)

        # Crea un thread per gestire ogni client
        threading.Thread(target=gestisciClient, args=(conn, key), daemon=True).start()


if __name__ == "__main__":
    main()
