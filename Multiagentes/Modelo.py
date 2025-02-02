# Model design
import agentpy as ap
import numpy as np
import os
# Visualization
import heapq
import time
# ============== MANEJO DE COORDENADAS ==========================
def add_dir(pos: tuple, dir: tuple, grid_shape: tuple) -> tuple:
    """Añade la dirección a la posición y verifica si está dentro de los límites del grid."""
    next_pos = pos[Y] + dir[Y], pos[X] + dir[X]
    if 0 <= next_pos[Y] < grid_shape[0] and 0 <= next_pos[X] < grid_shape[1]:
        return next_pos
    else:
        return False

#  Manhattan distance heuristic
def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])
       


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
        self.weight = -1

class Spawn(ap.Agent):
    def setup(self):
        self.weight = 0

class Building(ap.Agent):
    def setup(self):
        self.weight = 0

class Stoplight(ap.Agent):
    def setup(self):
        self.change_time = self.p.change_time
        self.state = True
        self.pos = None
        self.myRoads = []
        self.weight = 0
        

    def execute(self):
        print(self.myRoads)
        self.myRoads[0].stop = self.state
        self.myRoads[1].stop = not self.state
        self.change_time -= 1
        if self.change_time == 0:
            self.state = not self.state
            self.change_time = self.p.change_time


class Road(ap.Agent):
    def setup(self):
        self.dir = None
        self.paso_peatonal = False
        self.stop = False
        self.weight = 10
        self.flag = False
       

class Peaton(ap.Agent):
    def setup(self):

        self.env = self.model.environment
        self.route = []
        self.next_step = 1
        self.respect = 1 - 0.9*self.model.random.randint(0,1) #determina de forma  aleatoria si un peatón va a obedecer las leyes de tránsito o no

    '''
    Actual action execution. d
    '''
    def execute(self):
        if self.next_step >= len(self.route):
            self.env.remove_agents(self)
            self.model.peatones.remove(self)
        else:    
            next_pos = self.route[self.next_step]
            agents = [agent for agent in self.model.environment.agents[next_pos] if isinstance(agent, Peaton)]
            if len(agents) != 0:
                pos = self.get_position()
                dir = (next_pos[0] - pos[0], next_pos[1] - pos[1])
                if dir == DOWN:
                    agents = [agent for agent in self.model.environment.get_agents_in_dir(self,[LEFT],Car)]
                    agents.append(self.model.environment.get_agents_in_dir(self,[LEFT],Peaton))
                    if len(agents) != 0:
                        self.model.environment.move_by(self,UP)
                        self.next_step -= 1
                    else:
                         self.model.environment.move_by(self,LEFT)
                elif dir == RIGHT:
                    agents = [agent for agent in self.model.environment.get_agents_in_dir(self,[DOWN],Car)]
                    agents.append(self.model.environment.get_agents_in_dir(self,[DOWN],Peaton))
                    if len(agents) != 0:
                        self.model.environment.move_by(self,LEFT)
                        self.next_step -= 1
                    else:
                         self.model.environment.move_by(self,DOWN)


            else:
                self.model.environment.move_to(self, next_pos)
                self.next_step += 1
                if self.next_step < len(self.route):
                    curr_pos = self.route[self.next_step - 1]
                    agents = [agent for agent in self.model.environment.agents[curr_pos] if isinstance(agent, Road)]
                    if len(agents) != 0:
                        agents[0].flag = False
                    next_pos = self.route[self.next_step]
                    agents = [agent for agent in self.model.environment.agents[next_pos] if isinstance(agent, Road)]
                    if len(agents) != 0:
                        agents[0].flag = True


      
    def get_position(self):
        return self.env.positions[self]

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
                                    if agent.stop == False and agent.flag == False:
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
                            if agent.stop == False and agent.flag == False:
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
        agents = self.neighbors(p_agent,len(dirs))
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
    
    
    def weighted_a_star(self, start, goal, w):
        """
        Weighted A* search algorithm that finds the optimal path from start to goal.
        - Takes into account the weight of agents in the environment.
        - Uses a weight factor `w` to balance heuristic and actual cost.

        Parameters:
        - start: Tuple (x, y) representing the starting position.
        - goal: Tuple (x, y) representing the goal position.
        - w: Weight factor for heuristic importance (default = 1.5).
        
        Returns:
        - List of tuples [(x1, y1), (x2, y2), ...] representing the path.
        - Returns None if no valid path is found.
        """

        rows, cols = self.shape
        open_set = []
        heapq.heappush(open_set, (0, start))  # (total cost, position)
        
        came_from = {}  # To reconstruct the path
        g_score = {start: 0}  # Cost from start to each node
        f_score = {start: w * heuristic(start, goal)}  # Estimated total cost (weighted)

        while open_set:
            _, current = heapq.heappop(open_set)

            if current == goal:
                #  Reconstruct and return the path
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                return path[::-1]  # Reverse path

            for dx, dy in DIRS:
                neighbor = (current[0] + dx, current[1] + dy)

                #  Ensure the neighbor is within bounds
                if not (0 <= neighbor[0] < rows and 0 <= neighbor[1] < cols):
                    continue

                #  Get the weight of the neighbor cell
                weight = 0  # Default weight if no agent is present
                agents = self.agents[neighbor]
                for agent in agents:
                    if hasattr(agent, "weight"):  # Ensure the agent has a weight attribute
                        weight = agent.weight
                        break  # Use the first valid weight found
                
                #  If weight is negative, the cell is impassable
                if weight < 0:
                    continue
                weight = weight
                #  Calculate new cost with weight adjustment
                tentative_g_score = g_score[current] + weight

                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + (w * heuristic(neighbor, goal))
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))

        return None  # No path found


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
        self.building_positions = []
        stoplight_positions = []
        stoplight_state = []
        self.spawn_positions = []
        for row in range(len(self.city)):
            for col in range(len(self.city[row])):
                if self.city[row][col] == "<" or self.city[row][col] == ">" or self.city[row][col] == "v" or self.city[row][col] == "^" or self.city[row][col] == "+":
                    road_positions.append((row,col))
                    road_direction.append(self.city[row][col])
                elif self.city[row][col] == "B":
                    self.building_positions.append((row,col))
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
        self.buildings = ap.AgentList(self,len(self.building_positions),Building)
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
        self.environment.add_agents(self.buildings,self.building_positions)
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
        self.test = [] 
        for slight in self.stoplights:
            if slight.pos == "S":
                slight.myRoads = self.environment.get_agents_in_dir(slight,[DOWN,LEFT],Road)
                roads =  self.environment.get_agents_in_dir(slight,[DOWN,(2,0) ,LEFT, (0, -2)],Road)
                for road in roads:
                    road.paso_peatonal = True
                    road.weight = 0
                    if road.dir == "^" or road.dir == "v":
                        ext = self.environment.get_agents_in_dir(road,[UP],Road)
                        ext[0].paso_peatonal = True
                    elif road.dir == "<" or road.dir == ">":
                        ext = self.environment.get_agents_in_dir(road,[RIGHT],Road)
                        ext[0].paso_peatonal = True
                    
            else:
                slight.myRoads = self.environment.get_agents_in_dir(slight,[UP,RIGHT],Road)
                roads =  self.environment.get_agents_in_dir(slight,[UP,(-2, 0) ,RIGHT, (0, 2)],Road)
                for road in roads:
                    road.paso_peatonal = True
                    road.weight = 0
                    if road.dir == "^" or road.dir == "v":
                        ext = self.environment.get_agents_in_dir(road,[DOWN],Road)
                        ext[0].paso_peatonal = True
                    elif road.dir == "<" or road.dir == ">":
                        ext = self.environment.get_agents_in_dir(road,[LEFT],Road)
                        ext[0].paso_peatonal = True 
        # Manejo de peatones
        self.peatones = ap.AgentList(self,len(self.spawn_positions),Peaton)
        self.environment.add_agents(self.peatones,self.spawn_positions)
        for peaton in self.peatones:
            peaton.route = self.environment.weighted_a_star(self.environment.positions[peaton],self.random.choice(self.building_positions), 15*peaton.respect)
        #print(self.peaton.route)
        #exit(0)

        

    
    def car_spawn(self):
        spawns = self.car_pos
        cars = []
        for pos in spawns:
            agents = self.environment.agents[pos]
            for agent in agents:
                if isinstance(agent, Car):
                    cars.append(agent)
        if self.t != 0 and len(cars) == 0:    
            if self.t % self.p.car_spawn == 0 or len(self.cars) == 0:
                new_car = ap.AgentList(self, len(spawns), Car)
                for car,dir in zip(new_car,self.car_dir):
                    car.dir = dict[dir]
                self.environment.add_agents(new_car,self.car_pos)
                self.cars.extend(new_car)           
    
    def spawn_peaton(self):
        peatones = []
        for pos in self.spawn_positions:
            agents = self.environment.agents[pos]
            for agent in agents:
                if isinstance(agent, Peaton):
                    peatones.append(agent)
        if self.t != 0 and len(peatones) == 0:   
            if self.t % self.p.p_spawn == 0 or len(self.peatones) == 0:
                nuevos_peatones = ap.AgentList(self, len(self.spawn_positions), Peaton)
                self.environment.add_agents(nuevos_peatones,self.spawn_positions)
                for peaton in nuevos_peatones:
                    peaton.route = self.environment.weighted_a_star(self.environment.positions[peaton],self.random.choice(self.building_positions), 15*peaton.respect)
                self.peatones.extend(nuevos_peatones)   

    
    
    def step(self):
        self.car_spawn()
        self.spawn_peaton()
        for stop in self.stoplights:
            stop.execute()
        for car in self.cars:
            car.execute()
        for peaton in self.peatones:
            peaton.execute()
        self.print_grid()
        if len(self.peatones) == 0:
            self.stop()
  
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
                    repr = '   '
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
                        elif isinstance(agent, Peaton):
                            if agent.respect == 1:
                                repr = " P "
                            else:
                                repr = " b "
                            break
                        elif isinstance(agent, Road):
                            if agent.paso_peatonal == True and (agent.dir == "v" or agent.dir == "^"):
                                repr = f" = "
                            elif agent.paso_peatonal == True and (agent.dir == ">" or agent.dir == "<"):
                                repr = f"| |"    
                            else:
                                repr = f" {agent.dir} "
                        elif isinstance(agent, Building):
                            repr = "■■■"
                        elif isinstance(agent, Obstacle):
                            repr = " O "
                        elif isinstance(agent, Stoplight):
                            if agent.state == True:
                                repr = " R "
                            else:
                                repr = " V "
                    row_repr.append(repr)
                else:
                    row_repr.append('   ')
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
    'car_spawn': 8,
    'p_spawn': 10,
    'change_time': 10,
    'steps': 100
}
cityModel = Model(parameters)
cityModel.run()



