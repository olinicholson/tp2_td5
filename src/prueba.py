import json
import networkx as nx
import matplotlib.pyplot as plt
import math


def crear_tupla(diccionario, demanda): # Creo tuplas a partir de cada evento, para crear nodos (tipo inmutable)
	return (diccionario['time'], diccionario['station'], diccionario['type'], math.ceil(demanda)) #Tiempo / Estación / Tipo / Demanda (Ceil para calcular para arriba)

def crear_tupla_circ(diccionario): # Creo tuplas a partir de cada evento, para crear nodos (tipo inmutable)
	return (diccionario['time'], diccionario['station'], diccionario['type']) #Tiempo / Estación / Tipo / Demanda (Ceil para calcular para arriba)

def positions(retiro, tigre): # Para graficar, separa retiro de tigre en el eje X,Y
	vr = {}
	for i, k, p in zip(retiro, tigre, range(1,len(retiro)+1)):
		vr[i] = (0, p)
		vr[k] = (1, p)
	return vr


def ordenar_tuplas_por_numero(lista): # Ordenar listas según tiempo
	return sorted(lista, key=lambda x: x[0]) # Ordeno listas de nodos, para que sea creaciente en Numero




def main_modelado_circulacion(): # Modelado de la red como circulación
	filename = "instances/toy_instance.json"
	#filename = "instances/retiro-tigre-semana.json"

	with open(filename) as json_file: # Cargo data
		data = json.load(json_file)
	retiro = [] # Guardo Nodos retiro
	tigre = [] # Guardo Nodos tigre
	nodos = [] # Guardo todos los nodos

	#-----| Limpieza de datos |-----
	for service in data["services"]: # Itero sobre la data para obtener listas de cada nodo que representa la llegada/salida de un servicio
		for place in data["services"][service]["stops"]:
			nodos.append(crear_tupla_circ(place)) # Agregamos todos a nodos
			if place['station'] == 'Retiro': # Separamos en dos listas 'retiro' y 'tigre'
				retiro.append(crear_tupla_circ(place)) # Creo tupla (tipo inmutable) con caracteristicas del nodo
			else:
				tigre.append(crear_tupla_circ(place)) # Creo tupla (tipo inmutable) con caracteristicas del nodo	
	#------------------------------

	retiro = ordenar_tuplas_por_numero(retiro)  # Ordeno nodos (Para crear aristas)
	tigre = ordenar_tuplas_por_numero(tigre) # Ordeno nodos (Para crear aristas)
	pos = positions(retiro, tigre) # Defino posiciones (Unicamente para visualizar)

	G = nx.DiGraph() # Creamos Grafo G

	#----| Agregamos nodos al grafo, definiendo su demanda = 0 |----
	for i in range(0,len(retiro)): # Itero sobre retiro
		G.add_node(retiro[i],demand=0) # Agrego nodo

	for i in range(0,len(tigre)): # Itero sobre tigre
		G.add_node(tigre[i],demand=0) # Agrego nodo
	#---------------------------------------------------------------

	#----| Agregamos aristas de traspaso |----
	for i in range(0,len(retiro)-1): # Itero sobre retiro
		G.add_edge(retiro[i],retiro[i+1], lower_bound = 0, weight = 0, capacity = 1e10, color='blue') # Agrego arista n -> n+1 c/ costo 0 y capacidad infinita
	for i in range(0,len(tigre)-1): # Itero sobre tigre
		G.add_edge(tigre[i],tigre[i+1], lower_bound = 0, weight = 0, capacity = 1e10, color='blue') # Agrego arista n -> n+1 c/ costo 0 y capacidad infinita
	#-----------------------------------------

	#----| Agregamos aristas de tren |----
	for service in data["services"]: # Itero sobre servicios
		low = math.ceil(data["services"][service]["demand"][0]/data["rs_info"]['capacity']) # Definimos cota inferior
		temp = [] # Creo lista temporal
		for place in data["services"][service]["stops"]:  # Para cada servicio agrego amba información del nodo a la lista
			temp.append(crear_tupla_circ(place))
		G.add_edge(temp[0], temp[1], lower_bound = low, weight = 0, upper_bound=data["rs_info"]['max_rs'], color='green') # Agrego arista c/ peso 0 y capacidad máxima definida en JSON
	#-------------------------------------

	#----| Agregamos aristas de trasnoche |----
	G.add_edge(retiro[-1],retiro[0], lower_bound = 0, weight = 1, capicity = 1e10, color='red') # Agrego individualmente arísta n->1 c/ peso 1 (modificable con JSON) y capacidad infinita
	G.add_edge(tigre[-1],tigre[0], lower_bound = 0, weight = 1, capicity = 1e10, color='red') # Agrego individualmente arísta n->1 c/ peso 1 (modificable con JSON) y capacidad infinita
	#------------------------------------------

	edge_colors = [G[u][v]['color'] for u, v in G.edges()]  # Obtengo lista de colores de arístas
	nx.draw(G, with_labels=True, font_weight='bold', pos=pos, edge_color=edge_colors, connectionstyle='arc3, rad = 0.2')
	plt.show()  # Dibujo grafo


def main_modelado_cost_min(filename): # Modelado de la red como costo mínimo

	with open(filename) as json_file: # Cargo data
		data = json.load(json_file)
	retiro = [] # Guardo Nodos retiro
	tigre = [] # Guardo Nodos tigre
	nodos = [] # Guardo todos los nodos

	#-----| Limpieza de datos |-----
	for service in data["services"]: # Itero sobre la data para obtener listas de cada nodo que representa la llegada/salida de un servicio
		for place in data["services"][service]["stops"]:
			demand = (data["services"][service]["demand"][0]/data["rs_info"]['capacity']) #Defino cota inferior que será utilizada para modelar como costo minimo
			nodos.append(crear_tupla(place, demand)) # Agregamos todos a nodos
			if place['station'] == 'Retiro': # Separamos en dos listas 'retiro' y 'tigre'
				retiro.append(crear_tupla(place, demand)) # Creo tupla (tipo inmutable) con caracteristicas del nodo
			else:
				tigre.append(crear_tupla(place, demand)) # Creo tupla (tipo inmutable) con caracteristicas del nodo
	#------------------------------

	retiro = ordenar_tuplas_por_numero(retiro)  # Ordeno nodos (Para crear aristas)
	tigre = ordenar_tuplas_por_numero(tigre)  # Ordeno nodos (Para crear aristas)
	pos = positions(retiro, tigre) # Defino posiciones (Unicamente para visualizar)

	G = nx.DiGraph() # Creamos Grafo G

	#----| Agregamos nodos al grafo, definiendo su demanda (imbalance) para realizar costo mínimo |----

	for i in range(0,len(retiro)): # Itero sobre retiro
		if(retiro[i][2]=='D'): # Si es D (Salida)
			G.add_node(retiro[i],demand=(retiro[i][3])) # Agrego nodo con demanda positiva
		else: # Caso contrario
			G.add_node(retiro[i],demand=(-retiro[i][3])) # Agrego nodo con demanda negativa

	for i in range(0,len(tigre)): # Itero sobre tigre
		if(tigre[i][2]=='D'): # Si es D (Salida)
			G.add_node(tigre[i],demand=(tigre[i][3])) # Agrego nodo con demanda positiva
		else: # Caso contrario
			G.add_node(tigre[i],demand=(-tigre[i][3])) # Agrego nodo con demanda negativa

	#---------------------------------------------------------------------------------------------------

	#----| Agregamos aristas de traspaso |----
	for i in range(0,len(retiro)-1): # Itero sobre retiro
		G.add_edge(retiro[i],retiro[i+1], weight = 0, capacity = 1e10, color='blue') # Agrego arista n -> n+1 c/ costo 0 y capacidad infinita

	for i in range(0,len(tigre)-1): # Itero sobre tigre
		G.add_edge(tigre[i],tigre[i+1], weight = 0, capacity = 1e10, color='blue') # Agrego arista n -> n+1 c/ costo 0 y capacidad infinita
	#-----------------------------------------

	#----| Agregamos aristas de tren |----
	for service in data["services"]: # Itero sobre servicios
		temp = [] # Creo lista temporal
		for place in data["services"][service]["stops"]: # Para cada servicio agrego amba información del nodo a la lista
			temp.append(crear_tupla(place,(data["services"][service]["demand"][0]/data["rs_info"]['capacity'])))
		G.add_edge(temp[0], temp[1], weight=0, capacity = data["rs_info"]['max_rs']-(data["services"][service]["demand"][0]/data["rs_info"]['capacity']), color='green') # Agrego arista c/ peso 0 y capacidad máxima definida en JSON
	#-------------------------------------

	#----| Agregamos aristas de trasnoche |----
	G.add_edge(retiro[-1],retiro[0], weight = 1, capacity = 1e10, color='red') # Agrego individualmente arísta n->1 c/ peso 1 (modificable con JSON) y capacidad infinita
	G.add_edge(tigre[-1],tigre[0], weight = 1, capacity = 1e10, color='red') # Agrego individualmente arísta n->1 c/ peso 1 (modificable con JSON) y capacidad infinita
	#------------------------------------------

	edge_colors = [G[u][v]['color'] for u, v in G.edges()] # Obtengo lista de colores de arístas
	nx.draw(G, with_labels=True, font_weight='bold', pos=pos, edge_color=edge_colors, connectionstyle='arc3, rad = 0.2') # Dibujo grafo
	flowCost, flow_dict = nx.capacity_scaling(G, demand='demand', weight='weight') # Obtengo costo y flujos
	print('Cantidad total de trenes: ',flowCost)
	print('Flujo de Retiro: ',flow_dict[retiro[-1]],' / Flujo de Tigre: ' ,flow_dict[tigre[-1]])
	print('\n')
	#plt.show() # Grafico



def main_modelado_cost_min_restricciones(filename, sede, restriccion): # Modelado de la red como costo mínimo

	with open(filename) as json_file: # Cargo data
		data = json.load(json_file)
	retiro = [] # Guardo Nodos retiro
	tigre = [] # Guardo Nodos tigre
	nodos = [] # Guardo todos los nodos

	#-----| Limpieza de datos |-----
	for service in data["services"]: # Itero sobre la data para obtener listas de cada nodo que representa la llegada/salida de un servicio
		for place in data["services"][service]["stops"]:
			demand = (data["services"][service]["demand"][0]/data["rs_info"]['capacity']) #Defino cota inferior que será utilizada para modelar como costo minimo
			nodos.append(crear_tupla(place, demand)) # Agregamos todos a nodos
			if place['station'] == 'Retiro': # Separamos en dos listas 'retiro' y 'tigre'
				retiro.append(crear_tupla(place, demand)) # Creo tupla (tipo inmutable) con caracteristicas del nodo
			else:
				tigre.append(crear_tupla(place, demand)) # Creo tupla (tipo inmutable) con caracteristicas del nodo
	#------------------------------

	retiro = ordenar_tuplas_por_numero(retiro)  # Ordeno nodos (Para crear aristas)
	tigre = ordenar_tuplas_por_numero(tigre)  # Ordeno nodos (Para crear aristas)
	pos = positions(retiro, tigre) # Defino posiciones (Unicamente para visualizar)

	G = nx.DiGraph() # Creamos Grafo G

	#----| Agregamos nodos al grafo, definiendo su demanda (imbalance) para realizar costo mínimo |----

	for i in range(0,len(retiro)): # Itero sobre retiro
		if(retiro[i][2]=='D'): # Si es D (Salida)
			G.add_node(retiro[i],demand=(retiro[i][3])) # Agrego nodo con demanda positiva
		else: # Caso contrario
			G.add_node(retiro[i],demand=(-retiro[i][3])) # Agrego nodo con demanda negativa

	for i in range(0,len(tigre)): # Itero sobre tigre
		if(tigre[i][2]=='D'): # Si es D (Salida)
			G.add_node(tigre[i],demand=(tigre[i][3])) # Agrego nodo con demanda positiva
		else: # Caso contrario
			G.add_node(tigre[i],demand=(-tigre[i][3])) # Agrego nodo con demanda negativa

	#---------------------------------------------------------------------------------------------------

	#----| Agregamos aristas de traspaso |----
	for i in range(0,len(retiro)-1): # Itero sobre retiro
		G.add_edge(retiro[i],retiro[i+1], weight = 0, capacity = 1e10, color='blue') # Agrego arista n -> n+1 c/ costo 0 y capacidad infinita

	for i in range(0,len(tigre)-1): # Itero sobre tigre
		G.add_edge(tigre[i],tigre[i+1], weight = 0, capacity = 1e10, color='blue') # Agrego arista n -> n+1 c/ costo 0 y capacidad infinita
	#-----------------------------------------

	#----| Agregamos aristas de tren |----
	for service in data["services"]: # Itero sobre servicios
		temp = [] # Creo lista temporal
		for place in data["services"][service]["stops"]: # Para cada servicio agrego amba información del nodo a la lista
			temp.append(crear_tupla(place,(data["services"][service]["demand"][0]/data["rs_info"]['capacity'])))
		G.add_edge(temp[0], temp[1], weight=0, capacity = data["rs_info"]['max_rs']-(data["services"][service]["demand"][0]/data["rs_info"]['capacity']), color='green') # Agrego arista c/ peso 0 y capacidad máxima definida en JSON
	#-------------------------------------

	#----| Agregamos aristas de trasnoche |----
	if(sede=='Retiro'):
		G.add_edge(retiro[-1],retiro[0], weight = 1, capacity = restriccion, color='red') # Agrego individualmente arísta n->1 c/ peso 1 (modificable con JSON) y capacidad restringida
		G.add_edge(tigre[-1],tigre[0], weight = 1, capacity = 1e10, color='red') # Agrego individualmente arísta n->1 c/ peso 1 (modificable con JSON) y capacidad infinita
	#G.add_edge(retiro[-1],tigre[0], weight = 1, capacity = 1e10, color='red') # Descomentar si se quiere probar, es arista de solución propuesta en informe
	else:
		G.add_edge(retiro[-1],retiro[0], weight = 1, capacity = 1e10, color='red') # Agrego individualmente arísta n->1 c/ peso 1 (modificable con JSON) y capacidad infinita
		G.add_edge(tigre[-1],tigre[0], weight = 1, capacity = restriccion, color='red') # Agrego individualmente arísta n->1 c/ peso 1 (modificable con JSON) y capacidad restringida
		#G.add_edge(tigre[-1],retiro[0], weight = 1, capacity = 1e10, color='red') # Descomentar si se quiere probar, es arista de solución propuesta en informe
	#------------------------------------------

	edge_colors = [G[u][v]['color'] for u, v in G.edges()] # Obtengo lista de colores de arístas
	nx.draw(G, with_labels=True, font_weight='bold', pos=pos, edge_color=edge_colors, connectionstyle='arc3, rad = 0.2') # Dibujo grafo
	flowCost, flow_dict = nx.capacity_scaling(G, demand='demand', weight='weight') # Obtengo costo y flujos
	print('Cantidad total de trenes: ',flowCost)
	print('Flujo de Retiro: ',flow_dict[retiro[-1]],' / Flujo de Tigre: ',flow_dict[tigre[-1]])
	print('\n')

if __name__ == "__main__":


	#---- Dataset Toy --------------
	print('Dataset Toy')
	main_modelado_cost_min("instances/toy_instance.json")
	#-------------------------------
	''' 
	#---- Dataset Real -------
	print('Dataset Real')
	main_modelado_cost_min("instances/retiro-tigre-semana.json")
	#-------------------------------
'''