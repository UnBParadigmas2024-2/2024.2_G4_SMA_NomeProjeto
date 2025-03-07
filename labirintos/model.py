import mesa
from mesa.space import MultiGrid
from labirintos.parse_maps import parse_map_file
from labirintos.agents.runner import RunnerAgent
from labirintos.agents.enemy import EnemyAgent
from labirintos.agents.static_agents import WallAgent, ExitAgent, StartAgent
from labirintos.agents.key import KeyAgent
from labirintos.agents.key_collector import KeyCollectorAgent
from labirintos.agents.food import FoodAgent

RUNNERS_COUNT = 10
maze_maps = [
        "maps/map1.txt",
        "maps/map2.txt",
        "maps/map3.txt"
    ]
level = 0

class MazeModel(mesa.Model):
    def __init__(self, maze_map_path=maze_maps[level], runners_count=RUNNERS_COUNT, seed=None) -> None:
        super().__init__(seed=seed)
        
        maze = parse_map_file(maze_map_path)
        self.grid = MultiGrid(maze.width, maze.height, torus=False)
        self.pheromones = {}
        self.AGENTS_OUT = 0
        
        # print para verificar posições de comida
        print(f"Inicializando {len(maze.food)} posições de comida:")
        for pos in maze.food:
            food_agent = FoodAgent(self)
            self.grid.place_agent(food_agent, pos)
            print(f"Comida colocada em {pos}")

        # Coloca as paredes no mapa
        for pos in maze.walls:
            self.grid.place_agent(WallAgent(self), pos)

        # Coloca os inimigos no mapa
        for pos in maze.enemies:
            self.grid.place_agent(EnemyAgent(self, maze, pos), pos)

        # Coloca os runners no mapa
        for _ in range(runners_count):
            self.grid.place_agent(RunnerAgent(self, maze), maze.start_pos)

        # Coloca os agentes de início e saída no mapa
        self.grid.place_agent(StartAgent(self), maze.start_pos)
        self.grid.place_agent(ExitAgent(self), maze.exit_pos)

        # Coloca a chave no mapa
        self.key = KeyAgent(self)
        self.grid.place_agent(self.key, maze.key_pos)

        # Coloca os coletores
        for _ in range(1,3):
            self.key_collector = KeyCollectorAgent(self)
            self.grid.place_agent(self.key_collector, maze.start_pos)

    def reposition_key(self, key_agent):
        """Reposiciona a chave em uma posição aleatória."""
        # Gera uma posição aleatória válida
        while True:
            new_position = (self.random.randrange(self.grid.width), self.random.randrange(self.grid.height))
            # Verifica se a célula está vazia
            if self.grid.is_cell_empty(new_position):
                self.grid.move_agent(key_agent, new_position)
                print(f"Chave reposicionada para {new_position}")
                break

    def step(self) -> None:
        global level
        # Executa uma etapa do modelo, atualizando o estado de todos os agentes
        self.move_happened = False
        self.agents_by_type[EnemyAgent].do("walk")
        self.agents_by_type[RunnerAgent].do("walk")
        self.agents_by_type[KeyCollectorAgent].do("walk")

        total_runners = len(self.agents_by_type[RunnerAgent])
        
        if total_runners <= RUNNERS_COUNT/2:
            self.running = False
            print("A metade dos runners morreu, você perdeu!")
        elif self.AGENTS_OUT == total_runners:
            level += 1
            if level < len(maze_maps):
                print(f"Todos os runners saíram do labirinto! Avançando para o nível {level + 1}...")
                self.running = False
                next_map = maze_maps[level]
                next_model = MazeModel(maze_map_path=next_map, runners_count=RUNNERS_COUNT)
                next_model.run_model()
            else:
                print("Parabéns! Todos os labirintos foram concluídos!")
                self.running = False
        else:
            print(f"#agents {len(self.agents_by_type[RunnerAgent])}")

    def release_pheromones(self, position, strength):
        # Libera feromônios na posição especificada com a força dada
        if position not in self.pheromones:
            self.pheromones[position] = 0
        self.pheromones[position] = max(self.pheromones[position], strength)
        print(f"Released pheromone at {position} with strength {strength}")

    def get_pheromone_at(self, position):
        # Retorna a intensidade de feromônio em uma posição
        return self.pheromones.get(position, 0)