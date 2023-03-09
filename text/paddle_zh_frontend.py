
from text.frontend.zh_frontend import Frontend
frontend = Frontend()

pu_symbols = ['!', '?', '…', ",", "."]
replacements = [
    (u"yu",   u"u:"),   (u"ü",    u"u:"),   (u"v", u"u:"),
    (u"yi",   u"i"),    (u"you",  u"ㄧㄡ"), (u"y", u"i"),
    (u"wu",   u"u"),    (u"wong", u"ㄨㄥ"), (u"w", u"u"),
]

table = [
    # special cases
    (u"ju",   u"ㄐㄩ"), (u"qu",   u"ㄑㄩ"), (u"xu",  u"ㄒㄩ"),
    (u"zhi",  u"ㄓ"),   (u"chi",  u"ㄔ"),   (u"shi", u"ㄕ"),   (u"ri",   u"ㄖ"),
    (u"zi",   u"ㄗ"),   (u"ci",   u"ㄘ"),   (u"si",  u"ㄙ"),
    (u"r5",   u"ㄦ"),

    # initials
    (u"b",    u"ㄅ"),   (u"p",    u"ㄆ"),   (u"m",   u"ㄇ"),   (u"f",    u"ㄈ"),
    (u"d",    u"ㄉ"),   (u"t",    u"ㄊ"),   (u"n",   u"ㄋ"),   (u"l",    u"ㄌ"),
    (u"g",    u"ㄍ"),   (u"k",    u"ㄎ"),   (u"h",   u"ㄏ"),
    (u"j",    u"ㄐ"),   (u"q",    u"ㄑ"),   (u"x",   u"ㄒ"),
    (u"zh",   u"ㄓ"),   (u"ch",   u"ㄔ"),   (u"sh",  u"ㄕ"),   (u"r",    u"ㄖ"),
    (u"z",    u"ㄗ"),   (u"c",    u"ㄘ"),   (u"s",   u"ㄙ"),

    # finals
    (u"i",    u"ㄧ"),   (u"u",    u"ㄨ"),   (u"u:",  u"ㄩ"),
    (u"a",    u"ㄚ"),   (u"o",    u"ㄛ"),   (u"e",   u"ㄜ"),   (u"ê",    u"ㄝ"),
    (u"ai",   u"ㄞ"),   (u"ei",   u"ㄟ"),   (u"ao",  u"ㄠ"),   (u"ou",   u"ㄡ"),
    (u"an",   u"ㄢ"),   (u"en",   u"ㄣ"),   (u"ang", u"ㄤ"),   (u"eng",  u"ㄥ"),
    (u"er",   u"ㄦ"),
    (u"ia",   u"ㄧㄚ"), (u"io",   u"ㄧㄛ"), (u"ie",  u"ㄧㄝ"), (u"iai",  u"ㄧㄞ"),
    (u"iao",  u"ㄧㄠ"), (u"iu",   u"ㄧㄡ"), (u"ian", u"ㄧㄢ"),
    (u"in",   u"ㄧㄣ"), (u"iang", u"ㄧㄤ"), (u"ing", u"ㄧㄥ"),
    (u"ua",   u"ㄨㄚ"), (u"uo",   u"ㄨㄛ"), (u"uai", u"ㄨㄞ"),
    (u"ui",   u"ㄨㄟ"), (u"uan",  u"ㄨㄢ"), (u"un",  u"ㄨㄣ"),
    (u"uang", u"ㄨㄤ"), (u"ong",  u"ㄨㄥ"),
    (u"u:e",  u"ㄩㄝ"), (u"u:an", u"ㄩㄢ"), (u"u:n", u"ㄩㄣ"), (u"iong", u"ㄩㄥ"),

    # tones
    (u"1",    u"ˉ"),     (u"2",    u"ˊ"),
    (u"3",    u"ˇ"),    (u"4",    u"ˋ"),
    (u"5",    u"˙"),
]

table.sort(key=lambda pair: len(pair[0]), reverse=True)
replacements.extend(table)

zh_dict = [i.strip() for i in open("text/zh_dict.dict").readlines()]
zh_dict = {i.split("\t")[0]: i.split("\t")[1] for i in zh_dict}

reversed_zh_dict = {}
all_zh_phones = set()
for k, v in zh_dict.items():
    reversed_zh_dict[v] = k
    [all_zh_phones.add(i) for i in v.split(" ")]

def bopomofo(pinyin):
    '''Convert a pinyin string to Bopomofo
    The optional tone info must be given as a number suffix, eg: 'ni3'
    '''

    pinyin = pinyin.lower()
    for pair in replacements:
        pinyin = pinyin.replace(pair[0], pair[1])

    return pinyin

def phones_to_pinyins(phones):
    pinyins = ''
    accu_ph = []
    for ph in phones:
        accu_ph.append(ph)
        if ph not in all_zh_phones:
            assert len(accu_ph) == 1
            pinyins += ph
            accu_ph = []
        elif " ".join(accu_ph) in reversed_zh_dict.keys():
            pinyins += " " + reversed_zh_dict[" ".join(accu_ph)]
            accu_ph = []
    if not  accu_ph==[]:
        print(accu_ph)
    return pinyins.strip()

def pu_symbol_replace(data):
    chinaTab = ['！', '？', "…", "，", "。",'、', "..."]
    englishTab = ['!', '?', "…", ",", ".",",", "…"]
    for index in range(len(chinaTab)):
        if chinaTab[index] in data:
            data = data.replace(chinaTab[index], englishTab[index])
    return data

def zh_to_bopomofo(text):
    phones = zh_to_phonemes(text)
    pinyins = phones_to_pinyins(phones)
    bopomofos = bopomofo(pinyins)
    return bopomofos.replace(" ", "").replace("#", " ")

def pinyin_to_bopomofo(pinyin):
    bopomofos = bopomofo(pinyin)
    return bopomofos.replace(" ", "").replace("#", " ").replace("%", "% ")

def zh_to_phonemes(text):
    # 替换标点为英文标点
    text = pu_symbol_replace(text)
    phones = frontend.get_phonemes(text)[0]
    return phones

if __name__ == '__main__':
    print(zh_to_bopomofo("替换标点为英文标点"))

