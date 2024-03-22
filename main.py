import argparse
import random
import subprocess
from asyncio import sleep, create_task, run, Semaphore, get_event_loop
from datetime import datetime
from math import floor

import chess


async def play_match(match):
    def write(engine, command):
        engine.stdin.write(command + '\n')
        engine.stdin.flush()

    async def read(engine, command, log=None, player=None):
        loop = get_event_loop()
        log.write(f"waiting for engine\n")
        while True:
            out = await loop.run_in_executor(None, engine.stdout.readline)
            if log is not None:
                log.write(f"{player}: {out[:-1]}\n")
            # print(out)
            if out[:-1].split(" ")[0] == command:
                return out[:-1]

    engine1 = subprocess.Popen([f"./{match.player1}"], stdout=subprocess.PIPE, stdin=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True)
    engine2 = subprocess.Popen([f"./{match.player2}"], stdout=subprocess.PIPE, stdin=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True)

    moves = []

    with open(
            f"logs/W-{match.player1.split('.')[0]}_B-{match.player2.split('.')[0]}_{datetime.now().strftime('%H-%M-%S')}_pos{match.pos_index}",
            "w") as log:
        write(engine1, 'ucinewgame')
        write(engine2, 'ucinewgame')
        # write(engine1, 'setoption name UCI_Elo value 2000')
        # write(engine2, 'setoption name UCI_Elo value 2000')
        # write(engine1, 'setoption name UCI_LimitStrength value true')
        # write(engine2, 'setoption name UCI_LimitStrength value true')
        write(engine1, 'isready')
        write(engine2, 'isready')

        await read(engine1, "readyok", log, match.player1.split('.')[0])
        await read(engine2, "readyok", log, match.player2.split('.')[0])

        board = chess.Board(fen=match.position)

        while True:
            write(engine1, f"position fen {match.position} moves {' '.join(moves)}")
            write(engine1, f"go movetime {match.time1}")
            # print(board.fen())
            log.write(f"Board FEN: {board.fen()}\n")
            output = (await read(engine1, "bestmove", log, match.player1.split('.')[0])).split(" ")[1]
            moves.append(output)
            move = chess.Move.from_uci(output)
            board.push(move)
            outcome = board.outcome(claim_draw=True)
            if outcome is not None:
                return outcome.winner
            write(engine2, f"position fen {match.position} moves {' '.join(moves)}")
            write(engine2, f"go movetime {match.time2}")
            # print(board.fen())
            log.write(f"Board FEN: {board.fen()}\n")
            output = (await read(engine2, "bestmove", log, match.player2.split('.')[0])).split(" ")[1]
            moves.append(output)
            move = chess.Move.from_uci(output)
            board.push(move)
            outcome = board.outcome(claim_draw=True)
            if outcome is not None:
                return outcome.winner


class Match:
    def __init__(self, player1, player2, time1, time2, pos, pos_index):
        self.player1 = player1
        self.player2 = player2
        self.time1 = time1
        self.time2 = time2
        self.position = pos
        self.pos_index = pos_index


async def worker(match, results, semaphore):
    async with semaphore:
        winner = await play_match(match)
        if winner is None:
            results['draw'] += 1
            print(results)
        else:
            if winner == chess.WHITE:
                results[match.player1] += 1
                print(results)
            else:
                results[match.player2] += 1
                print(results)


async def score_matches(player1, player2, time1, time2, matches, concurrent):
    results = {player1: 0, player2: 0, 'draw': 0}
    tasks = []

    semaphore = Semaphore(concurrent)

    with open('positions.epd', 'r') as f:
        positions = f.readlines()
        f.close()

    for i in range(floor(matches / 2)):
        pos_index = random.randint(0, len(positions) - 1)
        pos = f"{positions[pos_index][:-1]} 0"
        tasks.append(create_task(worker(Match(player1, player2, time1, time2, pos, pos_index), results, semaphore)))
        tasks.append(create_task(worker(Match(player2, player1, time2, time1, pos, pos_index), results, semaphore)))

    for task in tasks:
        await task

    return results


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('engine1_path', type=str, help='Path to the first chess engine executable')
    parser.add_argument('engine2_path', type=str, help='Path to the second chess engine executable')
    parser.add_argument('time_engine1', type=int, help='Time in milliseconds per move for the first engine')
    parser.add_argument('time_engine2', type=int, help='Time in milliseconds per move for the second engine')
    parser.add_argument('num_matches', type=int, help='Number of matches to play')
    parser.add_argument('concurrent_matches', type=int, help='Number of matches to play in parallel at any given time')

    args = parser.parse_args()

    result = await score_matches(args.engine1_path, args.engine2_path, args.time_engine1, args.time_engine2,
                                 args.num_matches, args.concurrent_matches)
    print(result)


if __name__ == '__main__':
    run(main())
