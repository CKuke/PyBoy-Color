
.PHONY: build

all: build

PY := python3
ROOT_DIR := $(shell git rev-parse --show-toplevel)

build:
	${PY} logo_to_tiles.py
	rgbasm -o dmgbootrom.obj dmgbootrom.asm
	rgblink -m dmgbootrom.map -n dmgbootrom.sym -o dmgbootrom.gb dmgbootrom.obj
	rgbfix -p0 -v dmgbootrom.gb
	head -c 256 dmgbootrom.gb > ${ROOT_DIR}/pyboy/core/dmgbootrom.bin

	${PY} logo_to_tiles.py
	rgbasm -o cgbbootrom.obj cgbbootrom.asm
	rgblink -m cgbbootrom.map -n cgbbootrom.sym -o cgbbootrom.gb cgbbootrom.obj
	rgbfix -p0 -v cgbbootrom.gb
	head -c 256 cgbbootrom.gb > ${ROOT_DIR}/pyboy/core/cgbbootrom.bin


clean:
	rm logo.asm bootrom.map bootrom.sym bootrom.obj bootrom.gb
