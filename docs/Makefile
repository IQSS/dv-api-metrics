# Makefile to automatically build code documentation

SRC = ../src
SCRIPTS = ../scripts
BUILDDIR = build

# builds code and scripts documentation
all :
	pdoc -o "$(BUILDDIR)" "$(SRC)"
	pdoc -o "$(BUILDDIR)" "$(SCRIPTS)"

# deletes existing documentation, then builds documentation
clean : 
	pdoc -o "$(BUILDDIR)" "$(SRC)" --force
	pdoc -o "$(BUILDDIR)" "$(SCRIPTS)" --force