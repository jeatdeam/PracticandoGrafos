from collections import Counter


class Usuario:

    def __init__(self, nombre, apellido, correo, id_usuario):
        self.nombre = nombre
        self.apellido = apellido
        self.correo = correo
        self.peliculas_vistas = []
        self.generos_vistos = []
        self.favoritas = []
        self.genero_preferido = None
        self.id_usuario = id_usuario
        self.peliculasRecomendadas = []

    def mostrar_info(self):
        return f"Nombre: {self.nombre}, Apellido: {self.apellido}, Correo: {self.correo}"


    def asignar_pelicula_vistas(self, peliculas):
        self.peliculas_vistas.append(peliculas)


    def asignar_genero_vistos(self, generos):
        self.generos_vistos.append(generos)

    def mostrar_genero(self):
        return self.generos_vistos


    def mostrar_nombre(self):
        return self.nombre

    def ver_pelicula(self, pelicula_dict):
        # if pelicula_name not in self.peliculas_vistas:
        #     self.peliculas_vistas.append(pelicula_name)

        titulos_vistos = [p["titulo"] for p in self.peliculas_vistas]
        
        if pelicula_dict["titulo"] not in titulos_vistos:
            self.peliculas_vistas.append(pelicula_dict)


    def get_peliculasVistas(self):
        return self.peliculas_vistas


    def mostrar_peliculas_vistas(self):
        for pelicula in self.peliculas_vistas:
            print(pelicula["titulo"])

    #lo que devuelve pandas es un dataFrame
    #tambien te da un objeto series de pandas

    def obtener_generos_vistos(self):
        # for pelicula in self.peliculas_vistas:
        #         self.generos_vistos.append(pelicula["genero"])
        generos_obtenidos = [pelicula["genero"] for pelicula in self.peliculas_vistas]        
        self.generos_vistos = generos_obtenidos

        if not generos_obtenidos:
            # self.genero_preferido = "Sin preferido"
            print(f'{self.nombre} no vio ninguna película todavía.')
            return

        contador = Counter(generos_obtenidos)
        # print(contador)

        self.genero_preferido = contador.most_common(1)[0][0]

        return self.genero_preferido

        # print(f'El genero mas visto por {self.nombre} es {self.genero_preferido}')
        

    def get_generoFav(self):
        return self.genero_preferido


    def asignar_peliculasRecomendadas(self, peliculas_dict):
        return None