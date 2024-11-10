import networkx as nx
import matplotlib.pyplot as plt
import json
import math

# Cargar datos del JSON
with open("instances/toy_instance.json", "r") as file:
    data = json.load(file)

# Crear el grafo dirigido
G = nx.DiGraph()

# Parámetros generales
capacity = data["rs_info"]["capacity"]
max_rs = data["rs_info"]["max_rs"]
stations = data["stations"]
cost_per_unit = data["cost_per_unit"]

# 1. Agregar nodos y arcos de tren al grafo
for service_id, service in data["services"].items():
    stops = service["stops"]
    demand = service["demand"][0]

    # Crear nodos para los eventos
    departure_event = f"{service_id}_D"
    arrival_event = f"{service_id}_A"

    G.add_node(departure_event, station=stops[0]["station"], time=stops[0]["time"])
    G.add_node(arrival_event, station=stops[1]["station"], time=stops[1]["time"])

    # Agregar arco de tren
    G.add_edge(
        departure_event,
        arrival_event,
        low = math.ceil(demand / capacity),  # Demanda mínima
        upper=max_rs,  # Máximo permitido por servicio
        cost=0  # Sin costo en arcos de tren
    )


# 2. Agregar arcos de traspaso dentro de cada estación
    events_by_station = {station: [] for station in stations}
    for node, attributes in G.nodes(data=True):
        events_by_station[attributes["station"]].append((node, attributes["time"]))

    for station, events in events_by_station.items():
        # Ordenar eventos por tiempo dentro de la misma estación
        events.sort(key=lambda x: x[1])
        for i in range(len(events) - 1):
            G.add_edge(
                events[i][0],
                events[i + 1][0],
                lower=0,
                upper=float('inf'),  # Sin límite superior
                cost=0  # Sin costo en arcos de traspaso
            )

# 3. Agregar arcos de trasnoche
for station, events in events_by_station.items():
    if events:
        first_event = events[0][0]
        last_event = events[-1][0]
        G.add_edge(
            last_event,
            first_event,
            lower=0,
            upper=float('inf'),  # Sin límite superior
            cost=cost_per_unit[station]  # Costo de trasnoche por unidad
        )

# 4. Resolver flujo mínimo
flow_cost, flow_dict = nx.network_simplex(G)

# Validar conectividad del grafo
if not nx.is_connected(G.to_undirected()):
    print("Advertencia: El grafo no está completamente conectado.")

# 5. Mostrar resultados en texto
print("Costo mínimo (unidades de trasnoche):", flow_cost)
print("\nFlujo por arco:")
for u, v, attributes in G.edges(data=True):
    flujo = flow_dict.get(u, {}).get(v, 0)
    print(f"{u} -> {v}: Flujo = {flujo}, Costo = {attributes['cost']}")

# 6. Visualizar el grafo con Matplotlib
plt.figure(figsize=(12, 8))

# Posicionar nodos de acuerdo a la estación y tiempo
pos = {node: (attributes["time"], stations.index(attributes["station"]))
       for node, attributes in G.nodes(data=True)}

# Dibujar nodos y etiquetas
nx.draw_networkx_nodes(G, pos, node_size=700, node_color="lightblue")
nx.draw_networkx_labels(G, pos, font_size=10)

# Dibujar arcos con etiquetas de flujo
nx.draw_networkx_edges(G, pos, edge_color="black", arrowstyle="->")
edge_labels = {(u, v): f"{flow_dict.get(u, {}).get(v, 0)}"
               for u, v in G.edges()}
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8)

# Configurar título y mostrar
plt.title("Grafo de flujo con costos y flujos")
plt.xlabel("Tiempo")
plt.ylabel("Estación (índice)")
plt.grid(True)
plt.show()

# 7. Calcular la cantidad de vagones necesarios para cada arco de tren
vagones_por_arco = {}
for u, v, attributes in G.edges(data=True):
    # Obtenemos el flujo en este arco
    flujo = flow_dict.get(u, {}).get(v, 0)
    
    # Calculamos la cantidad de vagones, asumiendo que cada vagón tiene la capacidad especificada
    if flujo > 0:
        # Número de vagones necesarios = flujo total / capacidad de cada vagón
        vagones = flujo / capacity
        vagones_por_arco[(u, v)] = vagones
    else:
        vagones_por_arco[(u, v)] = 0

# 8. Mostrar resultados de vagones
print("\nCantidad de vagones por arco:")
for (u, v), vagones in vagones_por_arco.items():
    print(f"{u} -> {v}: {vagones} vagones")
    demand = service["demand"][0]  # Verifica que esto no sea cero
    print(demand)


