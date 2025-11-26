# https://www.apprendre-en-ligne.net/crypto/rsa/index.html <-- GROSSE inspiration du code d'encryptage trouvé sur se site
# https://cahier-de-prepa.fr/pc-wallon/download?id=234 <-- Pour mieux comprendre comment fonctionne le cryptage RSA


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


def crypter(message):
    # crypte un nombre
    global e, n
    e1 = e
    texte_crypte = 1
    while e1 > 0:
        texte_crypte *= message
        texte_crypte %= n
        e1 -= 1
    return texte_crypte


def decrypter(texte_crypte):
    # decrypte un nombre
    global d, n
    d1 = d
    decrypte = 1
    while d1 > 0:
        decrypte *= texte_crypte
        decrypte %= n
        d1 -= 1
    return decrypte


def chiffrer(message, bloc):
    # convertit chaque caractere dans son code ASCII avant de le chiffrer par groupe de "bloc" chiffres
    if 10**bloc > n:
        print("blocs trop grands par rapport à n")
    liste = []
    chiffres = ""
    for lettre in message:
        ascii = ord(lettre)
        if ascii < 10:
            chiffres += "0"
        if ascii < 100:
            chiffres += "0"
        chiffres += str(ascii)    # chiffres a toujours une longueur de 3 (code acsii etendu)
    while len(chiffres) % bloc != 0:
        chiffres = "0" + chiffres
    for paquet in range(len(chiffres) // bloc):
        nombre = int(chiffres[bloc * paquet:bloc * paquet + bloc])
        liste.append(crypter(nombre))
    return liste


def dechiffrer(encode, bloc):
    liste = []
    chiffres = ""
    s = ''
    for num in encode:
        liste.append(decrypter(num))
    for nombre in liste:
        str_nombre = str(nombre)
        while len(str_nombre) < bloc:
            str_nombre = "0" + str_nombre
        chiffres += str_nombre
    while len(chiffres) % 3 != 0:
        chiffres = chiffres[1:]    # enleve des 0 au debut de chiffres
    for paquet in range(len(chiffres) // 3):
        nombre = int(chiffres[3 * paquet:3 * paquet + 3])
        if nombre > 0:
            s += chr(nombre)
    return s

# ------------------  programme principal ------------------------------

bloc = 4
# clef publique
p = 197      # p et q sont des nombres premiers
q = 241
n = p * q
e = 200
phi = (p - 1) * (q - 1)   # indicatrice d'Euler
while (e < phi):
    # e et phi doivent etre premiers entre eux et e < phi
    if (pgdc(e, phi) == 1):
        break
    else:
        e += 1
print("clef publique : n =", n, ", e =", e)

# clef privee d
# d*e = 1 mod phi
d = euclide(e, phi)
print("clef privée   : n =", n, ", d =", d)

message = "prout"
print("\nMessage clair :")
print(message)

print("\nMessage chiffré :")
code = chiffrer(message, bloc)   # liste des blocs
print(' '.join(str(p) for p in code))

print("\nMessage déchiffré :")
print(''.join(str(p) for p in dechiffrer(code, bloc)))