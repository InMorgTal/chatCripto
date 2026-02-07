import socket
import threading
import json
import time

# Variabili globali
username = ""
lista_chat = []
storico_chat=[]
chat_corrente = None

def ricevi_messaggio(conn):
    """Thread che riceve messaggi dal server"""
    global lista_chat
    
    while True:
        try:
            dati = conn.recv(2048).decode()
        except:
            print("\nConnessione persa")
            break
        
        if not dati:
            print("\nServer disconnesso")
            break
        
        # Prende solo il primo messaggio
        if "\n" in dati:
            dati = dati.split("\n")[0]

        msg = json.loads(dati)

        tipo = msg["tipo"]
        
        match tipo:

            case "lista_chat":
                lista_chat = msg["chat"]
        
            case "storico":
                if chat_corrente:
                    storico_chat = msg["messaggi"]

            case "messaggio":
                dest = msg["destinazione"]
                mitt = msg["sorgente"]
                
                # Trova la chiave della chat
                if dest in lista_chat:  # Gruppo
                    chiave = dest
                else:  # Chat privata
                    chiave = tuple(sorted([mitt, username]))
                # Stampa se siamo in quella chat
                if chat_corrente == chiave:
                    print(f"{mitt}: {msg['testo']}")
        
def invia_messaggio(conn, msg):
    """Invia un messaggio al server"""
    try:
        testo = json.dumps(msg) + "\n"
        conn.sendall(testo.encode())
        return True
    except:
        return False

def mostra_chat(conn):
    """Mostra la lista delle chat"""
    global lista_chat
    
    # Richiedi lista aggiornata
    invia_messaggio(conn, {"tipo": "carica_chat"})
    time.sleep(0.3)
    
    ricevi_messaggio(conn)

    while True:
        print("\n=== LE TUE CHAT ===")
        
        for i, chat in enumerate(lista_chat):
            print(f"{i+1}) {chat}")
        
        print("0) Indietro")
        
        scelta = input("Scelta: ")
        
        if scelta == "0":
            return
        
        try:
            indice = int(scelta) - 1
            if 0 <= indice < len(lista_chat):
                apri_chat(conn, lista_chat[indice])
        except:
            print("Scelta non valida")

def apri_chat(conn, nome_chat):
    """Apre una chat e permette di chattare"""
    global chat_corrente, storico_chat
    
    chat_corrente = nome_chat
    
    # Richiedi storico
    invia_messaggio(conn, {"tipo": "apri_chat", "chat": nome_chat})
    time.sleep(0.3)
    
    # Stampa storico
    print(f"\n=== CHAT: {nome_chat} === 0 per uscire\n")

    if nome_chat in storico_chat:
        for msg in storico_chat[nome_chat]:
            mitt = msg["sorgente"]
            testo = msg["testo"]
            
            if mitt == username:
                print(f"Tu: {testo}")
            else:
                print(f"{mitt}: {testo}")
    
    # Loop messaggi
    while True:
        testo = input("")
        
        if testo== "0":
            chat_corrente = None
            return
        
        if not testo.strip():
            continue
        
        # Invia messaggio
        msg = {
            "tipo": "messaggio",
            "sorgente": username,
            "destinazione": nome_chat,
            "testo": testo
        }
        invia_messaggio(conn, msg)
        
        # Salva localmente
        if nome_chat not in storico_chat:
            storico_chat[nome_chat] = []
        storico_chat[nome_chat].append(msg)

def nuova_chat_privata(conn):
    """Crea una nuova chat privata"""
    destinatario = input("Con chi vuoi chattare? ")
    
    # Crea chiave chat
    chiave = tuple(sorted([destinatario, username]))
    
    msg={"tipo": "crea_chat", "chat": chiave}

    invia_messaggio(conn,msg)

    if chiave not in lista_chat:
        lista_chat.append(chiave)

def nuovo_gruppo(conn):
    """Crea un nuovo gruppo"""
    nome = input("Nome del gruppo: ")
    
    invia_messaggio(conn, {"tipo": "crea_gruppo", "nome": nome})
    
    print(f"Gruppo '{nome}' creato!")

def avvia_client():
    """Avvia il client"""
    global username
    
    # Connessione al server
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        client.connect(('localhost', 5000))
        print("Connesso al server!\n")
    except:
        print("Impossibile connettersi al server")
        return
    
    # LOGIN
    while True:
        username = input("Username: ")

        client.sendall(username.encode())
        
        risposta = client.recv(1024).decode()
        if risposta == "True":
            print("Login effettuato!\n")
            break
        else:
            print("Username già in uso, riprova\n")
    
     # Avvia thread per ricevere messaggi
    thread = threading.Thread(target=ricevi_messaggio, args=(client,))
    thread.start()

    # Menu principale
    try:
        while True:
            print("\n=== MENU ===")
            print("1) Le mie chat")
            print("2) Nuova chat privata")
            print("3) Crea gruppo")
            print("4) Esci")
            
            scelta = input("Scelta: ")
            match scelta:
                case "1":
                    mostra_chat(client)
                case "2":
                    nuova_chat_privata(client)
                case "3":
                    nuovo_gruppo(client)
                case "4":
                    client.close()
                    break
    except KeyboardInterrupt as e:
        print("\nChiusura... {e}")
    finally:
        client.close()


if __name__ == "__main__":
    avvia_client()