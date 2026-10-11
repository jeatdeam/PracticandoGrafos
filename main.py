import os
import re
import random
import matplotlib.pyplot as plt
import networkx as nx
from faker import Faker
from usuario import Usuario
import pandas as pd
import graphviz as gv


fake = Faker("es_ES")

#datos es un dataframe que conceptualmente se parece a una tabla
datos = pd.read_csv('peliculas_streaming_1000.csv')

# print(datos.head(10).columns)

# print(datos["movie_id"])


CANTIDAD_USUARIOS = 5
CANTIDAD_PELICULAS_VISTAS = 10
PELICULAS_A_RECOMENDAR = 5


# Definición de colores
ROJO = '\033[31m'
VERDE = '\033[32m'
AMARILLO = '\033[33m'
AZUL = '\033[34m'
RESET = '\033[0m'  # Restablece el color normal

#Creamos a los usuarios y los inicializamos
#el de arriba networkx sirve para hacer un grafo con nodos y aristas
#Creamos a las peliculas y las asignamos a los usuarios


class Project_Streaming:

    def __init__(self):
        self.usuarios_registrados = {}
        self.grafo = {}



    def generar_usuarios(self):

        for indice, _  in enumerate(range(CANTIDAD_USUARIOS)):
            nombre = fake.first_name()
            apellido = fake.last_name()
            correo = fake.email()

            nuevo_usuario = Usuario(nombre, apellido, correo, indice + 1)

            # print("\n")
            print(f"{indice+1} {nuevo_usuario.nombre} {nuevo_usuario.apellido}") 
            self.usuarios_registrados[indice + 1] = nuevo_usuario


    def asignar_peliculas(self):

        for indice, _ in enumerate(self.usuarios_registrados):
            #asigno peliculas vistas.
            peliculas_vistas = random.randint(0, CANTIDAD_PELICULAS_VISTAS)


            print(f"Usuario {indice + 1} [peliculas vistas] ------------------------")

            for _ in range(peliculas_vistas):
                posicion_random = random.randint(0, len(datos)-1)
                #aqui si pasamos .to_dick() sin parametros nos dara un diccionario donde las claves seran las columnas y dentro guardara otro diccionario {'usuario':{0: 'user', 1:'user_2'}}
                pelicula_dict = datos.iloc[posicion_random].to_dict()

                print(f'- {pelicula_dict["titulo"]}')
                self.usuarios_registrados[indice + 1].ver_pelicula(pelicula_dict)     

            # self.usuarios_registrados[indice + 1].obtener_generos_vistos()


       
    def mostrar_generos_usuario(self):

        for indice, usuario in enumerate(self.usuarios_registrados):
            print(f'Usuario {indice + 1} [genero favorito] -----------------')
            print(f"-  {self.usuarios_registrados[indice + 1].obtener_generos_vistos()}")            



    def dfs(self, s):
        n = len(self.grafo)
        path = [-1]*n
        visited = [False]*n

        def _dfs(u):
            visited[u] = True
            for v in range(n):
                 if not visited[v]:
                     path[v] = u
                     _dfs(v)
        _dfs(s)
        return path


    def draw_dfs(self, directed, path):
        graph = gv.Digraph('grafoD1') if directed else gv.Graph('grafoND1')       
        n = len(self.grafo)
        added = set()

        for u, v in enumerate(path):
            if v != -1:
                added.add((v,u))
                graph.edge(str(v), str(u), color = "blue")
                if not directed:
                    graph.edge(str(u), str(v))

        for u in range(1, n):
            for v in self.grafo[u]:
                if directed:
                    if (u, v) not in added:
                        graph.edge(str(u), str(v))
                        added.add((u,v))
                else:
                    if (u, v) not in added and (v, u) not in added:
                        graph.edge(str(u), str(v))
                        added.add((u,v))
                        added.add((v, u))


    def bfs(self, s):
        n = len(self.grafo)
        visited = [False]*n
        path = [-1]*n
        queue = [s]
        visited[s] = True

        while queue:
            u = queue.pop(0)
            for v in range(n):
                if self.grafo[u][v] == 1 and not visited[v]:
                    visited[v] = True
                    path[v] = u
                    queue.append(v)

    def generar_grafo(self):
        # Asignamos las conexiones (aristas) del grafo
        for id_usuario_1, usuario_1 in self.usuarios_registrados.items():
            # Inicializamos la lista de adyacencia para el usuario actual
            self.grafo[id_usuario_1] = []

            for id_usuario_2, usuario_2 in self.usuarios_registrados.items():
                # Evitamos que un usuario cree una conexión/relación consigo mismo
                if id_usuario_1 == id_usuario_2:
                    continue
                
                # Si comparten el género favorito, agregamos la conexión
                if usuario_1.get_generoFav() == usuario_2.get_generoFav():
                    # Puedes guardar el objeto entero o solo su ID (recomendado ID para grafos)
                    self.grafo[id_usuario_1].append(id_usuario_2)

        print("--------------------------------------")
        print(self.grafo)
        print(len(self.grafo))
        print("--------------------------------------")


    def mostrar_grafoMA(self):
        VERDE = '\033[32m'
        GRIS = '\033[90m'
        RESET = '\033[0m'

        nodos = sorted(self.grafo.keys())
        print("\t" + "\t".join(str(n) for n in nodos))

        for i in nodos:
            vecinos = set(self.grafo[i])
            fila = [str(i)]
            for j in nodos:
                if j in vecinos:
                    fila.append(f"{VERDE}1{RESET}")  # Pinta los 1 de verde
                else:
                    fila.append(f"{GRIS}0{RESET}")   # Pinta los 0 de gris
            print("\t".join(fila))
        #sirve para hacer u ngraficon con lineas uniendo coordenadas


    def generar_recomendaciones(self):
            
        def recomendar_peliculas(usuario):
            peliculas_usuario = [ pelicula['titulo']  for pelicula in usuario.get_peliculasVistas()]

            peliculas_recomendadas = []
            contador = 0
            for indice, pelicula in enumerate(datos["titulo"]):
                if contador == PELICULAS_A_RECOMENDAR:
                    break 
                if pelicula not in peliculas_usuario:
                      contador += 1
                      pelicula_agregada = datos[datos["titulo"] == pelicula].to_dict(orient='records')[0]

                      print(f'\n{indice + 1} Aqui va una pelicula agregada: {pelicula}')
                    #   print( pelicula_agregada)
                      peliculas_recomendadas.append(pelicula_agregada)


            print('---estas son las peliculas a recomendar----')
            print(peliculas_recomendadas)

            usuario.asignar_peliculasRecomendadas(peliculas_recomendadas)
    
    
        for indice, _ in enumerate(self.usuarios_registrados):
            recomendar_peliculas(self.usuarios_registrados[indice+1])


    def mostrar_menu():
        return None






project_streaming = Project_Streaming()

# project_streaming.generar_usuarios()
# project_streaming.asignar_peliculas()
# project_streaming.generar_grafo()
# project_streaming.mostrar_grafoMA()
# project_streaming.generar_recomendaciones()



def menu_opcion():

    while True:

        try: 
            opcion = int(input("Ingrese una opcion: "))
            if(opcion < 1 or opcion > 7):
                print('Error: ingrese un numero valido (1 - 7)')
            else:
                break
        except ValueError:
            print('Error: debes ingresar un número entero valido (no letras).')

    return opcion
   

def menu():


    while(True):
           os.system('cls' if os.name == 'nt' else 'clear')
           print("***************************************************")
           print("1. Generar usuarios")
           print("2. Asignar peliculas")
           print("3. Mostrar generos favoritos")
           print("4. Generar grafo")
           print("5. Mostrar grafo")
           print("6. Generar recomendaciones")
           print("7. Salir")
           print("***************************************************")
           opcion = menu_opcion()
           
           match opcion:
               case 1:
                   os.system('cls' if os.name == 'nt' else 'clear')
                   print("***************************************************")
                   project_streaming.generar_usuarios()
                   print("***************************************************")
                   input('Presione una tecla para continuar ... ')
               case 2: 
                   os.system('cls' if os.name == 'nt' else 'clear')
                   print("***************************************************")
                   project_streaming.asignar_peliculas()
                   print("***************************************************")
                   input('Presione una tecla para continuar ... ')
               case 3:
                   os.system('cls' if os.name == 'nt' else 'clear')
                   print("***************************************************")
                   project_streaming.mostrar_generos_usuario()
                   print("***************************************************")
                   input('Presione una tecla para continuar')
               case 4: 
                   os.system('cls' if os.name == 'nt' else 'clear')
                   print("***************************************************")
                   project_streaming.generar_grafo()
                   print("***************************************************")
                   input('Presione una tecla para continuar ... ')
               case 5:
                   os.system('cls' if os.name == 'nt' else 'clear')
                   print("***************************************************")
                   project_streaming.mostrar_grafoMA()
                   print("***************************************************")
                   input('Presione una tecla para continuar ... ')
               case 6:
                   os.system('cls' if os.name == 'nt' else 'clear')
                   print("***************************************************")
                   project_streaming.generar_recomendaciones()
                   print("***************************************************")
                   input('Presione una tecla para continuar ... ')
               case 7:
                   os.system('cls' if os.name == 'nt' else 'clear')
                   print("***************************************************")
                   path = project_streaming.dfs(2)
                   print(path)
                   project_streaming.draw_dfs(True, path)
                   print('llegamos al final')
                   print("***************************************************")
                   break



menu()















# PELICULAS_A_RECOMENDAR = 5

# print("#########################################")



# def recomendar_peliculas(usuario):

#     peliculas_usuario = [ pelicula['titulo']  for pelicula in usuario.get_peliculasVistas()]

#     peliculas_recomendadas = []
#     contador = 0
#     for pelicula in datos["titulo"]:
#         if contador == PELICULAS_A_RECOMENDAR:
#             break 
#         if pelicula not in peliculas_usuario:
#               contador += 1
#               pelicula_agregada = datos[datos["titulo"] == pelicula].to_dict(orient='records')[0]

#               print('\naqui va una pelicula agregada')
#               print( pelicula_agregada)
#               peliculas_recomendadas.append(pelicula_agregada)


#     print('\n---estas son las peliculas a recomendar----')
#     print(peliculas_recomendadas)

#     usuario.asignar_peliculasRecomendadas(peliculas_recomendadas)

# # recomendar_peliculas(usuarios_registrados[1])

# print("#########################################")


# for indice, usuario in enumerate(usuarios_registrados):
#     recomendar_peliculas(usuarios_registrados[indice+1])


# x = [1, 2, 3, 4]
# y = [10, 20, 15, 30]

# plt.plot(x, y)
# plt.show()

# G = nx.Graph()

# G.add_node("U1")
# G.add_node("U2")

# G.add_edge("U1", "U2")

# nx.draw(G)
# plt.show()

