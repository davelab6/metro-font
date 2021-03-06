#!/usr/bin/env python2
# encoding: utf-8

import argparse
from datetime import datetime
from sortsmill import ffcompat as fontforge
import psMat
import math

def handle_cloned_glyphs(font):
    for glyph in font.glyphs():
        if glyph.color == 0xff00ff:
            assert len(glyph.references) > 0, glyph
            base = glyph.references[0][0]
            base = font[base]
            assert base.anchorPoints, glyph
            glyph.anchorPoints = base.anchorPoints

def merge(args):
    arabic = fontforge.open(args.arabicfile)
    arabic.encoding = "Unicode"
    arabic.mergeFeature(args.feature_file)

    latin = fontforge.open(args.latinfile)
    latin.encoding = "Unicode"
    latin.em = arabic.em

    latin_locl = ""
    for glyph in latin.glyphs():
        if glyph.color == 0xff0000:
            latin.removeGlyph(glyph)
        else:
            if glyph.glyphname in arabic:
                name = glyph.glyphname
                glyph.unicode = -1
                glyph.glyphname = name + ".latin"
                if not latin_locl:
                    latin_locl = "feature locl {lookupflag IgnoreMarks; script latn;"
                latin_locl += "sub %s by %s;" % (name, glyph.glyphname)

    arabic.mergeFonts(latin)
    if latin_locl:
        latin_locl += "} locl;"
        arabic.mergeFeatureString(latin_locl)

    for ch in [(ord(u'،'), "comma"), (ord(u'؛'), "semicolon")]:
        ar = arabic.createChar(ch[0], fontforge.nameFromUnicode(ch[0]))
        en = arabic[ch[1]]
        colon = arabic["colon"]
        ar.addReference(en.glyphname, psMat.rotate(math.radians(180)))
        delta = colon.boundingBox()[1] - ar.boundingBox()[1]
        ar.transform(psMat.translate(0, delta))
        ar.left_side_bearing = en.right_side_bearing
        ar.right_side_bearing = en.left_side_bearing

    question_ar = arabic.createChar(ord(u'؟'), "uni061F")
    question_ar.addReference("question", psMat.scale(-1, 1))
    question_ar.left_side_bearing = arabic["question"].right_side_bearing
    question_ar.right_side_bearing = arabic["question"].left_side_bearing

    # Set metadata
    arabic.version = args.version
    years = datetime.now().year == 2015 and 2015 or "2015-%s" % datetime.now().year

    arabic.copyright = ". ".join(["Portions copyright © %s, Khaled Hosny (<khaledhosny@eglug.org>)",
                              "Portions " + latin.copyright[0].lower() + latin.copyright[1:].replace("(c)", "©")])
    arabic.copyright = arabic.copyright % years

    handle_cloned_glyphs(arabic)

    en = "English (US)"
    arabic.appendSFNTName(en, "Designer", "Khaled Hosny")
    arabic.appendSFNTName(en, "License URL", "http://scripts.sil.org/OFL")
    arabic.appendSFNTName(en, "License", 'This Font Software is licensed under the SIL Open Font License, Version 1.1. \
This Font Software is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR \
CONDITIONS OF ANY KIND, either express or implied. See the SIL Open Font License \
for the specific language, permissions and limitations governing your use of \
this Font Software.')
    arabic.appendSFNTName(en, "Descriptor", "Mada is a geometric, unmodulted Arabic display typeface inspired by Cairo road signage.")
    arabic.appendSFNTName(en, "Sample Text", "صف خلق خود كمثل ٱلشمس إذ بزغت يحظى ٱلضجيع بها نجلاء معطار.")

    return arabic

def main():
    parser = argparse.ArgumentParser(description="Create a version of Amiri with colored marks using COLR/CPAL tables.")
    parser.add_argument("arabicfile", metavar="FILE", help="input font to process")
    parser.add_argument("latinfile", metavar="FILE", help="input font to process")
    parser.add_argument("--out-file", metavar="FILE", help="output font to write", required=True)
    parser.add_argument("--feature-file", metavar="FILE", help="output font to write", required=True)
    parser.add_argument("--version", metavar="version", help="version number", required=True)

    args = parser.parse_args()

    font = merge(args)

    flags = ["round", "opentype", "no-mac-names"]
    font.generate(args.out_file, flags=flags)

if __name__ == "__main__":
    main()
