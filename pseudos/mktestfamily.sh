#!/usr/bin/env bash
python /home/dix/.virtualenvs/aiidaenv/bin/activate_this.py
verdi data psf uploadfamily . test_psf_family "Test *.psf pseudopotentials family for aiida_siesta example scripts."
