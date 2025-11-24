def decode_string(input, start = 0):
    pos = start
    char = input[start]
    while char != ":":
        pos += 1
        char = input[pos]
    len_str = int(input[start:pos])
    res = input[pos+1:pos+1+len_str]
    length = pos+1+len_str - start
    return res, length

def decode_int(input, start):
    end = start
    char = input[start]
    while char != 'e':
        end += 1
        char = input[end]
    res = int(input[start+1:end])
    length = end - start+1
    return res, length

def decode_list(input, start = 0):
    result = []
    res_lenght = 1
    pos = start + 1
    while pos < len(input):
        char = input[pos]

        if char == 'e':
            res_lenght += 1
            return result, res_lenght
        elif char == 'i':
            element, length  = decode_int(input, pos)
            result.append(element)
            res_lenght += length
            pos = pos + length
        elif char.isdigit():
            element, length = decode_string(input, pos)
            result.append(element)
            res_lenght += length
            pos = pos + length
        elif char == 'l':
            element, length = decode_list(input, pos)
            result.append(element)
            res_lenght += length
            pos += length
        elif char == 'd':
            element, length = decode_dict(input, pos)
            result.append(element)
            res_lenght += length
            pos = pos + length
    return result, res_lenght

def decode_dict(input, start = 0):
    res = {}
    res_len = 1
    pos = start +1

    while pos < len(input):
        char = input[pos]

        if char == 'e':
            res_len += 1
            return res, res_len
        
        key, length = decode_string(input, pos)
        res_len += length
        pos += length
        
        char = input[pos]
        if char == 'i':
            value, length = decode_int(input, pos)
            res[key] = value
            res_len += length
            pos += length
        
        elif char.isdigit():
            value, length = decode_string(input, pos)
            res[key] = value
            res_len += length
            pos += length

        elif char == 'l':
            value, length = decode_list(input, pos)
            res[key] = value
            res_len += length
            pos += length

        elif char == 'd':
            value, length = decode_dict(input, pos)
            res[key] = value
            res_len += length
            pos += length
    return res, res_len


def bencode_encode(data):
    if isinstance(data, int):
        return f"i{data}e".encode('latin-1')
    elif isinstance(data, str):
        return f"{len(data)}:{data}".encode('latin-1')
    elif isinstance(data, bytes):
        return f"{len(data)}:".encode('latin-1') + data
    elif isinstance(data, list):
        result = b'l'
        for element in data:
            result += bencode_encode(element)
        result += b'e'
        return result
    elif isinstance(data, dict):
        keys = list(data.keys())
        keys.sort()
        result = b'd'
        for key in keys:
            value = data[key]
            result += bencode_encode(key)
            result += bencode_encode(value)
        result += b'e'
        return result
    else:
        raise TypeError(f"Can't encode type {type(data)}")



def test_bencode():
    print("=" * 50)
    print("TESTING decode_string")
    print("=" * 50)
    
    # Basis-Tests
    value, length = decode_string("5:hello", 0)
    assert value == "hello" and length == 7, f"Expected ('hello', 7), got ({value}, {length})"
    print("Test 1: Einfacher String")
    
    value, length = decode_string("0:", 0)
    assert value == "" and length == 2, f"Expected ('', 2), got ({value}, {length})"
    print("Test 2: Leerer String")
    
    value, length = decode_string("12:Hello World!", 0)
    assert value == "Hello World!" and length == 15, f"Expected ('Hello World!', 15), got ({value}, {length})"
    print("Test 3: String mit Leerzeichen und 2-stelliger Länge")
    
    value, length = decode_string("3:abc", 0)
    assert value == "abc" and length == 5, f"Expected ('abc', 5), got ({value}, {length})"
    print("Test 4: 3-Zeichen String")
    
    # Mit Offset
    value, length = decode_string("XXX5:helloYYY", 3)
    assert value == "hello" and length == 7, f"Expected ('hello', 7), got ({value}, {length})"
    print("Test 5: String mit start-Offset")
    
    # Sonderzeichen
    value, length = decode_string("10:äöü!@#$%^&", 0)
    assert value == "äöü!@#$%^&" and length == 13, f"Got ({value}, {length})"
    print("Test 6: String mit Sonderzeichen")
    
    print("\n" + "=" * 50)
    print("TESTING decode_int")
    print("=" * 50)
    
    value, length = decode_int("i42e", 0)
    assert value == 42 and length == 4, f"Expected (42, 4), got ({value}, {length})"
    print("Test 7: Positiver Integer")
    
    value, length = decode_int("i0e", 0)
    assert value == 0 and length == 3, f"Expected (0, 3), got ({value}, {length})"
    print("Test 8: Null")
    
    value, length = decode_int("i-42e", 0)
    assert value == -42 and length == 5, f"Expected (-42, 5), got ({value}, {length})"
    print("Test 9: Negativer Integer")
    
    value, length = decode_int("i123456789e", 0)
    assert value == 123456789 and length == 11, f"Expected (123456789, 11), got ({value}, {length})"
    print("Test 10: Großer Integer")
    
    # Mit Offset
    value, length = decode_int("XXXi99eYYY", 3)
    assert value == 99 and length == 4, f"Expected (99, 4), got ({value}, {length})"
    print("Test 11: Integer mit start-Offset")
    
    print("\n" + "=" * 50)
    print("TESTING decode_list")
    print("=" * 50)
    
    value, length = decode_list("le", 0)
    assert value == [] and length == 2, f"Expected ([], 2), got ({value}, {length})"
    print("Test 12: Leere Liste")
    
    value, length = decode_list("li1ei2ei3ee", 0)
    assert value == [1, 2, 3] and length == 11, f"Expected ([1,2,3], 11), got ({value}, {length})"
    print("Test 13: Liste mit Integers")
    
    value, length = decode_list("l4:spam4:eggse", 0)
    assert value == ["spam", "eggs"] and length == 14, f"Expected (['spam','eggs'], 14), got ({value}, {length})"
    print("Test 14: Liste mit Strings")
    
    value, length = decode_list("li1e4:spam4:eggse", 0)
    assert value == [1, "spam", "eggs"] and length == 17, f"Expected ([1,'spam','eggs'], 17), got ({value}, {length})"
    print("Test 15: Liste mixed (int + strings)")
    
    # WICHTIG: Verschachtelte Liste
    value, length = decode_list("li1el4:spame4:eggse", 0)
    assert value == [1, ["spam"], "eggs"] and length == 19, f"Expected ([1, ['spam'], 'eggs'], 19), got ({value}, {length})"
    print("Test 16: Verschachtelte Liste + Element danach")
    
    value, length = decode_list("ll4:spamelee", 0)
    assert value == [["spam"], []] and length == 12, f"Expected ([['spam'], []], 12), got ({value}, {length})"
    print("Test 17: Mehrere verschachtelte Listen")
    
    value, length = decode_list("lli1eei2ee", 0)
    assert value == [[1], 2] and length == 10, f"Expected ([[1], 2], 10), got ({value}, {length})"
    print("Test 18: Verschachtelte Liste + Integer danach")
    
    # Tief verschachtelt
    value, length = decode_list("llli1eeee", 0)
    assert value == [[[1]]] and length == 9, f"Expected ([[[1]]], 9), got ({value}, {length})"
    print("Test 19: Dreifach verschachtelt")
    
    print("\n" + "=" * 50)
    print("ALLE TESTS BESTANDEN!")
    print("=" * 50)
def test_dict():
    value, length = decode_dict("d3:cow3:mooe", 0)
    assert value == {"cow": "moo"}
    print("Dict Test 1")
    
    value, length = decode_dict("d3:agei25e4:name4:Johne", 0)
    assert value == {"age": 25, "name": "John"}
    print("Dict Test 2")
    
    value, length = decode_dict("d4:listli1ei2eee", 0)
    assert value == {"list": [1, 2]}
    print("Dict Test 3")






