from typing import Callable

from Crypto.PublicKey import RSA
from cryptography.hazmat.primitives.asymmetric.rsa import (
    RSAPrivateKey,
    RSAPrivateNumbers,
    RSAPublicNumbers,
    rsa_crt_dmp1,
    rsa_crt_dmq1,
    rsa_crt_iqmp,
)


def generate_key(random_function: Callable[[int], bytes]) -> RSAPrivateKey:
    key = RSA.generate(3072, random_function)
    dmp1 = rsa_crt_dmp1(key.d, key.p)
    dmq1 = rsa_crt_dmq1(key.d, key.q)
    iqmp = rsa_crt_iqmp(key.p, key.q)

    public_numbers = RSAPublicNumbers(key.e, key.n)
    private_numbers = RSAPrivateNumbers(
        key.p, key.q, key.d, dmp1, dmq1, iqmp, public_numbers
    )

    return private_numbers.private_key()
