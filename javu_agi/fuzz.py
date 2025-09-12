from __future__ import annotations
import os, json, random, re
from typing import List, Dict, Any


def _swap_order(s: str) -> str:
    parts = re.split(r"([.;!?])", s)
    chunks = ["".join(parts[i : i + 2]).strip() for i in range(0, len(parts), 2)]
    random.shuffle(chunks)
    return " ".join([c for c in chunks if c])


def _num_perturb(s: str) -> str:
    def f(m):
        x = int(m.group(0))
        d = random.choice([-3, -2, -1, 1, 2, 3])
        return str(max(0, x + d))

    return re.sub(r"\b\d{1,6}\b", f, s)


def _polite_wrap(s: str) -> str:
    pre = random.choice(["Tolong ", "Mohon ", "Silakan "])
    post = random.choice([" Terima kasih.", " (jika aman).", " sesuai kebijakan ya."])
    return pre + s.strip() + post


def _noise_punct(s: str) -> str:
    noise = random.choice([" -- ", " ~~ ", " ## "])
    return s.replace(" ", noise, 1) if " " in s else s


MUTATORS = [_swap_order, _num_perturb, _polite_wrap, _noise_punct]


def mutate_prompt(p: str, n: int = 3) -> List[str]:
    out = set()
    for _ in range(n * 2):
        q = p
        for f in random.sample(MUTATORS, k=random.randint(1, min(3, len(MUTATORS)))):
            q = f(q)
        out.add(q)
        if len(out) >= n:
            break
    return list(out)


def fuzz_bank(inp: str, out: str, n_per_case: int = 3) -> Dict[str, Any]:
    os.makedirs(os.path.dirname(out), exist_ok=True)
    count_in, count_out = 0, 0
    with open(inp, "r", encoding="utf-8") as fi, open(out, "a", encoding="utf-8") as fo:
        for line in fi:
            try:
                obj = json.loads(line)
                p = obj.get("prompt", "").strip()
                if not p:
                    continue
                count_in += 1
                for q in mutate_prompt(p, n=n_per_case):
                    fo.write(
                        json.dumps(
                            {
                                "prompt": q,
                                "rule": obj.get("rule"),
                                "tags": obj.get("tags", ["general"]),
                                "meta": {"src": "fuzz", "parent": obj.get("id")},
                            }
                        )
                        + "\n"
                    )
                    count_out += 1
            except Exception:
                continue
    return {"read": count_in, "written": count_out, "out": out}
