import networkx as nx
import matplotlib.pyplot as plt
import json
import math

# Cargar datos del JSON
with open("instances/retiro-tigre-semana.json", "r") as file:
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

    # Crear nodos para los eventos con demanda positiva o negativa según el tipo
    departure_event = f"{service_id}_D"
    arrival_event = f"{service_id}_A"
    
    G.add_node(departure_event, station=stops[0]["station"], time=stops[0]["time"], demand=math.ceil(demand / capacity))
    G.add_node(arrival_event, station=stops[1]["station"], time=stops[1]["time"], demand=-math.ceil(demand / capacity))

    # Agregar arco de tren con demanda mínima y capacidad máxima
    G.add_edge(
        departure_event,
        arrival_event,
        lower=math.ceil(demand / capacity),  # Demanda mínima
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

# 3. Agregar arcos de trasnoche con capacidad ajustada
for station, events in events_by_station.items():
    if events:
        first_event = events[0][0]
        last_event = events[-1][0]
        
        G.add_edge(
            last_event,
            first_event,
            lower=0,
            upper=1e10,  # Capacidad de trasnoche
            cost=cost_per_unit[station]  # Costo de trasnoche por unidad
        )

# 4. Resolver flujo mínimo y calcular costos
flow_cost, flow_dict = nx.capacity_scaling(G, demand='demand', weight='cost')

# Validar conectividad del grafo
if not nx.is_connected(G.to_undirected()):
    print("Advertencia: El grafo no está completamente conectado.")

# 5. Mostrar resultados en texto
print("Costo mínimo (unidades de trasnoche):", flow_cost)
print("\nFlujo por arco:")
for u, v, attributes in G.edges(data=True):
    flujo = flow_dict.get(u, {}).get(v, 0)
    print(f"{u} -> {v}: Flujo = {flujo}, Costo = {attributes['cost']}")

# 6. Identificar estaciones recorridas y trasnoche para cada tren
for service_id, service in data["services"].items():
    recorrido = []
    trasnoche_station = None

    stops = service["stops"]
    departure_event = f"{service_id}_D"
    arrival_event = f"{service_id}_A"
    
    # Rastrear estaciones recorridas basadas en el flujo
    for u, destinations in flow_dict.items():
        if u.startswith(service_id):
            for v, flujo in destinations.items():
                if flujo > 0 and G.nodes[u]['station'] not in recorrido:
                    recorrido.append(G.nodes[u]['station'])
                if flujo > 0 and G.nodes[v]['station'] not in recorrido:
                    recorrido.append(G.nodes[v]['station'])

    # Verificar si el tren trasnocha en alguna estación
    for u, destinations in flow_dict.items():
        for v, flujo in destinations.items():
            if flujo > 0 and ((u == arrival_event and v == departure_event) or (u == departure_event and v == arrival_event)):
                trasnoche_station = G.nodes[v]['station']
                break

    print(f"\nTren {service_id} recorre las estaciones: {', '.join(recorrido)}")
    if trasnoche_station:
        print(f"Tren {service_id} trasnocha en la estación: {trasnoche_station}")
    else:
        print(f"Tren {service_id} no tiene trasnoche registrado.")

# 7. Visualizar el grafo con Matplotlib
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