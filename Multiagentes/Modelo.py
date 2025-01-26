# Model design
import agentpy as ap
import numpy as np
import os
# Visualization
import matplotlib.pyplot as plt
import IPython
import time
# ============== MANEJO DE COORDENADAS ==========================
def add_dir(pos: tuple, dir: tuple, grid_shape: tuple) -> tuple:
    """Añade la dirección a la posición y verifica si está dentro de los límites del grid."""
    next_pos = pos[Y] + dir[Y], pos[X] + dir[X]
    if 0 <= next_pos[Y] < grid_shape[0] and 0 <= next_pos[X] < grid_shape[1]:
        return next_pos
    else:
        return False



Y = 0
ROW = 0
X = 1
COL = 1
END_OF_ROAD = False



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

TURN_RIGHT = {
    UP: LEFT,
    DOWN: RIGHT,
    RIGHT: DOWN,
    LEFT: UP
    }




# ============== MANEJO DE ARCHIVOS ==========================




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
    def setup(self):
        self.change_time = self.p.change_time
        self.state = True
        self.pos = None
        self.cardinal = None
        self.myRoads = []
        

    def execute(self):
        print(self.myRoads)
        self.myRoads[0].stop = self.state
        self.myRoads[1].stop = not self.state
        if self.change_time == 0:
            self.change_time = self.p.change_time
        self.change_time -= 1
        if self.change_time == 0:
            self.state = not self.state


class Road(ap.Agent):
    def setup(self):
        self.dir = None
        self.paso_peatonal = False
        self.stop = False
        self.turn = None
       

class Peaton(ap.Agent):
    def setup(self):
        self.goal = None

class Car(ap.Agent):
    def setup(self):
        self.dir = None
        self.prev_dir = None
    
    def move_car(self):
        """Mueve el coche en la dirección que tiene asignada"""
        next_pos = None
        pos = self.model.environment.positions[self]
        possible_moves = self.model.environment.possible_moves_car(pos,self)
        for agent in self.model.environment.agents[pos]:
            if len(possible_moves) == 1:
                    next_pos = add_dir(pos,self.dir,self.model.environment.shape)
                    if next_pos != False:
                        agents = [agent for agent in self.model.environment.agents[next_pos] if isinstance(agent, Car) or isinstance(agent, Peaton)]
                        if len(agents) != 0:
                            next_pos = None
                        else:
                            for agent in self.model.environment.agents[next_pos]:
                                if isinstance(agent, Road):
                                    if agent.stop == False:
                                        return next_pos
                                    else:
                                        next_pos = None
                                        return next_pos
                    else:
                        return False
            elif len(possible_moves) == 2:
                next_dir = self.model.random.choice(possible_moves)
                print(next_dir)
                next_pos = add_dir(pos,next_dir,self.model.environment.shape)
                agents = [agent for agent in self.model.environment.agents[next_pos] if isinstance(agent, Car) or isinstance(agent, Peaton)]
                if len(agents) != 0:
                    next_pos = None
                else:
                    for agent in self.model.environment.agents[next_pos]:
                        if isinstance(agent, Road):
                            if agent.stop == False:
                                return next_pos
                            else:
                                next_pos = None
                    return next_pos    
            else:
                return False        

        
    def execute(self):
        next_pos = self.move_car()
        if next_pos != False:
            if next_pos != None:
                self.model.environment.move_to(self,next_pos)
                for agent in self.model.environment.agents[next_pos]:
                    if isinstance(agent, Road):
                        if agent.dir == "+":
                            self.dir = self.prev_dir
                        else:
                            self.prev_dir = self.dir
                            self.dir = dict[agent.dir]
            else:
                pass
        else:
            self.model.environment.remove_agents(self)
            self.model.cars.remove(self)


class City(ap.Grid):
    def setup(self):
        pass
    
    def distance (self,from_pos,to_pos) :
        """Calcula la distancia entre dos puntos, retorna una tupla (steps,distance Y,distance X)
          steps: pasos requeridos para llegar
          distance Y: distancia en el eje Y
          distance X: distancia en el eje X"""
        y_distance = abs(to_pos[Y] - from_pos[Y]) 
        x_distance = abs(to_pos[X] - from_pos[X])
        steps = y_distance + x_distance
        return (steps,y_distance,x_distance)

    def get_agents_in_dir (self,p_agent,dirs:list, agent_class) -> list:
        """Obtiene los agentes en la dirección"""
        agents = self.neighbors(p_agent,1)
        agents_in_dir = []
        pos = self.positions[p_agent]
        possible_dirs = [add_dir(pos, dir, self.shape) for dir in dirs]
        for agent in agents:
            if isinstance(agent, agent_class):
                if self.positions[agent] in possible_dirs:
                    agents_in_dir.append(agent)
        return agents_in_dir
    def possible_moves_car(self,current_position, car):
        """Determina los posibles movimientos validos en el ambiente para un coche.
           Retorna una lista de tuplas (x,y) que representan direcciones posibles para el coche.
        """
        possible_moves = []
        agents = self.agents[current_position]
        road = None
        for agent in agents:
            if isinstance(agent, Road):
                road = agent
                break   
        if road.dir == "+":
                possible_moves = [car.dir]
                dir_check = self.agents[add_dir(current_position,TURN_RIGHT[car.dir],self.shape)]
                for agent in dir_check:
                    if isinstance(agent, Road):
                        if agent.dir != "+": # Si la dirección es diferente a un cruce
                            if dict[agent.dir] == TURN_RIGHT[car.dir]:
                                possible_moves.append(TURN_RIGHT[car.prev_dir])
                return possible_moves
        else:
                possible_moves = [car.dir]
                return possible_moves

            
        
        
        

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
            if state == "S":
                stop.state = True
                stop.pos = state
            else:
                stop.state = False
                stop.pos = state
        self.environment.add_agents(self.roads,road_positions)
        self.environment.add_agents(self.obstacles,obstacle_positions)
        self.environment.add_agents(self.stoplights,stoplight_positions)
        self.environment.add_agents(self.buildings,building_positions)
        self.environment.add_agents(self.spawns,self.spawn_positions)
        car_list = []
        car_dir = []
        for row in range(len(self.city)):
            for col in range(len(self.city[row])):
                if self.city[row][col] == "v" and row == 0:
                     new_car = (row,col)
                     car_list.append(new_car)
                     car_dir.append(self.city[row][col])
                elif self.city[row][col] == "^" and row == len(self.city)-1:
                    new_car = (row,col)
                    car_list.append(new_car)
                    car_dir.append(self.city[row][col])
                elif self.city[row][col] == "<" and col == len(self.city[row])-1:
                    new_car = (row,col)
                    car_list.append(new_car)
                    car_dir.append(self.city[row][col])
                elif self.city[row][col] == ">" and col == 0:
                    new_car = (row,col)
                    car_list.append(new_car)
                    car_dir.append(self.city[row][col])
        self.cars = ap.AgentList(self,len(car_list),Car)
        self.car_pos = car_list
        self.car_dir = car_dir
        for car,dir in zip(self.cars,car_dir):
            car.dir = dict[dir]
        self.environment.add_agents(self.cars,car_list) 
        for slight in self.stoplights:
            if slight.pos == "S":
                slight.myRoads = self.environment.get_agents_in_dir(slight,[DOWN,LEFT],Road) 
            else:
                slight.myRoads = self.environment.get_agents_in_dir(slight,[UP,RIGHT],Road)
        
        

    
    def car_spawn(self):
        if self.t != 0:    
            if self.t % self.p.spawn == 0 or len(self.cars) == 0:
                spawns = self.car_pos
                new_car = ap.AgentList(self, len(spawns), Car)
                for car,dir in zip(new_car,self.car_dir):
                    car.dir = dict[dir]
                self.environment.add_agents(new_car,self.car_pos)
                self.cars.extend(new_car)           
    
    def spawn_peaton(self,spawn):
        if self.t != 0:   
            if self.t % self.p.spawn == 0 or len(self.peatones) == 0:
                nuevos_peatones = ap.AgentList(self, len(self.spawn_positions), Peaton)
                self.environment.add_agents(nuevos_peatones,self.spawn_positions)
                self.peatones.extend(nuevos_peatones)   

    # Manejo de peatones
        self.peatones = ap.AgentList(self, len(self.spawn_positions), Peaton)
    
    def step(self):
         
        self.car_spawn()
        for stop in self.stoplights:
            stop.execute()
        for car in self.cars:
            car.execute()
        self.print_grid()
  
    def print_grid(self):
        """Imprimir el estado del grid con sus agentes."""
        os.system('cls')
        grid_repr = []
        rows, cols = self.environment.shape
        for row in range(rows):
            row_repr = [f'{str(row).rjust(2)} - ']
            for col in range(cols):
                agents = self.environment.agents[(row, col)]
                if agents:
                    repr = '...'
                    for agent in agents:
                        if isinstance(agent, Car):
                            if agent.dir == RIGHT:
                                repr = "C →"
                            elif agent.dir == LEFT:
                                repr = "← C"
                            elif agent.dir == UP:
                                repr = "C ↑"
                            elif agent.dir == DOWN:
                                repr = "C ↓"
                            break
                        elif isinstance(agent, Road):
                            repr = f" {agent.dir} "
                        elif isinstance(agent, Building):
                            repr = " B "
                        elif isinstance(agent, Obstacle):
                            repr = " O "
                        elif isinstance(agent, Stoplight):
                            if agent.state == True:
                                repr = " R "
                            else:
                                repr = " V "
                        elif isinstance(agent, Peaton):
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
        time.sleep(1)

file_path = "mapa.txt"
city = text_to_matrix(file_path)
parameters = {
    'city': city,
    'steps': 35,
    'spawn': 8,
    'change_time': 10
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


