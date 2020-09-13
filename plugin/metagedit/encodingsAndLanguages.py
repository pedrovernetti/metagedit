
# =============================================================================================
# This program is free software: you can redistribute it and/or modify it under the terms of
# the GNU General Public License as published by the Free Software Foundation, either version
# 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# This script must/should come together with a copy of the GNU General Public License. If not,
# access <http://www.gnu.org/licenses/> to find and read it.
#
# Author: Pedro Vernetti G.
# Name: Metagedit
# Description: gedit plugin which adds multiple improvements and functionalities to it
#
# #  In order to have this script working (if it is currently not), run 'install.sh'.
# =============================================================================================

import re
from locale import getdefaultlocale as getDefaultLocale
import iso639



def defaultLanguage():
    language = iso639.languages.part1.get(getDefaultLocale()[0][:2])
    return re.sub(r',.*$', r'', language.name)

def defaultLanguageISO6391():
    return getDefaultLocale()[0][:2]

def defaultLanguageISO6392B():
    language = iso639.languages.part1.get(getDefaultLocale()[0][:2])
    return language.part2b



## ENCODING STUFF

_arabic = {r'eng', r'ara'}
_arabic_ext = _arabic | {r'fas', r'per', r'urd'}
_baltic = {r'eng', r'est', r'lav', r'lit'}
_baltic_ext = _baltic | {r'fin', r'pol'}
_celtic = {r'eng', r'bre', r'cor', r'cym', r'gla', r'gle', r'glv', r'mga', r'wel'}
_chinese = {r'chi', r'zho'} #TODO
_russian = {r'eng', r'bul', r'rus'}
_cyrillic = _russian | {r'bel', r'ukr'}
_cyrillic_ext = _cyrillic | {r'mac', r'srp'}
_eastern_european = {} #TODO
_esperanto = {r'eng', r'epo', r'mlt', r'tur'}
_greek = {r'eng', r'ell', r'gre'}
_hebrew = {r'eng', r'heb', r'lad', r'yid'}
_japanese = {r'eng', r'ain', r'jpn'}
_japanese_rus = _japanese | _russian
_japanese_ext = _japanese_rus | _greek | _chinese
_kazakh = _russian | {r'kaz'}
_korean = {r'eng', r'kor', r'rus'}
_latin4 = _baltic | {r'kal', r'sma', r'sme', r'smi', r'smj', r'smn', r'smo', r'sms'}
_nordic = {r'eng', r'dan', r'deu', r'fao', r'ger', r'nno', r'nob', r'nor', r'swe'}
_nordic_ext = _nordic | {r'ice'}
_baltic_nordic = _baltic_ext | _nordic | {r'deu', r'ger'}
_romance = {r'eng', r'ita', r'por', r'spa'}
_southern_european = {r'eng', r'alb', r'bos', r'deu', r'fre', r'ger', r'gle', r'hrv', r'hun', r'ita', r'pol', r'rum', r'slv', r'sqi', r'srp'}
_tajik = _russian | {r'tgk'}
_thai = {r'eng', r'tha'}
_turkish = {r'eng', r'tur'}
_ukrainian = _russian | {r'ukr'}
_vietnamese = {r'eng', r'vie'}

globalEncodings = [r'U8', r'UTF-8', r'UTF-8_sig', r'U16', r'UTF-16', r'UTF-16BE', r'UTF-16LE', r'U32', r'UTF-32', r'UTF-32BE', r'UTF-32LE', r'U7', r'UTF-7', r'CP65001', r'ASCII', r'US-ASCII', r'646', '437', r'CP437', r'IBM437']

specializedEncodings = {r'1125':_cyrillic, r'273':{}, r'850':{}, r'852':{}, r'855':_cyrillic_ext, r'857':{}, r'858':{}, r'860':_romance, r'861':_nordic_ext, r'862':_hebrew, r'863':{}, r'865':_nordic, r'866':_cyrillic, r'869':_greek, r'8859':{}, r'932':_japanese, r'936':{}, r'949':_korean, r'950':_chinese, r'BIG5':_chinese, r'BIG5-HKSCS':_chinese, r'BIG5-TW':_chinese, r'CP-GR':_greek, r'CP-IS':_nordic_ext, r'CP037':{}, r'CP1006':{r'eng', r'urd'}, r'CP1026':{}, r'CP1125':_cyrillic, r'CP1140':{}, r'CP1250':{}, r'CP1251':_cyrillic_ext, r'CP1252':{}, r'CP1253':_greek, r'CP1254':{}, r'CP1255':_hebrew, r'CP1256':_arabic_ext, r'CP1257':_baltic_nordic, r'CP1258':_vietnamese, r'CP1361':{}, r'CP154':_kazakh, r'CP273':{}, r'CP424':_hebrew, r'CP500':{}, r'CP720':_arabic, r'CP737':_greek, r'CP775':_baltic_nordic, r'CP819':{}, r'CP850':{}, r'CP852':{}, r'CP855':_cyrillic_ext, r'CP856':_hebrew, r'CP857':{}, r'CP858':{}, r'CP860':_romance, r'CP861':_nordic_ext, r'CP862':_hebrew, r'CP863':{}, r'CP864':_arabic, r'CP865':{}, r'CP866':_cyrillic, r'CP866U':_cyrillic, r'CP869':_greek, r'CP874':_thai, r'CP875':_greek, r'CP932':_japanese, r'CP936':{}, r'CP949':_korean, r'CP950':_chinese, r'csISO58GB231280':_chinese, r'EBCDIC-CP-BE':{}, r'EBCDIC-CP-CH':{}, r'EBCDIC-CP-HE':_hebrew, r'EUC JIS 2004':_japanese_ext, r'EUC JISX0213':_japanese_ext, r'EUC-CN':_chinese, r'EUC-JP':_japanese_rus, r'EUC-KR':_korean, r'EUCGB2312-CN':_chinese, r'GB18030':_chinese, r'GB18030-2000':_chinese, r'GB2312':_chinese, r'GB2312-80':_chinese, r'GBK':{}, r'Greek8':_greek, r'HKSCS':_chinese, r'HZ':{}, r'HZ-GB':{}, r'HZ-GB-2312':{}, r'IBM037':{}, r'IBM039':{}, r'IBM1026':{}, r'IBM1125':_cyrillic, r'IBM1140':{}, r'IBM273':{}, r'IBM424':_hebrew, r'IBM500':{}, r'IBM775':{}, r'IBM850':{}, r'IBM852':{}, r'IBM855':_cyrillic_ext, r'IBM857':{}, r'IBM858':{}, r'IBM860':_romance, r'IBM861':_nordic_ext, r'IBM862':_hebrew, r'IBM863':{}, r'IBM864':_arabic, r'IBM865':_nordic, r'IBM866':_cyrillic, r'IBM869':_greek, r'ISO-2022-JP':{}, r'ISO-2022-JP-1':{}, r'ISO-2022-JP-2':{}, r'ISO-2022-JP-2004':{}, r'ISO-2022-JP-3':{}, r'ISO-2022-JP-EXT':{}, r'ISO-2022-KR':{}, r'ISO-8859-1':{}, r'ISO-8859-10':_nordic_ext, r'ISO-8859-11':_thai, r'ISO-8859-13':_baltic_ext, r'ISO-8859-14':_celtic, r'ISO-8859-15':{}, r'ISO-8859-16':_southern_european, r'ISO-8859-2':{}, r'ISO-8859-3':{}, r'ISO-8859-4':_latin4, r'ISO-8859-5':_cyrillic_ext, r'ISO-8859-6':_arabic, r'ISO-8859-7':_greek, r'ISO-8859-8':_hebrew, r'ISO-8859-9':_turkish, r'ISO-IR-58':_chinese, r'JISX0213':_japanese_ext, r'Johab':{}, r'KOI8_R':_russian, r'KOI8_T':_tajik, r'KOI8_U':_ukrainian, r'KS C-5601':_korean, r'KS X-1001':_korean, r'KZ 1048':_kazakh, r'L1':{}, r'L10':_southern_european, r'L2':{}, r'L3':{}, r'L4':_latin4, r'L5':{}, r'L6':_nordic_ext, r'L7':_baltic_ext, r'L8':_celtic, r'L9':{}, r'Latin1':{}, r'Latin10':_southern_european, r'Latin2':{}, r'Latin3':{}, r'Latin4':_latin4, r'Latin5':{}, r'Latin6':_nordic_ext, r'Latin7':_baltic_ext, r'Latin8':_celtic, r'Latin9':{}, r'Mac Cyrillic':_cyrillic_ext, r'Mac Greek':{}, r'Mac Iceland':_nordic_ext, r'Mac Latin2':{}, r'Mac Roman':{}, r'Mac Turkish':{}, r'MacCentralEurope':{}, r'Macintosh':{}, r'MS-Kanji':_japanese, r'MS1361':{}, r'MS932':_japanese, r'MS936':{}, r'MS949':_korean, r'MS950':{}, r'PT154':_kazakh, r'PTCP154':_kazakh, r'RK1048':_kazakh, r'RUSCII':_cyrillic, r'Shift JIS':_japanese_rus, r'Shift JIS_2004':_japanese_rus, r'Shift JISX0213':_japanese_rus, r'SJIS 2004':_japanese_rus, r'SJIS':_japanese_rus, r'SJISX0213':_japanese_rus, r'STRK1048 2002':_kazakh, r'UHC':_korean, r'UJIS':_japanese_rus, r'Windows-1250':{}, r'Windows-1251':_cyrillic_ext, r'Windows-1252':{}, r'Windows-1253':_greek, r'Windows-1254':_turkish, r'Windows-1255':_hebrew, r'Windows-1256':_arabic_ext, r'Windows-1257':_baltic_nordic, r'Windows-1258':_vietnamese, r'Windows-932':_japanese, r'Windows-949':_korean} #TODO: fill missing encodings
  # Unsuported: ISCII, ASMO, VISCII, Windows-31J/MS932, TIS-620/MacThai [->CP874]

def supportedEncodings( languageISO6392=r'mul' ):
    encodings = []
    if (languageISO6392 in {r'', r'mul', r'und', r'zxx'}):
        encodings = [e for e in specializedEncodings.keys()]
    else:
        for e, supportedLanguages in specializedEncodings.items():
            if (languageISO6392 in supportedLanguages): encodings.append(e)
    encodings += reversed(globalEncodings)
    sortKey = lambda x: re.sub(r'[-_\s]+', r'', x).casefold()
    return sorted(encodings, key=sortKey, reverse=True)
