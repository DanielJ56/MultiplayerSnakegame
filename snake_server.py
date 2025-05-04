import numpy as np
import socket
from _thread import *
import pickle
from snake import SnakeGame
import uuid
import time 
import rsa
import pickle
import threading
# server = "10.11.250.207"
server = "localhost"
port = 5555
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

counter = 0 
rows = 20 

try:
    s.bind((server, port))
except socket.error as e:
    str(e)

s.listen(2)
# s.settimeout(0.5)
print("Waiting for a connection, Server Started")


game = SnakeGame(rows)
game_state = "" 
last_move_timestamp = time.time()
interval = 0.2
moves_queue = set()
public_key, private_key = rsa.newkeys(1024)
client_list = []
keys_list = []

def game_thread() : 
    global game, moves_queue, game_state 
    while True :
        last_move_timestamp = time.time()
        game.move(moves_queue)
        moves_queue = set()
        game_state = game.get_state()
        while time.time() - last_move_timestamp < interval : 
            time.sleep(0.1) 



rgb_colors = {
    "red" : (255, 0, 0),
    "green" : (0, 255, 0),
    "blue" : (0, 0, 255),
    "yellow" : (255, 255, 0),
    "orange" : (255, 165, 0),
} 
rgb_colors_list = list(rgb_colors.values())



def main() : 
    #global counter, game, private_key, public_key
    print("server is running")
    #when a client connects, accept and start a new thread
    while True:
        conn, addr = s.accept()
        print("Connected to:", addr)
        client = threading.Thread(target=user_handler,args = (conn, addr))
        client.start()
        client_list.append(conn)

def user_handler(conn,addr):
    global counter, game, private_key, public_key
    
    #conn, addr = s.accept()
    #print("Connected to:", addr)

    #receive public key from client, send server public key
    player_key= pickle.loads(conn.recv(1024))
    conn.send(pickle.dumps(public_key))
    #Done receiving public key
    keys_list.append(player_key)

    unique_id = str(uuid.uuid4())
    color = rgb_colors_list[np.random.randint(0, len(rgb_colors_list))]
    game.add_player(unique_id, color = color) 

    start_new_thread(game_thread, ())
    while True : 
        data = conn.recv(2048)
        #Until recv is called, received data is stored in a buffer, the data will be concated of all elements 
        #decrypt with the server's private key
        data = rsa.decrypt(data, private_key).decode()
        move = None 
        if not data :
            print("no data received from client")
            conn.send(game_state.encode())

            break 
        elif data == "get" : 
            #print("received get")
            conn.send(game_state.encode())

            pass 
        elif data == "quit" :
            conn.send(game_state.encode())
            print("received quit")
            game.remove_player(unique_id)
            target_index = client_list.index(conn)

            client_list.remove(conn)
            keys_list.remove(keys_list[target_index])
            conn.close()
            break
        elif data == "reset" : 
            conn.send(game_state.encode())
            game.reset_player(unique_id)

        elif data in ["up", "down", "left", "right"] : 
            conn.send(game_state.encode())
            move = data
            moves_queue.add((unique_id, move))
        
        #If it is a message,parse it and send it to all clients
        elif data[0:7] == "message":
            data = data.split(":")[1]
            data = "&" + data
            #broadcast the message to all clients, encrypted with the client's public key
            for indexs,sock in enumerate(client_list): 
                broad_casted_message = rsa.encrypt(data.encode(),keys_list[indexs])
                sock.send((broad_casted_message))

        else :
            conn.send(game_state.encode())
            print("Invalid data received from client:", data)
            
    #conn.close()

if __name__ == "__main__" : 
    main()