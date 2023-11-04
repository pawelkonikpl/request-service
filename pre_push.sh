#!/usr/bin/env bash
echo -e "Run black................................"
black .
echo -e "Black finish..............................\n\n"

echo -e "Run isort................................"
isort .
echo -e "Isort finish..............................\n\n"

echo -e "Run flake................................."
flake8 . > &2
