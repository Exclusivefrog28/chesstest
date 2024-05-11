import argparse
import random
import subprocess
from asyncio import create_task, run, Semaphore, get_event_loop, create_subprocess_exec
from asyncio.subprocess import PIPE
from datetime import datetime
from math import floor

import chess


async def play_match(match):
    def write(engine, command):
        engine.stdin.write((command + '\n').encode("utf-8"))

    async def read(engine, command, log=None, player=None):
        try:
            log.write(f"waiting for engine\n")
            async for line in engine.stdout:
                decoded = str(line.decode("utf-8"))
                if log is not None:
                    log.write(f"{player}: {decoded.strip()}\n")
                if decoded.strip().split(" ")[0] == command:
                    return decoded.strip()
        except Exception as e:
            print(e)

    async def read_stderr(engine, player=None):
        async for line in engine.stderr:
            decoded = str(line.decode("utf-8"))
            print(f"{player}: {decoded.strip()}")

    engine1 = await create_subprocess_exec(f"./{match.player1}", stdin=PIPE, stdout=PIPE,
                                           stderr=PIPE)
    engine2 = await create_subprocess_exec(f"./{match.player2}", stdin=PIPE, stdout=PIPE,
                                           stderr=PIPE)

    player1_name = match.player1.split('.')[0]
    player2_name = match.player2.split('.')[0]

    read_stderr(engine1, player1_name)
    read_stderr(engine2, player2_name)

    moves = []

    with open(
            f"logs/W-{engine1.pid}_B-{engine2.pid}_{datetime.now().strftime('%H-%M-%S')}_pos{match.pos_index}",
            "w") as log:
        write(engine1, 'ucinewgame')
        write(engine2, 'ucinewgame')
        write(engine1, 'setoption name UCI_Elo value 2000')
        write(engine2, 'setoption name UCI_Elo value 2000')
        write(engine1, 'setoption name UCI_LimitStrength value true')
        write(engine2, 'setoption name UCI_LimitStrength value true')
        write(engine1, 'isready')
        write(engine2, 'isready')

        await read(engine1, "readyok", log, player1_name)
        await read(engine2, "readyok", log, player2_name)

        board = chess.Board(fen=match.position)

        while True:
            write(engine1, f"position fen {match.position} moves {' '.join(moves)}")
            write(engine1, f"go movetime {match.time1}")
            log.write(f"Board FEN: {board.fen()}\n")
            output = (await read(engine1, "bestmove", log, player1_name)).split(" ")[1]
            moves.append(output)
            if output == 'a8a8':
                print('nullmove', engine1.pid)
            move = chess.Move.from_uci(output)
            board.push(move)
            outcome = board.outcome(claim_draw=True)
            if outcome is not None:
                engine1.terminate()
                engine2.terminate()
                log.write("match ended\n")
                await engine1.wait()
                await engine2.wait()
                return outcome.winner
            write(engine2, f"position fen {match.position} moves {' '.join(moves)}")
            write(engine2, f"go movetime {match.time2}")
            log.write(f"Board FEN: {board.fen()}\n")
            output = (await read(engine2, "bestmove", log, player2_name)).split(" ")[1]
            moves.append(output)
            if output == 'a8a8':
                print('nullmove', engine2.pid)
            move = chess.Move.from_uci(output)
            board.push(move)
            outcome = board.outcome(claim_draw=True)
            if outcome is not None:
                engine1.terminate()
                engine2.terminate()
                log.write("match ended\n")
                await engine1.wait()
                await engine2.wait()
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
