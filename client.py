import socket
import threading
import json
import time
import os
import cittografiaClient as cc

username = ""
chat_list = []  # Lista di dizionari: {"nome": "...", "tipo": "gruppo" o "privata"}
chat_storico = []
chat_corrente = None  # Dizionario della chat aperta: {"nome": "...", "tipo": "..."}


def riceviMsg(conn, key):
    #"""Thread che ascolta continuamente i messaggi dal server"""
    global chat_list, chat_storico, chat_corrente

    buffer = ""

    while True:
        try:
            tag = cc.recv_exact(conn, 16)
            nonce = cc.recv_exact(conn, 12)
            msg_len = int.from_bytes(cc.recv_exact(conn, 4), 'big')
            encrypted_msg = cc.recv_exact(conn, msg_len)  # Assicurati di leggere l'intera risposta cifrata
            data = key.decriptare(encrypted_msg, tag, nonce)
        except:
            break

        if not data:
            break

        buffer += data

        # Processa tutti i messaggi completi nel buffer
        while "\n" in buffer:
            msg_str, buffer = buffer.split("\n", 1)
            msg = json.loads(msg_str)

            if msg["tipo"] == "caricaChat":
                # Ricevuta lista delle chat
                chat_list = msg["chat"]

            elif msg["tipo"] == "chatAperta":
                # Ricevuto lo storico di una chat
                chat_storico = msg["messaggi"]

            elif msg["tipo"] == "messaggio":
                # Ricevuto un nuovo messaggio
                chat_storico.append(msg)
                
                # Se siamo in una chat, stampa il messaggio subito
                if chat_corrente is not None:
                    print(f"{msg['mittente']}: {msg['testo']}")
                    print("", end="", flush=True)


def inviaMsg(conn, msg, key):
    #Invia un messaggio JSON al server
    data = json.dumps(msg) + "\n"
    data = data.encode()
    encrypted_text, tag, nonce = key.criptare(data)
    conn.sendall(tag)
    conn.sendall(nonce)
    conn.sendall(len(encrypted_text).to_bytes(4, 'big'))
    conn.sendall(encrypted_text)


# -------------------------
# MENU PRINCIPALE
# -------------------------

def menu_principale(conn, key):
    while True:
        os.system("cls")
        print("--- MENU PRINCIPALE ---")
        print("1) Vedi chat")
        print("2) Nuova chat privata")
        print("3) Crea gruppo")
        print("4) Esci")

        scelta = input("Scelta: ")

        match scelta:
            case "1":
                menu_vedi_chat(conn, key)
                pass
            case "2":
                nuova_chat_privata(conn, key)
                pass
            case "3":
                crea_gruppo(conn, key)
                pass
            case "4":
                print("Uscita...")
                conn.close()
                return


# -------------------------
# MENU CHAT
# -------------------------

def menu_vedi_chat(conn, key):
    global chat_list

    # Chiedi al server la lista delle chat
    inviaMsg(conn, {"tipo": "caricaChat", "utente": username}, key)
    time.sleep(0.2)

    while True:
        os.system("cls")
        print("--- LE TUE CHAT ---")

        # Mostra tutte le chat
        for i, chat in enumerate(chat_list):
            tipo = "GRUPPO" if chat["tipo"] == "gruppo" else "PRIVATA"
            print(f"{i+1}) [{tipo}] {chat['nome']}")

        print("0) Torna indietro")

        scelta = input("Scelta: ")

        if scelta == "0":
            return

        try:
            scelta = int(scelta)
            if 1 <= scelta <= len(chat_list):
                apri_chat(conn, chat_list[scelta-1], key)
        except:
            pass


# -------------------------
# CHAT IN TEMPO REALE
# -------------------------

def apri_chat(conn, chat, key):
    """Apre una chat (gruppo o privata)"""
    global chat_storico, chat_corrente

    chat_corrente = chat  # Salva quale chat è aperta

    # Chiedi lo storico della chat al server
    inviaMsg(conn, {
        "tipo": "apriChat",
        "utente": username,
        "nome_chat": chat["nome"],
        "tipo_chat": chat["tipo"]
    }, key)
    time.sleep(0.2)

    # Stampa lo storico iniziale
    os.system("cls")
    tipo = "GRUPPO" if chat["tipo"] == "gruppo" else "PRIVATA"
    print(f"--- CHAT [{tipo}] {chat['nome']} --- (0 per uscire)")
    print()
    for msg in chat_storico:
        print(f"{msg['mittente']}: {msg['testo']}")
    print()

    # Loop per inviare messaggi (i messaggi in arrivo vengono stampati dal thread riceviMsg)
    while True:
        testo = input("")
        
        if testo == "0":
            chat_corrente = None  # Reset quando esci
            return

        # Invia il messaggio al server
        inviaMsg(conn, {
            "tipo": "messaggio",
            "mittente": username,
            "destinazione": chat["nome"],
            "tipo_chat": chat["tipo"],
            "testo": testo
        }, key)


# -------------------------
# CREAZIONE CHAT
# -------------------------

def nuova_chat_privata(conn, key):
    """Crea una nuova chat privata con un utente"""
    global username

    while True:
        destinatario = input("Con chi vuoi parlare? ")
        if destinatario != username:
            break
        print("Non puoi parlare con te stesso!")

    # Invia richiesta al server
    inviaMsg(conn, {
        "tipo": "iniziaConv",
        "utente1": username,
        "utente2": destinatario
    }, key)
    time.sleep(0.2)


def crea_gruppo(conn, key):
    """Crea un nuovo gruppo"""
    membri = []

    # Chiedi i partecipanti
    while True:
        utente = input("Aggiungi partecipante (0 per finire): ")
        if utente == "0":
            break
        if utente not in membri:
            membri.append(utente)

    # Aggiungi te stesso
    membri.append(username)
    
    # Chiedi il nome del gruppo
    nome = input("Nome del gruppo: ")

    # Invia richiesta al server
    inviaMsg(conn, {
        "tipo": "creaGruppo",
        "nome": nome,
        "membri": membri
    }, key)
    time.sleep(0.2)


# -------------------------
# CONNESSIONE AL SERVER
# -------------------------

def main():
    global username

    key = cc.crea_aes_key()  # Crea una chiave AES se non esiste già
    # Connessione al server
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('localhost', 5000))

    print("Connesso al server!\n")

    public_key = cc.ricevere_RSAkey(client)
    encripted_key = cc.cripta_RSA(public_key, key)
    client.sendall(len(encripted_key).to_bytes(4, 'big'))
    cc.sendAESkey(encripted_key, client)

    # Login con username
    while True:
        username = input("Inserisci username: ")

        client.sendall(username.encode())

        risposta = client.recv(2048).decode()
        if risposta == "Username occupato":
            print("Username già in uso!")
        else:
            break

    # Avvia il thread che ascolta i messaggi dal server
    threading.Thread(target=riceviMsg, args=(client, key), daemon=True).start()

    # Mostra il menu principale
    menu_principale(client, key)


if __name__ == "__main__":
    main()
