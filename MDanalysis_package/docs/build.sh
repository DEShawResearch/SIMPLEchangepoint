#!/bin/sh

set -e
set -x
if [[ -e docs ]] ; then cd docs ; fi
rm -rf out
desres-with -m dvipng/1.13-03A/bin -m Sphinx/1.2.2-05A/bin -m Sphinx-latex-fix/0.1/lib-python \
    sphinx-build -b html ./source ./out/html

cd out
tar -czf html.tar.gz html/
mv html.tar.gz ..

#sphinx-build -b singlehtml ./source ./out/single-html
#sphinx-build -b latex ./source ./out/latex
#cd out/latex
#latex Changepoint.tex
#latex Changepoint.tex
#pdflatex Changepoint.tex
#cd ..
#cp latex/Changepoint.tex .
#rm -rf latex
