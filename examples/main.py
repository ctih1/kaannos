import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # Just used for examples. Fixes import error, as the key_compiler isnt in the examples folder
import key_compiler

locales = os.path.join("examples", "locales")
output_path = os.path.join("examples", "keys.py")
key_compiler.build_result(
    primary_lang="en", # Using english as the primary language
    locale_dir=locales, # The path to our localization files
    output_path=output_path, # Python file where the keys will be stored
    types=True, # Enables types in the generated file
    generate_comments=True # Add intellisense function comments to show the keys in each language
) # > INFO: [key_compiler.py:build_result] Done in 0.005094289779663086s

# We can now use our keys

import keys as k

# Using keys
print(k.user_intro(user="Example user"))
print(k.description())

print()

# Changing languages
for language in k.languages:
    k.change_language(language)
    print(k.user_intro(user="Example user"))

print()

target_lang = input(f"Please enter what language to use. Available languages: {k.languages} ")
if target_lang not in k.languages:
    print("Invalid language!")

k.change_language(target_lang)
print(k.description())

print()

# Using a specifiy language
print(f"Description in english: {k.description(lang="en")}")
print(f"Description in finnish: {k.description(lang="fi")}")