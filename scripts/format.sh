#!/bin/sh
cd "$(dirname "$0")" || exit 1
cd ..


printf "\nFormatting Python 🧹\n"
poetry run black .

printf "\nSorting imports 🧹\n"
poetry run isort .

