import socket
import threading
import json
import time
import os

username = ""
chat_list = []  # Lista di dizionari: {"nome": "...", "tipo": "gruppo" o "privata"}
chat_storico = []
chat_corrente = None  # Dizionario della chat aperta: {"nome": "...", "tipo": "..."}


def riceviMsg(conn):
    """Thread che ascolta continuamente i messaggi dal server"""
    global chat_list, chat_storico, chat_corrente
    buffer = ""

    while True:
        try:
            data = conn.recv(2048).decode()
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


def inviaMsg(conn, msg):
    """Invia un messaggio JSON al server"""
    conn.sendall((json.dumps(msg) + "\n").encode())


# -------------------------
# MENU PRINCIPALE
# -------------------------

def menu_principale(conn):
    while True:
        os.system("cls")
        print("--- MENU PRINCIPALE ---")
        print("1) Vedi chat")
        print("2) Nuova chat privata")
        print("3) Crea gruppo")
        print("4) Esci")

        scelta = input("Scelta: ")

        if scelta == "1":
            menu_vedi_chat(conn)
        elif scelta == "2":
            nuova_chat_privata(conn)
        elif scelta == "3":
            crea_gruppo(conn)
        elif scelta == "4":
            print("Uscita...")
            conn.close()
            return


# -------------------------
# MENU CHAT
# -------------------------

def menu_vedi_chat(conn):
    global chat_list

    # Chiedi al server la lista delle chat
    inviaMsg(conn, {"tipo": "caricaChat", "utente": username})
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
                apri_chat(conn, chat_list[scelta-1])
        except:
            pass


# -------------------------
# CHAT IN TEMPO REALE
# -------------------------

def apri_chat(conn, chat):
    """Apre una chat (gruppo o privata)"""
    global chat_storico, chat_corrente

    chat_corrente = chat  # Salva quale chat è aperta

    # Chiedi lo storico della chat al server
    inviaMsg(conn, {
        "tipo": "apriChat",
        "utente": username,
        "nome_chat": chat["nome"],
        "tipo_chat": chat["tipo"]
    })
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
        })


# -------------------------
# CREAZIONE CHAT
# -------------------------

def nuova_chat_privata(conn):
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
    })
    time.sleep(0.2)


def crea_gruppo(conn):
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
    })
    time.sleep(0.2)


# -------------------------
# CONNESSIONE AL SERVER
# -------------------------

def main():
    global username

    # Connessione al server
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('localhost', 5000))

    print("Connesso al server!\n")

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
    threading.Thread(target=riceviMsg, args=(client,), daemon=True).start()

    # Mostra il menu principale
    menu_principale(client)


if __name__ == "__main__":
    main()