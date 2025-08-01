# The MIT License (MIT)

# Copyright (c) 2025 ctih1

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import os
from typing import Dict, List, Literal
import json
import sys
import logging
import time

NOTICE = """
# This file was automatically created from localization JSON files.
# DO NOT EDIT THIS FILE DIRECTLY. If you want to edit a translation, please use the language's JSON file.

#fmt: off
"""


logger = logging.getLogger("kaannos")


class LanguageCollector:
    def __init__(self, language_dir: str) -> None:
        self.path: str = language_dir
        self.languages: Dict[str, Dict[str, str]] = {}

        for file in os.listdir(self.path):
            if not file.endswith(".json") or len(file) > 7:
                logger.debug(f"Skipping {file}")
                continue

            locale: str = file.split(".json")[0]
            logger.info(f"Discovered {file}")
            with open(os.path.join(self.path, file), "r", encoding="UTF-8") as f:
                keys: Dict[str, str] = json.load(f)
                self.languages[locale] = keys

        self.find_missing_keys()

    def find_missing_keys(self) -> None:
        primary_language_keys: Dict[str, str] = self.languages["en"]

        for key in primary_language_keys:
            for language in self.languages:
                if key not in self.languages[language]:
                    logger.warning(f"Key {key} missing from {language}")

        for language in self.languages:
            for key in self.languages[language]:
                if key not in primary_language_keys:
                    logger.warning(f"Leftover key {key} found from {language}")


class Script:
    def __init__(self) -> None:
        self.script: str = ""

    def add_line(self, content, indent: int = 0, newline: bool = True) -> None:
        tabs = "\t" * indent
        newline_content = "\n" if newline else ""

        self.script += f"{tabs}{content}{newline_content}"


def process_name(key: str) -> str:
    return key.replace(" ", "_").replace(":", "").lower()


def find_args(string: str) -> List[str]:
    variable_open: bool = False
    temp_content: str = ""

    variables: List[str] = []
    for char in string:
        if variable_open:
            if char == "}":
                variable_open = False
                variables.append(temp_content)
                temp_content = ""
                continue

            if char == "{":
                raise SyntaxError("Variable already open!")

            temp_content += char

        else:
            if char == "}":
                raise SyntaxError("Trying to close a nonexistant variable")

            if char == "{":
                variable_open = True

    return variables


def convert_args(
    inp: str, vars: List[str], mode: Literal["brackets", "none"] = "brackets"
) -> str:
    replacements = {".": "_", ",": "_"}

    for var in vars:
        cleaned_var = var
        for key, val in replacements.items():
            cleaned_var = cleaned_var.replace(key, val)

        if mode == "none":
            inp = inp.replace(f"{var}", f"{cleaned_var}")
        else:
            inp = inp.replace(f"{{{var}}}", f"{{{cleaned_var}}}")

    return inp


class GenerateScript:
    def __init__(
        self,
        primary_lang: str,
        language_data: Dict[str, Dict[str, str]],
        use_typing: bool = True,
        output_path: str = "out.py",
        generate_comments: bool = True,
    ):
        self.data = language_data
        self.primary = primary_lang
        self.script = Script()
        self.uses_typing: bool = use_typing
        self.output = output_path
        self.generate_comments = generate_comments

    def create(self):
        # I really don't like this implementation but also it works
        self.script.add_line(NOTICE)
        if self.uses_typing:
            self.script.add_line("from typing import Literal, List")
            self.script.add_line(f"Language=Literal{list(self.data.keys())}")
            self.script.add_line(
                f"languages: List[Language] = {list(self.data.keys())}"
            )
            self.script.add_line(f"default_lang: Language | str='{self.primary}'")
            self.script.add_line(
                "def change_language(new_lang: Language | str) -> None: global default_lang; default_lang = new_lang"
            )
        else:
            self.script.add_line(f"languages = {list(self.data.keys())}")
            self.script.add_line(f"default_lang='{self.primary}'")
            self.script.add_line(
                "def change_language(new_lang): global default_lang; default_lang = new_lang"
            )

        self.primary_data = self.data[self.primary]

        for key in self.primary_data:
            args = find_args(self.primary_data[key])

            self.script.add_line(
                f"def {process_name(key)}({convert_args(','.join([*args, 'lang:str|None=None' if self.uses_typing else 'lang']), args, 'none')}):"
            )
            if self.generate_comments:
                self.script.add_line('"""', 1)
                self.script.add_line("### Locales", 1)
                for language in self.data:
                    self.script.add_line(
                        f"- {language.capitalize()}: **{self.data[language].get(key, self.primary_data[key])}**",
                        1,
                    )
                self.script.add_line('"""', 1)
            self.script.add_line("if not lang: lang=default_lang", 1)
            for language in self.data:
                formatted_map = "{"
                for arg in args:
                    formatted_map += f'"{convert_args(arg, args, "none")}": {convert_args(arg, args, "none")},'
                formatted_map = formatted_map[:-1] + "}"
                self.script.add_line(
                    f"""if lang == '{language}': return {convert_args(json.dumps(
                    self.data[language].get(key,self.primary_data[key]), 
                    ensure_ascii=False
                ), args)}{f'.format_map({formatted_map})' if len(args) > 0 else ''}""",
                    1,
                )

            self.script.add_line(
                "else: raise ValueError(f'Invalid language {lang}')", 1
            )
        with open(self.output, "w", encoding="UTF-8") as f:
            f.write(self.script.script)


def build_result(
    primary_lang: str,
    locale_dir: str,
    types: bool,
    output_path: str,
    generate_comments: bool = True,
):
    start = time.time()
    lc = LanguageCollector(locale_dir)
    GenerateScript(
        primary_lang, lc.languages, types, output_path, generate_comments
    ).create()
    logger.info(f"Done in {time.time() - start}s")
