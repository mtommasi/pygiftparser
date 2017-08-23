#!/usr/bin/python3
# -*- coding: utf-8 -*-
import logging
from pygiftparser import i18n
from pygiftparser import question
from pygiftparser import utils

_ = i18n.language.gettext


def parseFile(f):
    """
    parse a file to transform a text in GIFT format to an list of questions
    """
    cleanedSource = fullSource = ""
    category = '$course$'
    newCategory = None
    questions = []

    for line in f:
        if utils.reSepQuestions.match(line):
            if newCategory:
                # the previous line was a category declaration
                category = newCategory
                newCategory = None
            else:
                if cleanedSource != "":
                    # this is the end of a question
                    questions.append(question.Question(cleanedSource,
                                                       fullSource,
                                                       category))
                cleanedSource = fullSource = ""
        else:
            # it is not a blank line : is it a category definition?
            match = utils.reCategory.match(line)
            if match:
                newCategory = match.group('cat')
                continue

            # is it a comment ?
            if not utils.reComment.match(line):
                cleanedSource += line
            fullSource += line

    if cleanedSource != "":
        questions.append(question.Question(cleanedSource,
                                           fullSource,
                                           category))

    return questions


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Parses gift files.")
    parser.add_argument("-l", "--log",
                        dest="logLevel",
                        choices=['DEBUG', 'INFO',
                                 'WARNING', 'ERROR',
                                 'CRITICAL'],
                        help="Set the logging level",
                        default='WARNING')
    parser.add_argument('f',
                        help="gift file",
                        type=argparse.FileType('r'))
    parser.add_argument('-H',
                        '--html',
                        help="html output",
                        action="store_true")
    args = parser.parse_args()
    logging.basicConfig(filename='gift.log',
                        filemode='w',
                        level=getattr(logging,
                                      args.logLevel))

    questions = parseFile(args.f)
    args.f.close()

    for q in questions:
        if args.html:
            d = q.toHTML()
            print(d.getvalue())
            print("<hr />")
        else:
            q.myprint()
