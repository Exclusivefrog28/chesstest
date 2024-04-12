import argparse

import chess
import chess.pgn


def parse_pgn(file, depth, out):
    draw_offsets = []
    pgn = open(file)

    while True:
        offset = pgn.tell()
        headers = chess.pgn.read_headers(pgn)
        if headers is None:
            break

        if "1/2-1/2" in headers.get("Result", "?"):
            draw_offsets.append(offset)

    openings = []

    for offset in draw_offsets:
        pgn.seek(offset)
        game = chess.pgn.read_game(pgn)

        moves = []
        for move in game.mainline_moves():
            moves.append(move)
            if len(moves) == depth:
                break

        openings.append(" ".join(map(str, moves)))

    for opening in openings:
        print(opening)

    if out is not None:
        with open(out, "a") as f:
            for opening in openings:
                f.write(f"{opening}\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('file', type=str, help='Path to the PGN file')
    parser.add_argument('depth', type=int, help='Depth of the opening')
    parser.add_argument('-o', '--out', type=str, help='Path to the output file')

    args = parser.parse_args()

    parse_pgn(args.file, args.depth, args.out)
