import socket
import threading
import json
import time

# Variabili globali
username = ""
lista_chat = []
storico_chat = {}
chat_corrente = None
login_ok = False
risposta_login = threading.Event()


def ricevi_messaggi(conn):
    """Thread che riceve messaggi dal server"""
    global lista_chat, storico_chat, login_ok
    
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
        
        try:
            msg = json.loads(dati)
        except:
            continue
        
        tipo = msg.get("tipo")
        
        # Risposta login
        if tipo == "login":
            login_ok = msg["ok"]
            risposta_login.set()
        
        # Lista chat
        elif tipo == "lista_chat":
            lista_chat = msg["chat"]
        
        # Storico chat
        elif tipo == "storico":
            if chat_corrente:
                storico_chat[chat_corrente] = msg["messaggi"]
        
        # Nuovo messaggio
        elif tipo == "messaggio":
            dest = msg["destinazione"]
            mitt = msg["sorgente"]
            
            # Trova la chiave della chat
            if dest in lista_chat:  # Gruppo
                chiave = dest
            else:  # Chat privata
                if mitt < username:
                    chiave = f"{mitt}_{username}"
                else:
                    chiave = f"{username}_{mitt}"
            
            # Salva messaggio
            if chiave not in storico_chat:
                storico_chat[chiave] = []
            storico_chat[chiave].append(msg)
            
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


def menu_principale(conn):
    """Menu principale"""
    while True:
        print("\n=== MENU ===")
        print("1) Le mie chat")
        print("2) Nuova chat privata")
        print("3) Crea gruppo")
        print("4) Esci")
        
        scelta = input("Scelta: ")
        
        if scelta == "1":
            mostra_chat(conn)
        elif scelta == "2":
            nuova_chat_privata(conn)
        elif scelta == "3":
            nuovo_gruppo(conn)
        elif scelta == "4":
            conn.close()
            break


def mostra_chat(conn):
    """Mostra la lista delle chat"""
    global lista_chat
    
    # Richiedi lista aggiornata
    invia_messaggio(conn, {"tipo": "carica_chat"})
    time.sleep(0.3)
    
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
    print(f"\n=== CHAT: {nome_chat} ===")
    print("(scrivi 'esci' per uscire)\n")
    
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
        
        if testo.lower() == "esci":
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
    if username < destinatario:
        chiave = f"{username}_{destinatario}"
    else:
        chiave = f"{destinatario}_{username}"
    
    # Aggiungi alle chat se non esiste
    if chiave not in lista_chat:
        lista_chat.append(chiave)
    
    apri_chat(conn, chiave)


def nuovo_gruppo(conn):
    """Crea un nuovo gruppo"""
    nome = input("Nome del gruppo: ")
    
    invia_messaggio(conn, {"tipo": "crea_gruppo", "nome": nome})
    time.sleep(0.3)
    
    print(f"Gruppo '{nome}' creato!")


def avvia_client():
    """Avvia il client"""
    global username, login_ok
    
    # Connessione al server
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        client.connect(('localhost', 5000))
        print("Connesso al server!\n")
    except:
        print("Impossibile connettersi al server")
        return
    
    # Avvia thread per ricevere messaggi
    thread = threading.Thread(target=ricevi_messaggi, args=(client,))
    thread.daemon = True
    thread.start()
    
    # LOGIN
    while True:
        username = input("Username: ")
        
        risposta_login.clear()
        invia_messaggio(client, {"username": username})
        risposta_login.wait(timeout=2)
        
        if login_ok:
            print("Login effettuato!\n")
            break
        else:
            print("Username già in uso, riprova\n")
    
    # Menu principale
    try:
        menu_principale(client)
    except KeyboardInterrupt:
        print("\nChiusura...")
    finally:
        client.close()


if __name__ == "__main__":
    avvia_client()