# Copyright (c) 2021 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import re
from typing import Dict
from typing import List

import jieba.posseg as psg
import numpy as np
from g2pM import G2pM
from pypinyin import lazy_pinyin
from pypinyin import load_phrases_dict
from pypinyin import load_single_dict
from pypinyin import Style
from pypinyin_dict.phrase_pinyin_data import large_pinyin

from text.frontend.generate_lexicon import generate_lexicon
from text.frontend.tone_sandhi import ToneSandhi
from text.frontend.zh_normalization.text_normlization import TextNormalizer

class Frontend():
    def __init__(self,
                 g2p_model="pypinyin",
                 phone_vocab_path=None,
                 tone_vocab_path=None):
        self.tone_modifier = ToneSandhi()
        self.text_normalizer = TextNormalizer()

        self.punc = ['!', '?', '…', ",", ".", "#", '-', "%", "$"]
        # g2p_model can be pypinyin and g2pM
        self.g2p_model = g2p_model
        self.add_word_sep = True
        if self.g2p_model == "g2pM":
            self.g2pM_model = G2pM()
            self.pinyin2phone = generate_lexicon(
                with_tone=True, with_erhua=False)
        else:

            self.__init__pypinyin()
        self.must_erhua = {"小院儿", "胡同儿", "范儿", "老汉儿", "撒欢儿", "寻老礼儿", "妥妥儿"}
        self.not_erhua = {
            "虐儿", "为儿", "护儿", "瞒儿", "救儿", "替儿", "有儿", "一儿", "我儿", "俺儿", "妻儿",
            "拐儿", "聋儿", "乞儿", "患儿", "幼儿", "孤儿", "婴儿", "婴幼儿", "连体儿", "脑瘫儿",
            "流浪儿", "体弱儿", "混血儿", "蜜雪儿", "舫儿", "祖儿", "美儿", "应采儿", "可儿", "侄儿",
            "孙儿", "侄孙儿", "女儿", "男儿", "红孩儿", "花儿", "虫儿", "马儿", "鸟儿", "猪儿", "猫儿",
            "狗儿"
        }
        self.vocab_phones = {}
        self.vocab_tones = {}
        if phone_vocab_path:
            with open(phone_vocab_path, 'rt') as f:
                phn_id = [line.strip().split() for line in f.readlines()]
            for phn, id in phn_id:
                self.vocab_phones[phn] = int(id)
        if tone_vocab_path:
            with open(tone_vocab_path, 'rt') as f:
                tone_id = [line.strip().split() for line in f.readlines()]
            for tone, id in tone_id:
                self.vocab_tones[tone] = int(id)
        print("initialized zh frontend")
    def __init__pypinyin(self):
        large_pinyin.load()
        #
        # load_phrases_dict({u'开户行': [[u'ka1i'], [u'hu4'], [u'hang2']]})
        # load_phrases_dict({u'发卡行': [[u'fa4'], [u'ka3'], [u'hang2']]})
        # load_phrases_dict({u'放款行': [[u'fa4ng'], [u'kua3n'], [u'hang2']]})
        # load_phrases_dict({u'茧行': [[u'jia3n'], [u'hang2']]})
        # load_phrases_dict({u'行号': [[u'hang2'], [u'ha4o']]})
        # load_phrases_dict({u'各地': [[u'ge4'], [u'di4']]})
        # load_phrases_dict({u'借还款': [[u'jie4'], [u'hua2n'], [u'kua3n']]})
        # load_phrases_dict({u'时间为': [[u'shi2'], [u'jia1n'], [u'we2i']]})
        # load_phrases_dict({u'为准': [[u'we2i'], [u'zhu3n']]})
        # load_phrases_dict({u'色差': [[u'se4'], [u'cha1']]})

        # 调整字的拼音顺序
        load_single_dict({ord(u'地'): u'de,di4'})

    def _get_initials_finals(self, word: str) -> List[List[str]]:
        initials = []
        finals = []
        if self.g2p_model == "pypinyin":
            orig_initials = lazy_pinyin(
                word, neutral_tone_with_five=True, style=Style.INITIALS)
            orig_finals = lazy_pinyin(
                word, neutral_tone_with_five=True, style=Style.FINALS_TONE3)
            for c, v in zip(orig_initials, orig_finals):
                if re.match(r'i\d', v):
                    if c in ['z', 'c', 's']:
                        v = re.sub('i', 'ii', v)
                    elif c in ['zh', 'ch', 'sh', 'r']:
                        v = re.sub('i', 'iii', v)
                initials.append(c)
                finals.append(v)
        elif self.g2p_model == "g2pM":
            pinyins = self.g2pM_model(word, tone=True, char_split=False)
            for pinyin in pinyins:
                pinyin = pinyin.replace("u:", "v")
                if pinyin in self.pinyin2phone:
                    initial_final_list = self.pinyin2phone[pinyin].split(" ")
                    if len(initial_final_list) == 2:
                        initials.append(initial_final_list[0])
                        finals.append(initial_final_list[1])
                    elif len(initial_final_list) == 1:
                        initials.append('')
                        finals.append(initial_final_list[1])
                else:
                    # If it's not pinyin (possibly punctuation) or no conversion is required
                    initials.append(pinyin)
                    finals.append(pinyin)
        return initials, finals

    # if merge_sentences, merge all sentences into one phone sequence
    def _g2p(self,
             sentences: List[str],
             merge_sentences: bool=True,
             with_erhua: bool=True) -> List[List[str]]:
        segments = sentences
        phones_list = []
        for seg in segments:
            phones = []
            # Replace all English words in the sentence
            seg = re.sub('[a-zA-Z]+', '', seg)
            seg_cut = psg.lcut(seg)
            initials = []
            finals = []
            seg_cut = self.tone_modifier.pre_merge_for_modify(seg_cut)
            for word, pos in seg_cut:
                if self.add_word_sep and word == "#":
                    continue
                if pos == 'eng':
                    continue
                sub_initials, sub_finals = self._get_initials_finals(word)
                sub_finals = self.tone_modifier.modified_tone(word, pos,
                                                              sub_finals)
                if with_erhua:
                    sub_initials, sub_finals = self._merge_erhua(
                        sub_initials, sub_finals, word, pos)
                initials.append(sub_initials)
                finals.append(sub_finals)
                if self.add_word_sep and word not in self.punc:
                    initials.append(["#"])
                    finals.append(["#"])

                # assert len(sub_initials) == len(sub_finals) == len(word)
            initials = sum(initials, [])
            finals = sum(finals, [])

            for c, v in zip(initials, finals):
                # NOTE: post process for pypinyin outputs
                # we discriminate i, ii and iii
                if c:
                    phones.append(c)
                if v and v not in self.punc:
                    phones.append(v)

            phones_list.append(phones)
        if merge_sentences:
            merge_list = sum(phones_list, [])
            # rm the last 'sp' to avoid the noise at the end
            # cause in the training data, no 'sp' in the end
            if merge_list[-1] == 'sp':
                merge_list = merge_list[:-1]
            phones_list = []
            phones_list.append(merge_list)
        return phones_list

    def _merge_erhua(self,
                     initials: List[str],
                     finals: List[str],
                     word: str,
                     pos: str) -> List[List[str]]:
        if word not in self.must_erhua and (word in self.not_erhua or
                                            pos in {"a", "j", "nr"}):
            return initials, finals
        # "……" 等情况直接返回
        if len(finals) != len(word):
            return initials, finals

        assert len(finals) == len(word)

        new_initials = []
        new_finals = []
        for i, phn in enumerate(finals):
            if i == len(finals) - 1 and word[i] == "儿" and phn in {
                    "er2", "er5"
            } and word[-2:] not in self.not_erhua and new_finals:
                new_finals[-1] = new_finals[-1][:-1] + "r" + new_finals[-1][-1]
            else:
                new_finals.append(phn)
                new_initials.append(initials[i])
        return new_initials, new_finals

    def _p2id(self, phonemes: List[str]) -> np.array:
        # replace unk phone with sp
        phonemes = [
            phn if phn in self.vocab_phones else "sp" for phn in phonemes
        ]
        phone_ids = [self.vocab_phones[item] for item in phonemes]
        return np.array(phone_ids, np.int64)

    def _t2id(self, tones: List[str]) -> np.array:
        # replace unk phone with sp
        tones = [tone if tone in self.vocab_tones else "0" for tone in tones]
        tone_ids = [self.vocab_tones[item] for item in tones]
        return np.array(tone_ids, np.int64)

    def _get_phone_tone(self, phonemes: List[str],
                        get_tone_ids: bool=False) -> List[List[str]]:
        phones = []
        tones = []
        if get_tone_ids and self.vocab_tones:
            for full_phone in phonemes:
                # split tone from finals
                match = re.match(r'^(\w+)([012345])$', full_phone)
                if match:
                    phone = match.group(1)
                    tone = match.group(2)
                    # if the merged erhua not in the vocab
                    # assume that the input is ['iaor3'] and 'iaor' not in self.vocab_phones, we split 'iaor' into ['iao','er']
                    # and the tones accordingly change from ['3'] to ['3','2'], while '2' is the tone of 'er2'
                    if len(phone) >= 2 and phone != "er" and phone[
                            -1] == 'r' and phone not in self.vocab_phones and phone[:
                                                                                    -1] in self.vocab_phones:
                        phones.append(phone[:-1])
                        phones.append("er")
                        tones.append(tone)
                        tones.append("2")
                    else:
                        phones.append(phone)
                        tones.append(tone)
                else:
                    phones.append(full_phone)
                    tones.append('0')
        else:
            for phone in phonemes:
                # if the merged erhua not in the vocab
                # assume that the input is ['iaor3'] and 'iaor' not in self.vocab_phones, change ['iaor3'] to ['iao3','er2']
                if len(phone) >= 3 and phone[:-1] != "er" and phone[
                        -2] == 'r' and phone not in self.vocab_phones and (
                            phone[:-2] + phone[-1]) in self.vocab_phones:
                    phones.append((phone[:-2] + phone[-1]))
                    phones.append("er2")
                else:
                    phones.append(phone)
        return phones, tones

    def get_phonemes(self,
                     sentence: str,
                     merge_sentences: bool=True,
                     with_erhua: bool=False,
                     robot: bool=False,
                     print_info: bool=False) -> List[List[str]]:
        sentence = sentence.replace("嗯", "恩")
        sentences = self.text_normalizer.normalize(sentence)
        phonemes = self._g2p(
            sentences, merge_sentences=merge_sentences, with_erhua=with_erhua)
        # change all tones to `1`
        if robot:
            new_phonemes = []
            for sentence in phonemes:
                new_sentence = []
                for item in sentence:
                    # `er` only have tone `2`
                    if item[-1] in "12345" and item != "er2":
                        item = item[:-1] + "1"
                    new_sentence.append(item)
                new_phonemes.append(new_sentence)
            phonemes = new_phonemes
        if print_info:
            print("----------------------------")
            print("text norm results:")
            print(sentences)
            print("----------------------------")
            print("g2p results:")
            print(phonemes)
            print("----------------------------")
        return phonemes
