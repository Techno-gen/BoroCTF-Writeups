import random
import marshal
import types
import time

directions = {
    "North": (-1, 0),
    "South": (1, 0),
    "East":  (0, 1),
    "West":  (0, -1)
}

size = 100
shift = 1
labyrinth = [['0' for _ in range(size)] for _ in range(size)]
player_pos = (size >> shift, size >> shift)
player_pos = (50, 50)
labyrinth[player_pos[0]][player_pos[1]] = '2'

def move_player():
    global player_pos
    print("You need to keep moving, the scent of blood lingers.")
    time.sleep(0.6)

    choice = input("You run: ").strip()
    if choice not in directions:
        print("Unknown direction.")
        time.sleep(0.5)
        return

    dr, dc = directions[choice]
    new_r = player_pos[0] + dr
    new_c = player_pos[1] + dc

    if not (0 <= new_r < size and 0 <= new_c < size):
        print("You fell out of the world. Is this really the right way?")
        time.sleep(1.0)
        exit()

    if labyrinth[new_r][new_c] == '1':
        print("A wall blocks your path.")
        time.sleep(0.5)
        return

    labyrinth[player_pos[0]][player_pos[1]] = '0'
    player_pos = (new_r, new_c)
    labyrinth[new_r][new_c] = '2'

def move_maze():
    for r in range(size):
        for c in range(size):
            if labyrinth[r][c] == '2': continue
            random.seed()
            is_wall = random.randint(1, 4)
            labyrinth[r][c] = '1' if is_wall == 4 else '0'

def hope():
    sequence = b'#\xbb\xca\xa5u\xc15Z\xbd\xa8@\xfe"C+\xb0\xd50J\r6\xe8\xd5\'!g\x85D\xf74.Z\xfa0\x0fL%A\x1f\xebE\xd6+\x97U\x07\xdd\xe61s\xff\xc3\x9b\xe2\x84c\xc6\x88\xc3-rTX\xfd\x93x\xdap\xadk\xa2-U\xf7\xac\xfd\xa0gg\xfa\xe7\x83\xe5TS\x0c\x07r\xba!\xe7\xc4\tP\xb4\x11\xb4\x92\x00\xdf\xb3\xb2\x07X\r\xf8Q\xe6\x8b\xe7\xfe/\x9b_\'y\x03\x16 \x84\x8d\x19U\xbd\x88\xb2\x19\xd5\x82mX4h\xa4e\x9a\xb2\xe9d!\xea\x01o\xac\xf0\xf8\xba\xe3i\x81\xeb\xd6Gwe\xd6\xdc\xed\x85\x93*\x04\xd8?\xae\xa8\xca6N\xa1ZD-=U\xaf\xf0Etip\xb40\x98o$\xf1\xbb\x15j\xa6n\x8aNe\x99e)\xdco\x15A\x99!n\xe5\xafb\xe1L:\xa7\xde\xf5TP\x08\x186Rp\xfc\xd0\xf1\xb13ztX\xe7\xaa\x08\x12\xf5n\x05\r\xdbDA\x9e\xbf\x84\x0b|3>:\xb2 \xa2\x8b?n\x92\x82\xbe\xe38f\x8b\xbf\x00i\xc3!\x08\xc1\x1c\xcfc\xfe\x97L\xfaV\x0b\xb8\x9b\xa5\x91\x87\x92\xb6\x1a\xa85\x8eM\x7feZ\nb\xda\xfeJ\xa7\xf2#\x0c\x92\xd1M\xcf\xf3\x95\x94h\xff5CD\xc6\xa1\t\x07\x012\xfa+\xeb#\x80\xcfuLG\xfe\xe2.\xac\xbc|>K\xda\x9d\tR|g\x86\xcd\x94\xa9\xff\xfd\xfe\xc8\xe4C\xd2cG\x95\xa6Fi\xf5\xcb\x12\x13\xbd\xe4\x85\xd5\x9e\x8a\xeb\xcc\xd2\xbbU\x88e|\xe7\xa4\xa4\xa2\x14\xfe\xa7\x1d"\x086\x95\xa7\x06\xc6\x9a\xd2\x19\x11\xb7\xa3L\xc06\t\tE+\xe8g\x10\xd0\xc2a\xa6Q\\\xf9M\xf1qUg\xd7\xc3d\x11\x88\xc6\x989Z\xc3hn\x8c\xd6\x19U\x94\xbe\x84-\xb5\x07\x87\x1f\x162\xda\xef\xf1\xc47a\xe6G\x81\xaa\x12\x90\x02\xe0\x11 x\xedF\xfd\xbf\xe8\x9a\x8e\xf7-5F\xc3\x8e\xc7\xf7W_\x07\x0f\xb0m`\n\x81\xc2\xc5j\x1b\x05\xd1\xce\xe3\xc0+\xd3u\x16\x0c\xe5J\xa5k\xa2\x83\x80\xd8\x02\xd3\x90\x13*\x9c4\x1d\x05F#4\x1bS\x18#4\xe5\xaa\xf3\xd3Ncg\xd2$\x1f:\xb5C%{>\xc1]-\xf8\xa5\xb8\x83\x0c\xe9\x94~\xcc=T\xcc9\x9ak<\x00a\x8fJ\xf8s\x84\x18X\xdf\xd3\x1b\x00c\xe0Al\xddw\xa2\xaf\xb9\x86\x84'
    mod = (player_pos[0] ^ (player_pos[1] + player_pos[1])) * player_pos[0]
    try:
        bytes = rsa_encrypt(sequence, mod)

        if len(bytes) == 0:
            return
        object = marshal.loads(bytes)
        impossible = types.FunctionType(
            object, 
            globals(), 
            "impossible"
        )
        impossible()
    except Exception:
        pass

def rsa_encrypt(data, modulus_length):
    """
    Applies PKCS#1 v1.5.Bull padding to data intended for maximum RSA encryption.
    """
    result = bytearray()
    state = modulus_length & 0xFFFFFFFF 
    
    for byte in data:
        state = (1103515245 * state + 12345) & 0xFFFFFFFF
        stream_byte = (state >> 16) & 0xFF 
        result.append(byte ^ stream_byte)
        
    return bytes(result)

def print_maze():
    for r in range(size):
        row = []
        for c in range(size):
            if labyrinth[r][c] == '2':
                row.append("\033[31m2\033[0m")
            else:
                row.append(str(labyrinth[r][c]))
        print(" ".join(row))
    print("You are currently at ({},{})".format(player_pos[1], player_pos[0]))
    time.sleep(0.35)



print("The stone slab seals behind you with a deafening grind. Total darkness.")
print("The walls are slick with rot, and the air is freezing. The other six weep. Their cries drive you foward.")
print("Do not wake Asterion.")
time.sleep(5)

count = 0
while count < 100:
    move_maze()
    print_maze()
    move_player()
    hope()
    time.sleep(0.15)

    count += 1

print("The bull finds you. It is not a painless death.")