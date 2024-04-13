class Node:
    def __init__(self, move):
        self.move = move
        self.frequency = 0
        self.children = []


def insert_moves(node, moves):
    for child in node.children:
        if child.move == moves[0]:
            child.frequency += 1
            if len(moves) > 1:
                insert_moves(child, moves[1:])
            return
    node.children.append(Node(moves[0]))
    if len(moves) > 1:
        insert_moves(node.children[-1], moves[1:])


def create_tree(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()
        lines = [line.strip() for line in lines]

    tree = Node('root')
    for line in lines:
        moves = line.split(' ')
        insert_moves(tree, moves)

    return tree


def visit_tree(node, path):
    best_score, best_move = -1, ""
    for child in node.children:
        if child.frequency > best_score:
            best_score = child.frequency
            best_move = child.move

    path.append(best_move)

    for child in node.children:
        if len(child.children) > 0:
            path.append("m")
            path.append(child.move)
            visit_tree(child, path)
            path.append("u")


def create_path(tree):
    path = []
    visit_tree(tree, path)
    return path


def save_path(path, filename):
    with open(filename, 'w') as f:
        f.write("\n".join(map(str, path)))


if __name__ == '__main__':
    tree = create_tree('pgn/complete.txt')
    path = create_path(tree)
    save_path(path, 'opening_book.txt')
