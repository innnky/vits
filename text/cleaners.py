import re
from text.japanese import japanese_to_romaji_with_accent, japanese_to_ipa, japanese_to_ipa2, japanese_to_ipa3
from text.korean import latin_to_hangul, number_to_hangul, divide_hangul, korean_to_lazy_ipa, korean_to_ipa
from text.mandarin import number_to_chinese, latin_to_bopomofo, chinese_to_romaji, \
    chinese_to_lazy_ipa, chinese_to_ipa, chinese_to_ipa2, pinyin_to_ipa
from text.english import english_to_lazy_ipa, english_to_ipa2, english_to_lazy_ipa2
from text.symbols import symbols
from text import cleaned_text_to_sequence


def str_replace( data):
    chinaTab = [";", ":", "\"", "'"]
    englishTab = [".", ",", ' ', " "]
    for index in range(len(chinaTab)):
        if chinaTab[index] in data:
            data = data.replace(chinaTab[index], englishTab[index])
    return data


def _clean_text(text):
    cleaned_text, lang_seq = cjke_cleaners3(text)
    cleaned_text = str_replace(cleaned_text)
    cleaned_text, lang_seq = remove_invalid_text(cleaned_text, lang_seq)

    return cleaned_text, lang_seq

def text_to_sequence(text):
    cleaned_text, lang_seq = _clean_text(text)
    return cleaned_text_to_sequence(cleaned_text), lang_seq


def japanese_cleaners(text):
    text = japanese_to_romaji_with_accent(text)
    text = re.sub(r'([A-Za-z])$', r'\1.', text)
    return text


def japanese_cleaners2(text):
    return japanese_cleaners(text).replace('ts', 'ʦ').replace('...', '…')


def korean_cleaners(text):
    '''Pipeline for Korean text'''
    text = latin_to_hangul(text)
    text = number_to_hangul(text)
    text = divide_hangul(text)
    text = re.sub(r'([\u3131-\u3163])$', r'\1.', text)
    return text


def chinese_cleaners(text):
    '''Pipeline for Chinese text'''
    text = number_to_chinese(text)
    text = chinese_to_bopomofo(text)
    text = latin_to_bopomofo(text)
    text = re.sub(r'([ˉˊˇˋ˙])$', r'\1。', text)
    return text


def zh_ja_mixture_cleaners(text):
    text = re.sub(r'\[ZH\](.*?)\[ZH\]',
                  lambda x: chinese_to_romaji(x.group(1))+' ', text)
    text = re.sub(r'\[JA\](.*?)\[JA\]', lambda x: japanese_to_romaji_with_accent(
        x.group(1)).replace('ts', 'ʦ').replace('u', 'ɯ').replace('...', '…')+' ', text)
    text = re.sub(r'\s+$', '', text)
    text = re.sub(r'([^\.,!\?\-…~])$', r'\1.', text)
    return text


def sanskrit_cleaners(text):
    text = text.replace('॥', '।').replace('ॐ', 'ओम्')
    text = re.sub(r'([^।])$', r'\1।', text)
    return text


def cjks_cleaners(text):
    text = re.sub(r'\[ZH\](.*?)\[ZH\]',
                  lambda x: chinese_to_lazy_ipa(x.group(1))+' ', text)
    text = re.sub(r'\[JA\](.*?)\[JA\]',
                  lambda x: japanese_to_ipa(x.group(1))+' ', text)
    text = re.sub(r'\[KO\](.*?)\[KO\]',
                  lambda x: korean_to_lazy_ipa(x.group(1))+' ', text)
    text = re.sub(r'\[SA\](.*?)\[SA\]',
                  lambda x: devanagari_to_ipa(x.group(1))+' ', text)
    text = re.sub(r'\[EN\](.*?)\[EN\]',
                  lambda x: english_to_lazy_ipa(x.group(1))+' ', text)
    text = re.sub(r'\s+$', '', text)
    text = re.sub(r'([^\.,!\?\-…~])$', r'\1.', text)
    return text


def cjke_cleaners(text):
    text = re.sub(r'\[ZH\](.*?)\[ZH\]', lambda x: chinese_to_lazy_ipa(x.group(1)).replace(
        'ʧ', 'tʃ').replace('ʦ', 'ts').replace('ɥan', 'ɥæn')+' ', text)
    text = re.sub(r'\[JA\](.*?)\[JA\]', lambda x: japanese_to_ipa(x.group(1)).replace('ʧ', 'tʃ').replace(
        'ʦ', 'ts').replace('ɥan', 'ɥæn').replace('ʥ', 'dz')+' ', text)
    text = re.sub(r'\[KO\](.*?)\[KO\]',
                  lambda x: korean_to_ipa(x.group(1))+' ', text)
    text = re.sub(r'\[EN\](.*?)\[EN\]', lambda x: english_to_ipa2(x.group(1)).replace('ɑ', 'a').replace(
        'ɔ', 'o').replace('ɛ', 'e').replace('ɪ', 'i').replace('ʊ', 'u')+' ', text)
    text = re.sub(r'\s+$', '', text)
    text = re.sub(r'([^\.,!\?\-…~])$', r'\1.', text)
    return text


def cjke_cleaners2(text):
    text = re.sub(r'\[ZH\](.*?)\[ZH\]',
                  lambda x: chinese_to_ipa(x.group(1))+' ', text)
    text = re.sub(r'\[JA\](.*?)\[JA\]',
                  lambda x: japanese_to_ipa2(x.group(1))+' ', text)
    text = re.sub(r'\[KO\](.*?)\[KO\]',
                  lambda x: korean_to_ipa(x.group(1))+' ', text)
    text = re.sub(r'\[EN\](.*?)\[EN\]',
                  lambda x: english_to_ipa2(x.group(1))+' ', text)
    text = re.sub(r'\[P\](.*?)\[P\]',
                  lambda x: pinyin_to_ipa(x.group(1))+' ', text)
    text = re.sub(r'\s+$', '', text)
    text = re.sub(r'([^\.,!\?\-…~])$', r'\1.', text)
    return text

lang_map = {
    "ZH": 0,
    "JA": 1,
    "KO": 2,
    "EN": 3,
    "P": 0,
    "other":5
}


def cjke_cleaners3(text: str):
    text = str_replace(text).replace("\"", '')
    # find all text blocks enclosed in [JA], [ZH], [EN], [P]
    original_text = text
    blocks = re.finditer(r'\[(JA|ZH|EN|P|KO)\](.*?)\[\1\]', text)
    cleaned_text = ""
    lang_seq = []
    last_end = 0
    for block in blocks:
        start, end = block.span()
        # insert text not enclosed in any blocks
        remaining_text = original_text[last_end:start]
        ipa = others_to_ipa(remaining_text)
        lang_seq += [lang_map["other"] for i in ipa]
        cleaned_text += ipa
        last_end = end
        language = block.group(1)
        text = block.group(2)
        if language == 'P':
            ipa = pinyin_to_ipa(text)
            lang_seq += [lang_map[language] for i in ipa]
            cleaned_text += ipa
        if language == 'JA':
            ipa = japanese_to_ipa2(text)
            lang_seq += [lang_map[language] for i in ipa]
            cleaned_text += ipa
        elif language == 'ZH':
            ipa = chinese_to_ipa(text)
            lang_seq += [lang_map[language] for i in ipa]
            cleaned_text += ipa
        elif language == 'EN':
            ipa = english_to_ipa2(text)
            lang_seq += [lang_map[language] for i in ipa]
            cleaned_text += ipa
        elif language == 'KO':
            ipa = korean_to_ipa(text)
            lang_seq += [lang_map[language] for i in ipa]
            cleaned_text += ipa
    remaining_text = original_text[last_end:]

    ipa = others_to_ipa(remaining_text)
    lang_seq += [lang_map["other"] for i in ipa]
    cleaned_text += ipa
    assert len(cleaned_text) == len(lang_seq)
    return cleaned_text, lang_seq

def others_to_ipa(text):
    return text

def remove_invalid_text(cleaned_text, lang_seq):
    new_cleaned_text = ''
    new_lang_seq = []
    for symbol, la in zip(cleaned_text, lang_seq):
        if symbol not in symbols:
            print(cleaned_text)
            print("skip:", symbol)
            continue
        if la == lang_map["other"]:
            print("skip:", symbol)
            continue
        new_cleaned_text += symbol
        new_lang_seq.append(la)
    return new_cleaned_text, new_lang_seq

if __name__ == '__main__':
    # print(_clean_text("%[EN]Miss Radcliffe's letter had told him [EN]"))
    print(cjke_cleaners3("[EN]Miss Radcliffe's letter had told him [EN]你好 hello[ZH]你好啊[ZH]"))
    # print(_clean_text("[P]ke3 % xian4 zai4 % jia4 ge2 % zhi2 jiang4 dao4 % yi2 wan4 duo1 $[P]"))
    # print(_clean_text("[ZH]可现在价格是降到一万多[ZH]"))