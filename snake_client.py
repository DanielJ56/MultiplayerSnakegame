
from socket import *
import time
import socket
import threading
import pygame
import sys
import rsa
import pickle
import random

def drawGrid(surface):
    #Draw the grid lines
    global sides,rows
    space = sides // rows

    x = 0
    y = 0
    for l in range(rows):
        x = x + space
        y = y + space
        pygame.draw.line(surface, (255,255,255),(x,0),(x,sides))
        pygame.draw.line(surface, (255,255,255),(0,y),(sides,y))

def redrawWindow(surface):
    #Draw the grid
    surface.fill((0,0,0))
    drawGrid(surface)
    pygame.display.update()

def draw_rectangles(surface,snakecoord,col):
    #Draw a rectange at the given coordinates "snakecoord"
    global sides, rows
    dis = sides // rows
    
    pygame.draw.rect(surface, col, (int(snakecoord[0])*dis+1,int(snakecoord[1])*dis+1, dis-2, dis-2))
    pygame.display.update()

#For nth snake, use nth color
snake_color_list = [(128, 64, 192),
                    (255, 0, 128),
                    (200, 200, 50),
                    (45, 90, 135),
                    (210, 105, 30),
                    (30, 144, 255),
                    (255, 69, 0),
                    (75, 0, 130),
                    (255, 215, 0),
                    (173, 216, 230),
                    (0, 191, 255),
                    (0, 128, 128),
                    (255, 20, 147),
                    (65, 105, 225),
                    (0, 100, 0),
                    (0, 0, 205),
                    (218, 112, 214),
                    (244, 164, 96),
                    (107, 142, 35),
                    (219, 112, 147)]
def parser(server_message):
    global window
    #Parse server message
    #if & in message, then it is a message from another player
    if ("&" in server_message): 
        #If the message starts with something other than blank, it has been merged with a game state, so print the message and 
        # recursively parse the game state
        parts = server_message.split("&")
        if (parts[0] == ""):
            print(parts[1])
        else: 
            print(parts[1])
            parser(parts[0])
    else:
        #draw game state
        server_message = server_message.split("|")
        snake_multi = server_message[0].split("**")
        cube_positions = server_message[1].split("**")
        
        redrawWindow(window)
        #Draw the snake

        for j,snake_positions in enumerate(snake_multi):
            
            snake_positions = snake_positions.split("*")
            for i in snake_positions:
                coord = i.replace("(","").replace(")","").replace(" ","").split(",")
                draw_rectangles(window,coord,snake_color_list[j % 20])
        #Draw the cube
        for i in cube_positions:
            coord = i.replace("(","").replace(")","").replace(" ","").split(",")
            draw_rectangles(window,coord,(0,255,0))

def receiver(clientSocket):
    clientSocket.settimeout(10)

    clock = pygame.time.Clock()
    #Handle user input
    while True:
        user_input = ""

        events = pygame.event.get()
        if (events == []):
            user_input = "get"
            
        else: 
            for event in events:

                user_input = "get"
                if (event.type == pygame.QUIT):
                    pygame.quit()
                    user_input = "quit"
                if (event.type == pygame.KEYDOWN):
                    if event.key == pygame.K_UP:
                        user_input = "up"
                    elif event.key == pygame.K_DOWN:
                        user_input = "down"
                    elif event.key == pygame.K_LEFT:
                        user_input = "left"
                    elif event.key == pygame.K_RIGHT:
                        user_input = "right"
                    elif event.key == pygame.K_z:
                        user_input = "message:"+client_ip+"@"+ str(client_port) +"- Congratulations!"
                        break
                    elif event.key == pygame.K_x:
                        user_input = "message:"+client_ip+"@"+ str(client_port) +"- It Works!"
                        break
                    elif event.key == pygame.K_c:
                        user_input = "message:"+client_ip+"@"+ str(client_port) +"- Ready?"
                        break
                    elif event.key == pygame.K_r:
                        user_input = "reset"
                        break
        #If the user quits, close the socket
        #Encrypt with the server's public key
        if (user_input == "quit"):
            user_input = rsa.encrypt(user_input.encode(),server_key)

            clientSocket.send(user_input)
            clientSocket.close()
            break
        else: 
        #Otherwise, send the user input to the server
            user_input = rsa.encrypt(user_input.encode(),server_key)
            clientSocket.send(user_input)
            #server_message = clientSocket.recv(1024)
        pygame.time.delay(50)
        clock.tick(10)
    return 0
#listen for messages, if can decrypt it is message, otherwise it is games state
def listener(client_socket):

    client_socket.settimeout(10)
    try:
        while True:
            server_message = client_socket.recv(1024)
            try:
                #decrypt witht the client's private key
                server_message = rsa.decrypt(server_message, private_key)

                parser(server_message.decode())
            except:
                parser(server_message.decode())
    except OSError as e:
        return 0

#Socket setup and drawing pygame window
server_addr = 'localhost'
server_port = 5555
global sides,rows, window
rows = 20
sides = 500
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #TCP
client_socket.connect((server_addr, server_port))
client_ip, client_port = client_socket.getsockname()

#passing keys , send the client public key, receive the server public key
public_key, private_key = rsa.newkeys(1024)
client_socket.send(pickle.dumps(public_key))
server_key = pickle.loads(client_socket.recv(1024))
#Done passing keys
window = pygame.display.set_mode((500, 500))

listener_thread = threading.Thread(target=listener, args=(client_socket,))
listener_thread.start()
#receiver_thread = threading.Thread(target=receiver, args=(client_socket,))
#receiver_thread.start()
receiver(client_socket)


