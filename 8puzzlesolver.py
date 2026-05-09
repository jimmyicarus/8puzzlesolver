import heapq

GOAL = [1, 2, 3, 4, 5, 6, 7, 8, 0]

# Node

class Node:
    state = None
    parentstate = None
    action = None
    edgeCost = None
    gOfN = None      # total edge cost
    hOfN = None      # heuristic value
    heuristicFn = None

    def __init__(self, value):
        self.value = value

    # needed so heapq can compare Nodes when f-values tie
    def __lt__(self, other):
        return False


# Helpers

def get_neighbors(state):
    """Return list of (action, new_state) reachable from state."""
    neighbors = []
    idx = state.index(0)
    row, col = divmod(idx, 3)

    moves = {
        'UP':    (row - 1, col),
        'DOWN':  (row + 1, col),
        'LEFT':  (row, col - 1),
        'RIGHT': (row, col + 1),
    }

    for action, (r, c) in moves.items():
        if 0 <= r < 3 and 0 <= c < 3:
            new_state = state[:]
            new_idx = r * 3 + c
            new_state[idx], new_state[new_idx] = new_state[new_idx], new_state[idx]
            neighbors.append((action, new_state))

    return neighbors


def reconstruct(node_map, state_key, start_key):
    """Walk parent pointers and return (path_of_actions, full_path_of_states)."""
    actions = []
    states  = []
    key = state_key
    while key != start_key:
        info = node_map[key]          # (parent_key, action, state)
        actions.append(info['action'])
        states.append(info['state'])
        key = info['parent']
    states.append(node_map[start_key]['state'])
    actions.reverse()
    states.reverse()
    return actions, states


# Heuristics

## Default heuristic for when g is only considered
def h_nil(state):
    return 0

def h_misplaced(state):
    """h1 – number of misplaced tiles (excluding blank)."""
    return sum(s != g and s != 0 for s, g in zip(state, GOAL))

def h_manhattan(state):
    """h2 – Manhattan distance."""
    total = 0
    for i, tile in enumerate(state):
        if tile == 0:
            continue
        goal_i = GOAL.index(tile)
        total += abs(i // 3 - goal_i // 3) + abs(i % 3 - goal_i % 3)
    return total

def h_linear_conflict(state):
    """h3 – Manhattan distance + linear conflict (dominates h2)."""
    dist = h_manhattan(state)
    conflict = 0

    # row conflicts
    for row in range(3):
        tiles = []
        for col in range(3):
            tile = state[row * 3 + col]
            if tile == 0:
                continue
            goal_row = GOAL.index(tile) // 3
            if goal_row == row:
                tiles.append((tile, col))
        for i in range(len(tiles)):
            for j in range(i + 1, len(tiles)):
                ti, ci = tiles[i]
                tj, cj = tiles[j]
                gi = GOAL.index(ti) % 3
                gj = GOAL.index(tj) % 3
                if (ci < cj) != (gi < gj):
                    conflict += 2

    # column conflicts
    for col in range(3):
        tiles = []
        for row in range(3):
            tile = state[row * 3 + col]
            if tile == 0:
                continue
            goal_col = GOAL.index(tile) % 3
            if goal_col == col:
                tiles.append((tile, row))
        for i in range(len(tiles)):
            for j in range(i + 1, len(tiles)):
                ti, ri = tiles[i]
                tj, rj = tiles[j]
                gi = GOAL.index(ti) // 3
                gj = GOAL.index(tj) // 3
                if (ri < rj) != (gi < gj):
                    conflict += 2

    return dist + conflict


# Generic priority-queue search

def _search(start, end, h, g_flag):
    """
    priority_fn(g, state) -> priority value placed on the heap.
    Returns (path, fullPath, totalCost).
    """
    
    start_key = tuple(start)
    goal_key  = tuple(end)

    priority_fn = lambda g, s: (g if g_flag else 0) + h(s)

    # node_map stores the best known info for each visited state
    node_map = {start_key: {'parent': None, 'action': None, 'state': start, 'g': 0}}

    # heap entries: (priority, node)
    start_node = Node(start)
    start_node.state  = start
    start_node.gOfN   = 0
    start_node.hOfN   = priority_fn(0, start)

    heap = [(priority_fn(0, start), start_node)]
    visited = set()

    while heap:
        _, current = heapq.heappop(heap)
        state_key = tuple(current.state)

        if state_key in visited:
            continue
        visited.add(state_key)

        if state_key == goal_key:
            path, full_path = reconstruct(node_map, state_key, start_key)
            return path, full_path, node_map[state_key]['g']

        g = node_map[state_key]['g']

        for action, new_state in get_neighbors(current.state):
            new_key = tuple(new_state)
            new_g   = g + 1                          # edge cost = 1

            if new_key in visited:
                continue

            if new_key not in node_map or node_map[new_key]['g'] > new_g:
                node_map[new_key] = {
                    'parent': state_key,
                    'action': action,
                    'state':  new_state,
                    'g':      new_g,
                }
                child = Node(new_state)
                child.state = new_state
                child.gOfN  = new_g
                child.hOfN  = h(new_state)
                priority = priority_fn(new_g, new_state)
                heapq.heappush(heap, (priority, child))

    return [], [], -1          # no solution found


# SearchAlgorithms class
class SearchAlgorithms:
    Path     = []
    fullPath = []
    totalCost = -1
    chosen_h = h_linear_conflict

    def __init__(self, start, end):
        self.start = start
        self.end   = end

    def UCS(self):
        """Uniform Cost Search — f(n) = g(n)."""
        path, fullPath, cost = _search(
            self.start, self.end, h_nil, True
        )
        self.Path      = path
        self.fullPath  = fullPath
        self.totalCost = cost
        return self.Path, self.fullPath, self.totalCost

    def Astar(self):
        """A* Search — f(n) = g(n) + h(n)  [using Manhattan distance h2]."""
        path, fullPath, cost = _search(
            self.start, self.end, SearchAlgorithms.chosen_h, True
        )
        self.Path      = path
        self.fullPath  = fullPath
        self.totalCost = cost
        return self.Path, self.fullPath, self.totalCost

    def Greedy(self):
        """Greedy Best-First Search — f(n) = h(n)  [using Manhattan distance h2]."""
        path, fullPath, cost = _search(
            self.start, self.end, SearchAlgorithms.chosen_h, False
        )
        self.Path      = path
        self.fullPath  = fullPath
        self.totalCost = cost
        return self.Path, self.fullPath, self.totalCost


# main
def main():
    s3 = SearchAlgorithms([1, 2, 3, 4, 0, 6, 7, 5, 8], [1,2,3,4,5,6,7,8,0])
    path, fullPath, cost = s3.UCS()
    print('UCS Path: ' + str(path), end='\nFull Path is: ')
    print(fullPath)
    print(" + total Cost = " + str(cost))

    s4 = SearchAlgorithms([1, 2, 3, 4, 0, 6, 7, 5, 8], [1,2,3,4,5,6,7,8,0])
    path, fullPath, cost = s4.Astar()
    print('AstarHeuristic Path: ' + str(path), end='\nFull Path is: ')
    print(fullPath)
    print(" + total Cost = " + str(cost))

    s4 = SearchAlgorithms([1, 2, 3, 4, 0, 6, 7, 5, 8], [1,2,3,4,5,6,7,8,0])
    path, fullPath, cost = s4.Greedy()
    print('GreedyHeuristic Path: ' + str(path), end='\nFull Path is: ')
    print(fullPath)
    print(" + total Cost = " + str(cost))


if __name__ == "__main__":
    main()
