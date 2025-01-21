# Model design
import agentpy as ap
import numpy as np

# Visualization
import matplotlib.pyplot as plt
import IPython
import time
# ============== MANEJO DE COORDENADAS ==========================
def add_dir (pos:tuple,dir:tuple) -> tuple:
        """Añade la dirección a la posicion"""
        next_dir = pos[Y]+dir[Y],pos[X]+dir[X]
        return(next_dir)



Y = 0
ROW = 0
X = 1
COL = 1




UP = (-1,0)
DOWN = (1,0)
LEFT = (0,-1)
RIGHT = (0,1)
dict =     {"<" : LEFT,
            ">" : RIGHT,
            "^" : UP,
            "v" : DOWN,
            "+ ": "intersection",
            "B" : "building",
            "S" : "stoplight",
            "s" : "stoplight",
            "O" : "obstacle",
                }

DIRS = [UP,DOWN,LEFT,RIGHT]




def text_to_matrix(file_path, delimiter=None):
    """
    Convierte un archivo de texto en una matriz.

    Args:
        file_path (str): Ruta al archivo de texto.
        delimiter (str, optional): Delimitador para separar columnas. Si es None, se usa cualquier espacio en blanco.

    Returns:
        list: Matriz representada como una lista de listas.
    """
    matrix = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                # Divide cada línea en una lista de caracteres
                matrix.append(list(line.strip()))
    except FileNotFoundError:
        print(f"Error: El archivo '{file_path}' no fue encontrado.")
    except Exception as e:
        print(f"Error: {e}")

    return matrix

class Obstacle(ap.Agent):
    def setup(self):
        pass

class Spawn(ap.Agent):
    def setup(self):
        pass

class Building(ap.Agent):
    def setup(self):
        pass

class Stoplight(ap.Agent):
    def setup(self, state="s"):
        self.change_time = 15
        self.state = True
        if state == "S":
            False
        else:
            True
        self.myRoads = []
    
    def execute(self):
        if self.change_time == 0:
            self.change_time = 15
        self.change_time -= 1
        if self.change_time == 0:
            self.state = not self.state


class Road(ap.Agent):
    def setup(self, dir="<"):
        self.dir = dir
        self.paso_peatonal = False
       

class Peaton(ap.Agent):
    def setup(self):
        self.goal = None


class City(ap.Grid):
    def setup(self):
        pass

    def get_agents_in_dir (self,p_agent,dirs:list, agent_class) -> list:
        """Obtiene los agentes en la dirección"""
        agents = self.neighbors(p_agent,1)
        agents_in_dir = []
        pos = self.positions[p_agent]
        possible_dirs = [add_dir(pos, dir) for dir in dirs]
        for agent in agents:
            if isinstance(agent, agent_class):
                if self.positions[agent] in possible_dirs:
                    agents_in_dir.append(agent)


class Model(ap.Model):
    """Modelo que define el ambiente y los agentes."""
    def setup(self):
        # --- Crear el grid
        self.city = self.p.city
        self.cols = len(self.city[0])
        self.rows = len(self.city)
        self.environment = City(self, shape=(self.cols,self.rows), track_empty=True)
        road_positions = []
        road_direction = []
        obstacle_positions = []
        building_positions = []
        stoplight_positions = []
        stoplight_state = []
        self.spawn_positions = []
        for row in range(len(self.city)):
            for col in range(len(self.city[row])):
                if self.city[row][col] == "<" or self.city[row][col] == ">" or self.city[row][col] == "v" or self.city[row][col] == "^" or self.city[row][col] == "+":
                    road_positions.append((row,col))
                    road_direction.append(self.city[row][col])
                elif self.city[row][col] == "B":
                    building_positions.append((row,col))
                elif self.city[row][col] == "S" or self.city[row][col] == "s":
                    stoplight_positions.append((row,col))
                    stoplight_state.append(self.city[row][col])
                elif self.city[row][col] == "O":
                    obstacle_positions.append((row,col))
                elif self.city[row][col] == "P":
                    self.spawn_positions.append((row,col))
        self.roads = ap.AgentList(self,len(road_positions),Road)
        self.obstacles = ap.AgentList(self,len(obstacle_positions),Obstacle)
        self.stoplights = ap.AgentList(self,len(stoplight_positions),Stoplight)
        self.buildings = ap.AgentList(self,len(building_positions),Building)
        self.spawns = ap.AgentList(self,len(self.spawn_positions),Spawn)
        for road,dir in zip(self.roads,road_direction):
            road.dir = dir
        for stop,state in zip(self.stoplights,stoplight_state):
            stop.state = state
        self.environment.add_agents(self.roads,road_positions)
        self.environment.add_agents(self.obstacles,obstacle_positions)
        self.environment.add_agents(self.stoplights,stoplight_positions)
        self.environment.add_agents(self.buildings,building_positions)
        self.environment.add_agents(self.spawns,self.spawn_positions)
        for slight in self.stoplights:
            if slight.state == "S":
                slight.myRoads = self.environment.get_agents_in_dir(slight,[RIGHT,LEFT],Road) 
            else:
                slight.myRoads = self.environment.get_agents_in_dir(slight,[UP,DOWN],Road)

    # Manejo de peatones
        self.peatones = ap.AgentList(self, len(self.spawn_positions), Peaton)
    
    def step(self):
        """if self.t % self.p.spawn == 0: #Se considera flujo constante de peatones para estadística, pero pudo ser aleatoria
            nuevos_peatones = ap.AgentList(self, len(self.spawn_positions), Peaton)
            self.environment.add_agents(nuevos_peatones,self.spawn_positions)
            self.peatones.extend(nuevos_peatones)"""
        print(self.stoplights[2].myRoads)
        self.print_grid()
  
    def print_grid(self):
        """Imprimir el estado del grid con sus agentes."""
        time.sleep(1)
        grid_repr = []
        rows, cols = self.environment.shape
        for row in range(rows):
            row_repr = [f'{str(row).rjust(2)} - ']
            for col in range(cols):
                agents = self.environment.agents[(row, col)]
                if agents:
                    repr = '...'
                    for agent in agents:
                        if isinstance(agent, Road):
                            repr = f" {agent.dir} "
                        elif isinstance(agent, Building):
                            repr = " B "
                        elif isinstance(agent, Obstacle):
                            repr = " O "
                        elif isinstance(agent, Stoplight):
                            repr = " S "
                        if isinstance(agent, Peaton):
                            repr = " P "
                    row_repr.append(repr)
                else:
                    row_repr.append('...')
            grid_repr.append(" ".join(row_repr))
        print("\n")
        header = ['    ']
        for col in range(cols):
            header.append(str(col).rjust(3))
        print(" ".join(header))
        for line in grid_repr:
            print(line)
        print("\n")

file_path = "mapa.txt"
city = text_to_matrix(file_path)
parameters = {
    'city': city,
    'steps': 2,
    'spawn': 3, 
}
cityModel = Model(parameters)
cityModel.run()

"""
 neighbors = self.model.environment.neighbors(self,1)
        if dir != "+":
            for neighbor in neighbors:
                if isinstance(neighbor,  Stoplight):
                    self.paso_peatonal = True

"""


