import uuid
import time
import random


def generate_uuid7() -> str:
    ts_ms = int(time.time_ns() // 1_000_000)
    rand_a = random.getrandbits(12)
    rand_b_msb = 0x8000 | random.getrandbits(14)
    rand_b_lsb = random.getrandbits(48)

    uuid7_bytes = (
        ts_ms.to_bytes(6, "big")
        + ((7 << 4) | (rand_a >> 8)).to_bytes(1, "big")
        + (rand_a & 0xFF).to_bytes(1, "big")
        + rand_b_msb.to_bytes(2, "big")
        + rand_b_lsb.to_bytes(6, "big")
    )

    return str(uuid.UUID(bytes=uuid7_bytes))
