'''
Defines the set of symbols used in text input to the model.
'''


# cjke_cleaners2
_pad        = '_'
_punctuation = ',.!?-~…'
_letters = 'NQabdefghijklmnopstuvwxyzɑæʃʑçɯɪɔɛɹðəɫɥɸʊɾʒθβŋɦ⁼ʰ`^#*=ˈˌ→↓↑ '

_extra = "ˌ%$"
# Export all symbols:
symbols = [_pad] + list(_punctuation) + list(_letters) + list(_extra)

# Special symbol ids
SPACE_ID = symbols.index(" ")
