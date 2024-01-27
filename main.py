import subprocess
from asyncio import sleep, create_task, run

import chess


async def play_match(match):
    def write(engine, command):
        engine.stdin.write(command + '\n')
        engine.stdin.flush()

    async def read(engine, command):
        while True:
            out = engine.stdout.readline()
            # print(out)
            if out[:-1].split(" ")[0] == command:
                return out[:-1]
            await sleep(0.01)

    engine1 = subprocess.Popen([f"./{match.player1}"], stdout=subprocess.PIPE, stdin=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True)
    engine2 = subprocess.Popen([f"./{match.player2}"], stdout=subprocess.PIPE, stdin=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True)

    moves = []

    write(engine1, 'ucinewgame')
    write(engine2, 'ucinewgame')
    write(engine1, 'setoption name UCI_Elo value 2000')
    write(engine2, 'setoption name UCI_Elo value 2000')
    write(engine1, 'setoption name UCI_LimitStrength value true')
    write(engine2, 'setoption name UCI_LimitStrength value true')
    write(engine1, 'isready')
    write(engine2, 'isready')

    await read(engine1, "readyok")
    await read(engine2, "readyok")

    board = chess.Board()

    while True:
        write(engine1, f"position startpos moves {' '.join(moves)}")
        write(engine1, f"go movetime {match.time1}")
        # print(board.fen())
        await sleep(0.05)
        output = (await read(engine1, "bestmove")).split(" ")[1]
        moves.append(output)
        move = chess.Move.from_uci(output)
        board.push(move)
        outcome = board.outcome(claim_draw=True)
        if outcome is not None:
            return outcome.winner
        write(engine2, f"position startpos moves {' '.join(moves)}")
        write(engine2, f"go movetime {match.time2}")
        # print(board.fen())
        await sleep(0.05)
        output = (await read(engine2, "bestmove")).split(" ")[1]
        moves.append(output)
        move = chess.Move.from_uci(output)
        board.push(move)
        outcome = board.outcome(claim_draw=True)
        if outcome is not None:
            return outcome.winner


class Match:
    def __init__(self, player1, player2, time1, time2):
        self.player1 = player1
        self.player2 = player2
        self.time1 = time1
        self.time2 = time2


async def worker(match, results):
    winner = await play_match(match)
    if winner is None:
        results['draw'] += 1
    else:
        if winner == chess.WHITE:
            results[match.player1] += 1
        else:
            results[match.player2] += 1


async def score_matches(player1, player2, time1, time2, n):
    results = {player1: 0, player2: 0, 'draw': 0}

    tasks = []

    from math import floor
    for i in range(floor(n / 2)):
        tasks.append(create_task(worker(Match(player1, player2, time1, time2), results)))
        tasks.append(create_task(worker(Match(player2, player1, time2, time1), results)))

    for task in tasks:
        await task

    return results


async def main():
    result = await score_matches('ChessEngineSoft.exe', 'fish.exe', 100, 100, 20)
    print(result)


if __name__ == '__main__':
    run(main())
