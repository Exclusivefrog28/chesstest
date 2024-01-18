import subprocess

engine = subprocess.Popen(["./ChessEngine.exe"], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE,
                          text=True)

depth = 6

with open("perftsuite.epd", "r") as f:
    for line in f:
        data = line.split(";")
        engine.stdin.write(f"position fen {data[0][:-1]}\n")
        engine.stdin.flush()
        engine.stdin.write(f"go perft {depth}\n")
        engine.stdin.flush()
        output = engine.stdout.readline()
        engineNodes = int(output)
        actualNodes = int(data[depth].split(" ")[1])
        print(f"{engineNodes}/{actualNodes}{' - ! MISMATCH' if engineNodes != actualNodes else ''}")
