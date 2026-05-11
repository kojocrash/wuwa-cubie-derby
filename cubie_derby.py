import random
from collections import defaultdict

class Cube:
    def __init__(self, name, position):
        self.name = name
        self.position = position
        self.stack = []
        self.start_position = position

    def reset(self):
        self.position = self.start_position
        self.stack.clear()

def roll_dice():
    return random.randint(1, 3)

def apply_abilities(cube, cubes, move_order, round_index):
    move = roll_dice()
    if cube.name == "Brant" and move_order[0] == cube:
        move += 2
    if cube.name == "Pheobe" and random.random() < 0.5:
        move += 1
    if cube.name == "Calcharo":
        if cube.position == min(c.position for c in cubes) and cube.name not in [n.name for c in cubes for n in c.stack]: # TODO: check if bottom stack as well
            move += 3
    return move

def jinhsi_check(jinhsi, whole_stack):
    if random.random() < 0.4:
        for c in whole_stack:
            try:
                c.stack.remove(jinhsi)
            except:
                pass
            c.stack.append(jinhsi)

        whole_stack.remove(jinhsi)
        whole_stack.append(jinhsi)
        jinhsi.stack = []

def simulate_game(start_positions=None, start_stacks=None):
    if start_positions is None:
        start_positions = {name: 1 for name in ["Brant", "Pheobe", "Jinhsi", "Calcharo"]}

    cubes_dict = {name: Cube(name, pos) for name, pos in start_positions.items()}
    if start_stacks:
        stacks = defaultdict(list)
        for stack_group in start_stacks:
            if not stack_group:
                continue
            pos = cubes_dict[stack_group[0]].position
            for name in stack_group: # bottom to top
                stacks[pos].append(cubes_dict[name])
    else:
        # Default: stack randomly if not provided
        stacks = defaultdict(list)
        for name, cube in cubes_dict.items():
            stacks[cube.position].append(cube)
        for pos in stacks:
            random.shuffle(stacks[pos])

    cubes = list(cubes_dict.values())

    while True:
        all_cubes = []
        for pos in sorted(stacks.keys()):
            stack = stacks[pos]
            for i, cube in enumerate(stack):
                cube.stack = stack[i+1:]
                all_cubes.append(cube)

        move_order = random.sample(all_cubes, len(all_cubes))

        for i, cube in enumerate(move_order):
            move = apply_abilities(cube, cubes, move_order, i)
            total_stack = [cube] + cube.stack
            new_position = min(cube.position + move, 23)

            for c in total_stack:
                try:
                    stacks[cube.position].remove(c)
                except:
                    pass

            for c in total_stack:
                c.position = new_position
                
            old_stack_at_new_pos = stacks[new_position]
            jinhsi_eligible = False
            for c in old_stack_at_new_pos:
                if c.name == "Jinhsi":
                    jinhsi_eligible = True
                
                c.stack.extend(total_stack)

            stacks[new_position].extend(total_stack)

            for c in stacks[new_position]:
                if c.name == "Jinhsi" and jinhsi_eligible:
                    jinhsi_check(c, stacks[new_position])

            if new_position == 23:
                return cube.name

def simulate_many_games(n, start_positions=None, start_stacks=None):
    win_counts = {"Brant": 0, "Pheobe": 0, "Jinhsi": 0, "Calcharo": 0}
    for _ in range(n):
        winner = simulate_game(start_positions, start_stacks)
        win_counts[winner] += 1
    for k in win_counts:
        win_counts[k] = (win_counts[k] / n) * 100
    return win_counts

if __name__ == "__main__":
    start_positions = {"Brant": -1, "Pheobe": -2, "Jinhsi": -1, "Calcharo": 0}
    start_stacks = [["Jinhsi", "Brant"], ["Calcharo"], ["Pheobe"]]

    results = simulate_many_games(10000, start_positions, start_stacks)
    print(results)