"""
https://www.apprendre-en-ligne.net/crypto/rsa/index.html <-- GROSSE inspiration du code d'encryptage trouvé sur se site
https://cahier-de-prepa.fr/pc-wallon/download?id=234 <-- Pour mieux comprendre comment fonctionne le cryptage RSA
"""

import random
from sympy import isprime

def pgdc(a, b):
    # plus grand diviseur commun de a et b
    temp = 0
    while True:
        temp = a % b
        if (temp == 0):
            return b
        a = b
        b = temp


def euclide(b, n):
    # calcule b ^(-1) mod n
    n0 = n
    b0 = b
    t0 = 0
    t = 1
    q = n0 // b0
    r = n0 % b0
    while r > 0:
        temp = t0 - q * t
        while temp < 0:
            temp += n
        t0 = t
        t = temp
        n0 = b0
        b0 = r
        q = n0 // b0
        r = n0 % b0
    if b0 != 1:
        return None
    else:
        return t


def crypter(message, n, e):
    # crypte un nombre
    # utilisation de pow avec aide de cette video https://www.youtube.com/watch?v=MMQphbVOTNU&t=3s
    return pow(message, e, n)


def decrypter(texte_crypte, n, d):
    # decrypte un nombre
    return pow(texte_crypte, d, n)


def chiffrer(message, cle_publique, bloc):
    n, e = cle_publique
    # convertit chaque caractere dans son code ASCII avant de le chiffrer par groupe de "bloc" chiffres
    if 10 ** bloc > n:
        print("blocs trop grands par rapport à n")
    liste = []
    chiffres = ""
    for lettre in message:
        ascii = ord(lettre)
        # Petite adaptation ici pour assurer que le formatage reste compatible avec le reseau
        str_ascii = str(ascii)
        while len(str_ascii) < 3:
            str_ascii = "0" + str_ascii
        chiffres += str_ascii  # chiffres a toujours une longueur de 3 (code acsii etendu)
    while len(chiffres) % bloc != 0:
        chiffres = "0" + chiffres
    for paquet in range(len(chiffres) // bloc):
        nombre = int(chiffres[bloc * paquet:bloc * paquet + bloc])
        liste.append(crypter(nombre, n, e))
    return liste


def dechiffrer(encode, cle_privee, bloc):
    n, d = cle_privee
    liste = []
    chiffres = ""
    s = ''
    for num in encode:
        liste.append(decrypter(num, n, d))
    for nombre in liste:
        str_nombre = str(nombre)
        while len(str_nombre) < bloc:
            str_nombre = "0" + str_nombre
        chiffres += str_nombre
    while len(chiffres) % 3 != 0:
        chiffres = chiffres[1:]  # enleve des 0 au debut de chiffres
    for paquet in range(len(chiffres) // 3):
        try:
            nombre = int(chiffres[3 * paquet:3 * paquet + 3])
            if nombre > 0:
                s += chr(nombre)
        except: pass
    return s

def generer_cles_automatiquement():
    """
    fonction qui génère un p et un q premier aléatoire
    fait avec l'aide de https://www.educative.io/answers/what-is-the-sympyisprime-method-in-python
    et https://www.ionos.fr/digitalguide/sites-internet/developpement-web/python-randint/
    et https://www.etudestech.com/decryptage/algorithme-deuclide/
    """
    p = 0
    q = 0

    while not isprime(p):
        p = random.randint(100, 500)

    while not isprime(q) or q == p:
        q = random.randint(100, 500)

    n_val = p * q
    phi = (p - 1) * (q - 1)

    e_val = random.randint(3, phi - 1)
    while pgdc(e_val, phi) != 1:
        e_val = random.randint(3, phi - 1)

    d_val = euclide(e_val, phi)

    return (n_val, e_val), (n_val, d_val)
