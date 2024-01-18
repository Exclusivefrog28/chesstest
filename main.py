import subprocess
import chess

def write(engine, command):
    engine.stdin.write(command + '\n')
    engine.stdin.flush()


engine1 = subprocess.Popen(["./ChessEngine"], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE,
                           text=True)
engine2 = subprocess.Popen(["./ChessEngine"], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE,
                           text=True)

write(engine1, 'isready')
write(engine2, 'isready')

output1 = engine1.stdout.readline()
output2 = engine2.stdout.readline()
if output1 != "readyok\n" or output2 != "readyok\n":
    print("Error")
    exit(1)

board = chess.Board()

while True:
    write(engine1, f"position fen {board.fen()}")
    write(engine1, 'go movetime 100')
    print("\n")
    print(board.fen())
    output = engine1.stdout.readline()
    print(output)
    if output == "problem":
        output = engine1.stdout.readline()
        print(output)
    move = chess.Move.from_uci(output.split(" ")[1][:-1])
    print(move in board.legal_moves)
    board.push(move)
    if board.is_game_over(claim_draw=True):
        print(board.result(claim_draw=True))
        break
    print(board)
    write(engine2, f"position fen {board.fen()}")
    write(engine2, 'go movetime 100')
    print("\n")
    print(board.fen())
    output = engine2.stdout.readline()
    print(output)
    if output == "problem":
        output = engine2.stdout.readline()
        print(output)
    move = chess.Move.from_uci(output.split(" ")[1][:-1])
    print(move in board.legal_moves)
    board.push(move)
    if board.is_game_over(claim_draw=True):
        print(board.result(claim_draw=True))
        break
    print(board)
