import json
import networkx as nx


def main():
	filename = "../instances/toy_instance.json"
	filename = "../instances/retiro-tigre-semana.json"

	with open(filename) as json_file:
		data = json.load(json_file)

	# test file reading

	for service in data["services"]:
		print(service, data["services"][service]["stops"])

if __name__ == "__main__":
	main()
