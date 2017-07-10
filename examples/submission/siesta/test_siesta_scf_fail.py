#!/usr/bin/env runaiida
# -*- coding: utf-8 -*-

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.7.0"
__contributors__ = "Andrea Cepellotti, Victor Garcia-Suarez, Alberto Garcia, Emanuele Bosoni"

#
# This is an example of a calculation that will end in a FAILED state due
# to lack of scf convergence in the allotted number of iterations.
# To restart, either in a verdi shell or via a script, do:
#
# c = load_node(PK)
# c2 = c.create_restart(force_restart=True)
# c2.store_all()
# c2.submit()
#
# (You can use the 'test_siesta_restart.py' script)

import sys
import os

from aiida.common.example_helpers import test_and_get_code
from aiida.common.exceptions import NotExistent

################################################################

PsfData = DataFactory('siesta.psf')
ParameterData = DataFactory('parameter')
KpointsData = DataFactory('array.kpoints')
StructureData = DataFactory('structure')

try:
    dontsend = sys.argv[1]
    if dontsend == "--dont-send":
        submit_test = True
    elif dontsend == "--send":
        submit_test = False
    else:
        raise IndexError
except IndexError:
    print >> sys.stderr, ("The first parameter can only be either "
                          "--send or --dont-send")
    sys.exit(1)

try:
    codename = sys.argv[2]
except IndexError:
    codename = 'Siesta-4.0@rinaldo'

# If True, load the pseudos from the family specified below
# Otherwise, use static files provided
auto_pseudos = False

queue = None
settings = None

code = test_and_get_code(codename, expected_code_type='siesta.siesta')

alat = 5.430 # angstrom
cell = [[0.5*alat, 0.5*alat, 0.,],
        [0., 0.5*alat, 0.5*alat,],
        [0.5*alat, 0., 0.5*alat,],
       ]

# Si
# This was originally given in the "ScaledCartesian" format
#
s = StructureData(cell=cell)
s.append_atom(position=(0.000*alat,0.000*alat,0.000*alat),symbols=['Si'])
s.append_atom(position=(0.250*alat,0.250*alat,0.250*alat),symbols=['Si'])


elements = list(s.get_symbols_set())

if auto_pseudos:
    valid_pseudo_groups = PsfData.get_psf_groups(filter_elements=elements)

    try:
        #pseudo_family = sys.argv[3]
        pseudo_family = 'lda-ag'
    except IndexError:
        print >> sys.stderr, "Error, auto_pseudos set to True. You therefore need to pass as second parameter"
        print >> sys.stderr, "the pseudo family name."
        print >> sys.stderr, "Valid PSF families are:"
        print >> sys.stderr, "\n".join("* {}".format(i.name) for i in valid_pseudo_groups)
        sys.exit(1)

    try:
        PsfData.get_psf_group(pseudo_family)
    except NotExistent:
        print >> sys.stderr, "auto_pseudos is set to True and pseudo_family='{}',".format(pseudo_family)
        print >> sys.stderr, "but no group with such a name found in the DB."
        print >> sys.stderr, "Valid PSF groups are:"
        print >> sys.stderr, ",".join(i.name for i in valid_pseudo_groups)
        sys.exit(1)

parameters = ParameterData(dict={
                'xc:functional': 'LDA',
                'xc:authors': 'CA',
                'spinpolarized': True,
                'meshcutoff': '40.000 Ry',
                'dm:numberpulay': 4,
                'dm:mixingweight': 0.3,
                'dm:tolerance': 1.e-3,
                'max-scfiterations': 3,
                'scf-must-converge': True,
                'Solution-method': 'diagon',
                'electronic-temperature': '25 meV',
                'md-typeofrun': 'cg',
                'md-numcgsteps': 0,
                'md-maxcgdispl': '0.1 Ang',
                'md-maxforcetol': '0.04 eV/Ang',
                'writeforces': True,
                'writecoorstep': True,
                'xml:write': True
                })

basis = ParameterData(dict={
'pao-energy-shift': '300 meV',
'%block pao-basis-sizes': """
Si DZP                    """,
})

kpoints = KpointsData()

# method mesh
kpoints_mesh = 4
kpoints.set_kpoints_mesh([kpoints_mesh,kpoints_mesh,kpoints_mesh])


# (the object settings is optional)
settings_dict={'test_key': 'test_value'}
settings = ParameterData(dict=settings_dict)

calc = code.new_calc()
calc.label = "Si_bulk"
calc.description = "Siesta scf non-convergence test"
calc.set_max_wallclock_seconds(100) 

calc.set_resources({"num_machines": 1})
code_mpi_enabled =  False
try:
    code_mpi_enabled =  code.get_extra("mpi")
except AttributeError:
    pass
calc.set_withmpi(code_mpi_enabled)

#calc.set_custom_scheduler_commands("#SBATCH --account=ch3")

if queue is not None:
    calc.set_queue_name(queue)

calc.use_structure(s)
calc.use_parameters(parameters)
calc.use_basis(basis)

if auto_pseudos:
    try:
        calc.use_pseudos_from_family(pseudo_family)
        print "Pseudos successfully loaded from family {}".format(pseudo_family)
    except NotExistent:
        print ("Pseudo or pseudo family not found. You may want to load the "
               "pseudo family, or set auto_pseudos to False.")
        raise
else:
    raw_pseudos = [("Si.psf", 'Si')]

    for fname, kinds, in raw_pseudos:
      absname = os.path.realpath(os.path.join(os.path.dirname(__file__),
                                            "data",fname))
      pseudo, created = PsfData.get_or_create(absname,use_first=True)
      if created:
        print "Created the pseudo for {}".format(kinds)
      else:
        print "Using the pseudo for {} from DB: {}".format(kinds,pseudo.pk)
        
      # Attach pseudo node to the calculation
      calc.use_pseudo(pseudo,kind=kinds)

calc.use_kpoints(kpoints)

# K-points for bands
# NOTE: bandskpoints.set_cell(s.cell, s.pbc) HAS TO BE SET ALWAYS ###
bandskpoints = KpointsData()

##..kp path automatically generated from structure (all high-simmetry point)..##
##.....labels automatically included, 0.05 is the distance between kpoints....##
bandskpoints.set_cell(s.cell, s.pbc)
bandskpoints.set_kpoints_path(kpoint_distance = 0.05)

calc.use_bandskpoints(bandskpoints)

if settings is not None:
    calc.use_settings(settings)

if submit_test:
    subfolder, script_filename = calc.submit_test()
    print "Test_submit for calculation (uuid='{}')".format(
        calc.uuid)
    print "Submit file in {}".format(os.path.join(
        os.path.relpath(subfolder.abspath),
        script_filename
        ))
else:
    calc.store_all()
    print "created calculation; calc=Calculation(uuid='{}') # ID={}".format(
        calc.uuid,calc.dbnode.pk)
    calc.submit()
    print "submitted calculation; calc=Calculation(uuid='{}') # ID={}".format(
        calc.uuid,calc.dbnode.pk)

