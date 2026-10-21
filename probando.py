# %%
# Asegúrate de tener instaladas las librerías: pip install graphviz ipython
import os
import graphviz
from IPython.display import display

# Agregamos correctamente la ruta al PATH de las variables de entorno de la sesión
os.environ["PATH"] += os.pathsep + r"C:\Program Files\Graphviz\bin"
# O si se instaló en el directorio de usuario (AppData), suele estar en:
# os.path.append(os.path.expanduser("~\\AppData\\Local\\Programs\\Graphviz\\bin"))

# Creamos un grafo dirigido básico
grafo = graphviz.Digraph(comment='Ejemplo en VS Code')

# Añadimos nodos
grafo.node('1', 'Inicio (Nodo 1)')
grafo.node('2', 'Centro (Nodo 2)')
grafo.node('3', 'Fin (Nodo 3)')

# Añadimos conexiones (aristas) con color
grafo.edge('1', '2', color='blue')
grafo.edge('2', '3', color='red')

# Mostramos el grafo usando display()
display(grafo)
# %%
