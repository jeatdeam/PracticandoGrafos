import os
import re
import random
import matplotlib.pyplot as plt
import networkx as nx
from faker import Faker
from usuario import Usuario
import pandas as pd
import graphviz as gv

import os
from IPython.display import display

# Agregamos correctamente la ruta al PATH de las variables de entorno de la sesión
os.environ["PATH"] += os.pathsep + r"C:\Program Files\Graphviz\bin"


fake = Faker("es_ES")

#datos es un dataframe que conceptualmente se parece a una tabla
datos = pd.read_csv('peliculas_streaming_1000.csv')

# print(datos.head(10).columns)

# print(datos["movie_id"])


CANTIDAD_USUARIOS = 25
CANTIDAD_PELICULAS_VISTAS = 100
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
        self.grafo_dirigido = []



    def generar_usuarios(self):
        self.usuarios_registrados = {}
        
        # 1. Guardamos temporalmente las líneas formateadas en una lista
        lineas_impresion = []

        for indice, _ in enumerate(range(CANTIDAD_USUARIOS)):
            nombre = fake.first_name()
            apellido = fake.last_name()
            correo = fake.email()

            nuevo_usuario = Usuario(nombre, apellido, correo, indice + 1)
            self.usuarios_registrados[indice] = nuevo_usuario 

            # Creamos el texto de cada usuario
            texto_usuario = f"{indice+1}: {nuevo_usuario.nombre} {nuevo_usuario.apellido}"
            lineas_impresion.append(texto_usuario)

        # 2. Imprimimos en 2 columnas (dividimos la lista a la mitad)
        mitad = (len(lineas_impresion) + 1) // 2

        for i in range(mitad):
            # Obtenemos el elemento de la columna izquierda
            columna_izq = lineas_impresion[i]
            
            # Verificamos si existe un elemento correspondiente para la columna derecha
            columna_der = lineas_impresion[i + mitad] if (i + mitad) < len(lineas_impresion) else ""

            # Imprimimos ambos lados alineados (el '35' es el ancho del espacio para la columna izquierda)
            print(f"{columna_izq:<35} | {columna_der}")


    def asignar_peliculas(self):
        for indice, _ in enumerate(self.usuarios_registrados):
            # Asigno películas vistas.
            peliculas_vistas = random.randint(0, CANTIDAD_PELICULAS_VISTAS)

            print(f"Usuario {indice + 1} ---------------------------------------------------------------- [peliculas vistas] ")

            if peliculas_vistas == 0:
                print("-El usuario aun no ha visto ninguna pelicula")
            
            # Lista temporal para guardar los títulos de este usuario
            titulos_usuario = []

            for i in range(peliculas_vistas):
                posicion_random = random.randint(0, len(datos) - 1)
                pelicula_dict = datos.iloc[posicion_random].to_dict()
                
                # Guardamos el título y registramos la película
                titulos_usuario.append(pelicula_dict["titulo"])
                self.usuarios_registrados[indice].ver_pelicula(pelicula_dict)

            # Imprimir en dos columnas recorriendo de 2 en 2
            for i in range(0, len(titulos_usuario), 2):
                col1 = f"{i + 1}. {re.sub(r'\d','',titulos_usuario[i])}"
                
                # Verificamos si existe una segunda columna para este par
                if i + 1 < len(titulos_usuario):
                    col2 = f"{i + 2}. {re.sub(r'\d','',titulos_usuario[i + 1])}"
                    # Usamos un ancho fijo (ej. 50 espacios) para alinear la segunda columna
                    print(f"{col1:<50} | {col2}")
                else:
                    # Si es número impar, solo imprimimos la primera columna
                    print(f"{col1}")

            print("------------------------------------------------------------------------------------------")
            print("\n")   


       
    def mostrar_generos_usuario(self):

        print("----------------------------------------------------------[genero favorito]")

        for clave, valor in self.usuarios_registrados.items():
            # print(f'Usuario {clave}: {valor.get_nombre()} -------------------- ', end = "")
            info_usuario = f"Usuario {clave}: {valor.get_nombre()}"
            print(f"{info_usuario:<25}    -------------------------->      ", end = "")
            if self.usuarios_registrados[clave].obtener_generos_vistos() != None:
                    print(self.usuarios_registrados[clave].obtener_generos_vistos())




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


    # def draw_dfs(self, directed, path):
    #     graph = gv.Digraph('grafoD1') if directed else gv.Graph('grafoND1')       
    #     n = len(self.grafo)
    #     added = set()

    #     for u, v in enumerate(path):
    #         if v != -1:
    #             added.add((v,u))
    #             graph.edge(str(v), str(u), color = "blue")
    #             if not directed:
    #                 graph.edge(str(u), str(v))

    #     for u in range(1, n + 1):
    #         for v in self.grafo[u]:
    #             if directed:
    #                 if (u, v) not in added:
    #                     graph.edge(str(u), str(v))
    #                     added.add((u,v))
    #             else:
    #                 if (u, v) not in added and (v, u) not in added:
    #                     graph.edge(str(u), str(v))
    #                     added.add((u,v))
    #                     added.add((v, u))

    #     graph.render('resultado_dfsa', format='png', cleanup=True)
    #     print("¡Grafo guardado como 'resultado_dfs.png' en tu carpeta!")


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



    def obtener_sub_grafo(self):

        n = len(self.grafo_dirigido)
        visited = [False]*n
        sub_grafos = []

        def _dfs(u):
            visited[u] = True
            for v in self.grafo_dirigido[u]:
                if not visited[v]:
                    _dfs(v)





    def generar_grafo(self):
        # Asignamos las conexiones (aristas) del grafo

        self.grafo_dirigido = []

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

        for _, valor in self.grafo.items():
            self.grafo_dirigido.append(valor)

        print("---------------------------------------------------")
        print("[")
        for indice, nodo in enumerate(self.grafo_dirigido):
            print(f" {self.usuarios_registrados[indice].nombre} ",nodo)
        print("]")
        print("---------------------------------------------------")


    def mostrar_subGrafo(self,  posicion, directed = False):
        graph = gv.Digraph('grafoD1') if directed else gv.Graph('grafoND1')
        n = len(self.grafo_dirigido[posicion])
        added = set()


        graph.node(str(posicion), f"{self.usuarios_registrados[posicion].nombre}-{posicion}")

        aux_seccion_grafo = list(self.grafo_dirigido[posicion]) + [posicion]

        usuario_genero = self.usuarios_registrados[0].genero_preferido

        for u in self.grafo_dirigido[posicion]:
            graph.node(str(u), f"{self.usuarios_registrados[u].nombre}-{u}")

        graph.node(usuario_genero, usuario_genero, color = "lightblue", fillcolor = "lightblue", style="filled")


        for u in aux_seccion_grafo:
            graph.edge(usuario_genero, str(u), color = "blue")
            for v in self.grafo_dirigido[posicion]:
                if (u,v) not in added and u != v:
                    if directed:
                        graph.edge(str(u), str(v))
                        added.add((u,v))
                    else:
                        graph.edge(str(u), str(v))
                        added.add((u,v))
                        added.add((v,u))


        graph.render(filename="sub_grafo", format = "png", cleanup=True)


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

        # print(datos.sample(n = 1).values[0])
            
        def recomendar_peliculas(usuario):
            peliculas_usuario = [ pelicula['titulo']  for pelicula in usuario.get_peliculasVistas()]

            peliculas_recomendadas = []
            contador = 0

            genero_usuario = str(usuario.genero_preferido)

            peliculas_filtradas = datos[datos['genero'] == genero_usuario].to_dict(orient="records")

            print(f"Usuario {usuario.nombre}")


            for indice, pelicula in enumerate(peliculas_filtradas):
                if contador == PELICULAS_A_RECOMENDAR:
                   break 
                if pelicula['titulo'] not in peliculas_usuario:
                      contador += 1

                    #   pelicula_agregada = datos[datos["titulo"] == pelicula].to_dict(orient='records')[0]

                      print(f"{indice + 1}.", re.sub(r"\d", "", pelicula['titulo']))
                    #   print( pelicula_agregada)
                      peliculas_recomendadas.append(pelicula)

            # print(peliculas_recomendadas)
            print("\n")
            usuario.asignar_peliculasRecomendadas(peliculas_recomendadas)
    
    
        for indice, _ in enumerate(self.usuarios_registrados):
            recomendar_peliculas(self.usuarios_registrados[indice])



    def grafico_grafo(self, directed = False, path = []):
         
        graph = gv.Digraph('grafoD1') if directed else gv.Graph('grafoND1')
        n = len(self.grafo_dirigido)

        added = set()


        generos_filtrados = set()

        for u in range(n):
            graph.node(str(u), f"{self.usuarios_registrados[u].nombre}-{u}")
            genero = self.usuarios_registrados[u].genero_preferido
            if genero == None:
                generos_filtrados.add("sin peliculas vistas")
            else:
                generos_filtrados.add(genero)

        lista_generos = list(generos_filtrados)

        # -----------------------------
        for genero in lista_generos:
            graph.node(genero, genero, color = "lightblue", fillcolor = "lightblue", style="filled")

        # graph.node(str("999"), usuario_genero, color = "lightblue", fillcolor = "lightblue", style="filled")

        for u in range(n):
            if self.usuarios_registrados[u].genero_preferido == None:
                graph.edge('sin peliculas vistas', str(u), color="blue") 
            else:
                genero_usuario = self.usuarios_registrados[u].genero_preferido
                graph.edge(genero_usuario, str(u), color = "blue")

            for v in self.grafo_dirigido[u]:

                if (u,v) not in added:
                    if directed:
                        graph.edge(str(u), str(v))
                        added.add((u,v))
                    else:
                        graph.edge(str(u), str(v))
                        added.add((u,v))
                        added.add((v,u))


        graph.render(filename="grafito_clientes", format = "png", cleanup = True)


    def mostrar_menu():
        return None




project_streaming = Project_Streaming()


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
           print("************************* Menu Streaming **************************")
           print("1. Generar usuarios")
           print("2. Asignar peliculas")
           print("3. Mostrar generos favoritos")
           print("4. Generar grafo")
           print("5. Mostrar grafo")
           print("6. Generar recomendaciones")
           print("7. Salir")
           print("*******************************************************************")
           opcion = menu_opcion()
           
           match opcion:
               case 1:
                   os.system('cls' if os.name == 'nt' else 'clear')
                   print("************************* Usuarios registrados ******************************")
                   project_streaming.generar_usuarios()
                   print("*****************************************************************************")
                   input('Presione una tecla para continuar ... ')
               case 2: 
                   os.system('cls' if os.name == 'nt' else 'clear')
                #    print("***************************************************\n")
                   project_streaming.asignar_peliculas()
                #    print("\n***************************************************")
                   input('Presione una tecla para continuar ... ')
               case 3:
                   os.system('cls' if os.name == 'nt' else 'clear')
                   print("*************************** Generos mas vistos por los usuarios ***************************")
                   project_streaming.mostrar_generos_usuario()
                   print("*******************************************************************************************")
                   input('Presione una tecla para continuar')
               case 4: 
                   os.system('cls' if os.name == 'nt' else 'clear')
                   print("***************************************************")
                   project_streaming.generar_grafo()
                   project_streaming.grafico_grafo()
                   print("***************************************************")
                   input('Presione una tecla para continuar ... ')
               case 5:
                   os.system('cls' if os.name == 'nt' else 'clear')
                #    print("***************************************************")
                   project_streaming.mostrar_grafoMA()
                #    print("***************************************************")
                   input('Presione una tecla para continuar ... ')
               case 6:
                   os.system('cls' if os.name == 'nt' else 'clear')
                   print("****************************************************")
                   print('------- Estas son las peliculas a recomendar -------')

                   project_streaming.generar_recomendaciones()
                   print("***************************************************")
                   input('Presione una tecla para continuar ... ')
               case 7:
                   os.system('cls' if os.name == 'nt' else 'clear')
                   # %%
                   nodo_grafo = input('Ingrese un nodo a buscar para el sub_grafo: ')
                   project_streaming.mostrar_subGrafo(int(nodo_grafo))

                   input('Presione una tecla para continuar ...')
                #    path = project_streaming.dfs(1)
                #    print(path)
                #    project_streaming.draw_dfs(True, path)
                   # En lugar de display(graph), usas esto en tu código:
                   # %%
                   print('llegamos al final')
                   print("***************************************************")
                   break



menu()
