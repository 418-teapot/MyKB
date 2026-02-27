objects = CompilationSystem.svg HardwareOrganization.svg MemoryHierarchy.svg \
          LayeredViewOfComputer.svg AbstractionsOfOS.svg VirtualAddressSpace.svg \
          AbstractionsOfSystem.svg

all: $(objects)

$(objects): %.svg: %.pdf
	pdftocairo $< -svg

%.pdf: %.tex
	latexmk -xelatex $<

clean:
	latexmk -c
	rm *.xdv *.pdf

.PHONY: all clean
