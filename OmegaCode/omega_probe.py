import random
import socket
import string
import time


HOST = "f7k2mXqL9pRwN4sB.boroctf.com"
PORT = 39174


def ev(v: int) -> str:
    if v == 0:
        return "a"
    q, r = divmod(v, 25)
    return "z" * q if r == 0 else "z" * q + chr(ord("a") + r)


def es(s: str) -> str:
    return " ".join(ev(ord(c) - 32) for c in s)


def recv_all(sock: socket.socket, delay: float = 0.2, idle_timeout: float = 0.8) -> str:
    sock.settimeout(delay)
    chunks = []
    last_data = time.time()
    while True:
        try:
            data = sock.recv(65536)
        except TimeoutError:
            if time.time() - last_data >= idle_timeout:
                break
            continue
        if not data:
            break
        chunks.append(data)
        last_data = time.time()
    return b"".join(chunks).decode("utf-8", "replace")


def compile_run(program: str, runtime_inputs: list[str]) -> str:
    sock = socket.create_connection((HOST, PORT), timeout=10)
    try:
        recv_all(sock)
        sock.sendall(b"1\n")
        time.sleep(0.1)
        recv_all(sock)
        payload = program + "EOF\n" + "".join(f"{line}\n" for line in runtime_inputs)
        sock.sendall(payload.encode())
        time.sleep(0.5)
        return recv_all(sock, delay=0.2, idle_timeout=2.0)
    finally:
        sock.close()


def run_gauntlet(program: str) -> str:
    sock = socket.create_connection((HOST, PORT), timeout=10)
    try:
        recv_all(sock)
        sock.sendall(b"2\n")
        time.sleep(0.1)
        recv_all(sock)
        sock.sendall(program.encode())
        sock.sendall(b"EOF\n")
        time.sleep(0.5)
        return recv_all(sock, delay=0.2, idle_timeout=2.0)
    finally:
        sock.close()


def expected_output(lines: list[str]) -> str:
    out = ["Input your code, line by line. Type EOF to finish:", "===YOUR CODE===:"]
    for i, line in enumerate(lines, 1):
        out.append(f"{i} | {line}")
    return "\n".join(out) + "\n"


def concat_print(lines_out: list[str], prefix_var: str, value_var: str, cleanup: bool = True) -> None:
    lines_out.extend(["zz di", prefix_var, "zz di", value_var, "zz dx", "zz fr", "zz dx", "zz fo"])
    if cleanup:
        lines_out.extend(["zz dp", "zz dp"])


def generate_solver(counts: list[int]) -> str:
    inputs = list("abcdefgit")
    prefix_vars = list("jklmnoqrs")
    branch_vars = list("uvwxy")

    consts = []
    for var in inputs:
        consts.append((var, "a"))
    for var in branch_vars:
        consts.append((var, "a"))
    consts += [
        ("p", es("Input your code, line by line. Type EOF to finish:")),
        ("h", es("===YOUR CODE===:")),
        ("z", es("EOF")),
    ]
    for idx, var in enumerate(prefix_vars, 1):
        consts.append((var, es(f"{idx} | ")))

    lines = []
    for var, val in consts:
        lines.extend([f"zm {var}", val])

    labels = {}

    def label(name: str) -> None:
        labels[name] = len(lines) + 1

    def emit(*items: str) -> None:
        lines.extend(items)

    def print_prompt() -> None:
        emit("zz di", "p", "zz fo", "zz dp")

    def print_header() -> None:
        emit("zz di", "h", "zz fo", "zz dp")

    def read_store(var: str) -> None:
        emit("zz fi", "zz do", var)

    def branch(pvar: str, qvar: str) -> None:
        emit("zz di", pvar, "zz mm", "zz di", qvar, "zz ma", "zz do", "X")

    def check_eof(var: str, pvar: str, qvar: str) -> None:
        emit("zz di", var, "zz di", "z", "zz eq")
        branch(pvar, qvar)

    def outblock(n: int) -> None:
        print_header()
        for k in range(n):
            concat_print(lines, prefix_vars[k], inputs[k], cleanup=(k != n - 1))
        emit("ex")

    label("start")
    print_prompt()

    ordered_counts = sorted(set(counts))
    final_count = ordered_counts[-1]
    stop_counts = ordered_counts[:-1]
    read_vars = inputs[:final_count]
    branch_alloc = []
    used_temp_vars = set()
    extra_iter = iter(branch_vars)
    for stop_count in stop_counts:
        temp_vars = []
        read_pos = stop_count
        future_pool = [var for var in read_vars[read_pos + 1 :] if var not in used_temp_vars]
        while len(temp_vars) < 2 and future_pool:
            chosen = future_pool.pop(0)
            temp_vars.append(chosen)
            used_temp_vars.add(chosen)
        while len(temp_vars) < 2:
            try:
                chosen = next(extra_iter)
                temp_vars.append(chosen)
                used_temp_vars.add(chosen)
            except StopIteration as exc:
                raise ValueError("not enough branch variables for requested counts") from exc
        branch_alloc.append((read_vars[read_pos], temp_vars[0], temp_vars[1], f"cont{stop_count+1}", f"out{stop_count}"))

    branches_by_var = {var: (pv, qv, cont, out) for var, pv, qv, cont, out in branch_alloc}
    for var in read_vars:
        read_store(var)
        if var in branches_by_var:
            pv, qv, cont, _ = branches_by_var[var]
            check_eof(var, pv, qv)
            label(cont)

    label(f"out{final_count}")
    outblock(final_count)
    for n in stop_counts:
        label(f"out{n}")
        outblock(n)

    idxmap = {var: 2 * i + 1 for i, (var, _) in enumerate(consts)}
    for _, pv, qv, cont, out in branch_alloc:
        lines[idxmap[pv]] = ev(labels[out] - labels[cont])
        lines[idxmap[qv]] = ev(labels[cont] - 1)

    return "\n".join(lines) + "\n"


def generate_known_404() -> str:
    inputs = list("abcdefgit")
    prefix_vars = list("jklmnoqrs")
    consts = []
    for var in inputs:
        consts.append((var, "a"))
    for var in ["u", "v", "w", "x"]:
        consts.append((var, "a"))
    consts += [
        ("p", es("Input your code, line by line. Type EOF to finish:")),
        ("h", es("===YOUR CODE===:")),
        ("z", es("EOF")),
    ]
    for idx, var in enumerate(prefix_vars, 1):
        consts.append((var, es(f"{idx} | ")))

    lines = []
    for var, val in consts:
        lines.extend([f"zm {var}", val])

    labels = {}

    def label(name: str) -> None:
        labels[name] = len(lines) + 1

    def emit(*items: str) -> None:
        lines.extend(items)

    def print_prompt() -> None:
        emit("zz di", "p", "zz fo", "zz dp")

    def print_header() -> None:
        emit("zz di", "h", "zz fo", "zz dp")

    def read_store(var: str) -> None:
        emit("zz fi", "zz do", var)

    def branch(pvar: str, qvar: str) -> None:
        emit("zz di", pvar, "zz mm", "zz di", qvar, "zz ma", "zz do", "X")

    def check_eof(var: str, pvar: str, qvar: str) -> None:
        emit("zz di", var, "zz di", "z", "zz eq")
        branch(pvar, qvar)

    def outblock(n: int) -> None:
        print_header()
        for k in range(n):
            concat_print(lines, prefix_vars[k], inputs[k], cleanup=(k != n - 1))
        emit("ex")

    label("start")
    print_prompt()
    read_store("a")
    read_store("b")
    check_eof("b", "d", "e")
    label("cont2")
    read_store("c")
    check_eof("c", "f", "g")
    label("cont3")
    read_store("d")
    check_eof("d", "i", "t")
    label("cont4")
    read_store("e")
    check_eof("e", "u", "v")
    label("cont5")
    read_store("f")
    check_eof("f", "w", "x")
    label("cont6")
    read_store("g")
    read_store("i")
    read_store("t")

    label("out9")
    outblock(9)
    for n in [1, 2, 3, 4, 5]:
        label(f"out{n}")
        outblock(n)

    idxmap = {var: 2 * i + 1 for i, (var, _) in enumerate(consts)}
    jumps = [
        ("d", "e", "cont2", "out1"),
        ("f", "g", "cont3", "out2"),
        ("i", "t", "cont4", "out3"),
        ("u", "v", "cont5", "out4"),
        ("w", "x", "cont6", "out5"),
    ]
    for pvar, qvar, cont, out in jumps:
        lines[idxmap[pvar]] = ev(labels[out] - labels[cont])
        lines[idxmap[qvar]] = ev(labels[cont] - 1)

    return "\n".join(lines) + "\n"


def find_mismatches(program: str, tries: int = 50) -> list[tuple[list[str], str, str]]:
    specials = ["", " ", "  ", "zz di", "a", "1", "|", "hello", "x y", "==="]
    alpha = string.ascii_letters + string.digits + " |=:"
    failures = []
    for _ in range(tries):
        count = random.choice([1, 2, 3, 4, 5, 9])
        lines = []
        for _ in range(count):
            if random.random() < 0.4:
                lines.append(random.choice(specials))
            else:
                lines.append("".join(random.choice(alpha) for _ in range(random.randint(0, 8))))
        got = compile_run(program, lines + ["EOF"])
        expected = expected_output(lines)
        if expected not in got:
            failures.append((lines, expected, got))
    return failures


if __name__ == "__main__":
    solver = generate_known_404()
    print(run_gauntlet(solver))
