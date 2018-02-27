import logging as log
import numpy as np
import os as os
import re as re
import subprocess as sp
import parmed as pmd

from .utils import check_for_leap_log

def add_dummy(input_structure, atom_name='DUM', res_name='DUM', x=0.000, y=0.000, z=0.000):
    """ Add a dummy atom at the specified coordinates to the end of the structure """

    # Assume the input_structure is a filename or ...
    if type(input_structure) is str:
        structure = align.return_structure(input_structure)
    # ... a parmed.structure
    elif type(input_structure) is RefStructureForCmp:
        structure = input_structure
    else:
        raise Exception('add_dummy does not support the type associated with input_structure:'+type(input_structure))

    dum = pmd.topologyobjects.Atom()
    dum.name = atom_name
    dum.xx = x
    dum.xy = y
    dum.xz = z
    
    # This assumes that the atom numbering we read in is correct!!
    dum.number = structure.atoms[-1].number + 1
    res_num = structure.residues[-1].number + 1
    
    structure.add_atom(dum, res_name, res_num)

    # tleap will probably want TER cards in any PDBs we make, so enforce
    # that for both the dummy residue and the residue before it
    structure.residues[-2].ter = True
    structure.residues[-1].ter = True

    return structure



def read_tleaplines(tleapfile, pdbfile=None, skip_solvate=True):
    """
    Read a functional tleap file and return a list containing each line of instruction
    
        tleapfile : A functioning tleap input file which properly builds your system
        pdbfile : If specified, replace the loadpdb target with that specified by pdbfile.
        skip_solvate : If True, skip over solvatebox or addion type statements.
    """

    # Read tleapfile
    tleaplines = []
    with open(tleapfile, 'r') as f:
        for line in f.readlines():
            if re.search('loadpdb', line):
                words = line.rstrip().replace('=', ' ').split()
                if pdbfile is None:
                    pdbfile = words[2]
                unit = words[0]
                tleaplines.append("{} = loadpdb {}\n".format(unit, pdbfile))
            if not re.search(
                    r"^\s*addions|^\s*addions2|^\s*addionsrand|^\s*desc|"
                    r"^\s*quit|^\s*solvate|loadpdb|^\s*save", line,
                    re.IGNORECASE):
                tleaplines.append(line)

    return tleaplines


def write_tleapin(filename='tleap.in',
                  directory='.',
                  tleaplines=[],
                  unit='model',
                  pbctype=1,
                  bufferval=12.0,
                  waterbox='TIP3BOX',
                  neutralize=True,
                  counter_cation='Na+',
                  counter_anion='Cl-',
                  addion_residues=None,
                  addion_values=None,
                  removewat=None,
                  saveprefix=None):
    """
    Write a `tleap` input file.
    """

    with open(directory + '/' + filename, 'w') as f:
        for line in tleaplines:
            f.write(line)
        if pbctype == 0:
            f.write("solvatebox {} {} {:0.5f} iso\n".format(
                unit, waterbox, bufferval))
        elif pbctype == 1:
            f.write("solvatebox {} {} {{10.0 10.0 {:0.5f}}}\n".format(
                unit, waterbox, bufferval))
        elif pbctype == 2:
            f.write("solvateoct {} {} {:0.5f} iso\n".format(
                unit, waterbox, bufferval))
        elif pbctype is None:
            f.write("# Skipping solvation ...\n")
        else:
            raise Exception("Incorrect pbctype value provided: " + pbctype +
                            ". Only 0, 1, 2, and None are valid")
        if neutralize:
            f.write("addionsrand {} {} 0\n".format(unit, counter_cation))
            f.write("addionsrand {} {} 0\n".format(unit, counter_anion))
        if addion_residues:
            for i, res in enumerate(addion_residues):
                f.write("addionsrand {} {} {}\n".format(
                    unit, res, addion_values[i]))
        if removewat:
            for watnum in removewat:
                f.write("remove {} {}.{}\n".format(unit, unit, watnum))
        if saveprefix:
            f.write("savepdb {} {}.pdb\n".format(unit, saveprefix))
            f.write("saveamberparm {} {}.prmtop {}.rst7\n".format(
                unit, saveprefix, saveprefix))
        f.write("desc {}\n".format(unit))
        f.write("quit\n")


def run_tleap(filename, directory):
    """
    Execute tLEaP.
    """

    check_for_leap_log(path=directory)
    p = sp.Popen(
        'tleap -s -f ' + filename,
        stdout=sp.PIPE,
        bufsize=1,
        universal_newlines=True,
        cwd=directory,
        shell=True)
    output = []
    while p.poll() is None:
        line = p.communicate()[0]
        output.append(line)
    if p.poll() is None:
        p.kill()

    return output


def basic_tleap(tleapfile, directory='.', pdbfile=None, saveprefix=None):
    """
    Run tleap with a user supplied tleap script, optionally substitute PDB.
    """

    log.debug('Reading {}, writing {}/tleap.in, and executing ...'.format(
        tleapfile, directory))

    tleaplines = read_tleaplines(
        tleapfile, pdbfile=pdbfile, skip_solvate=False)

    write_tleapin(
        filename='tleap.in',
        directory=directory,
        tleaplines=tleaplines,
        pbctype=None,
        neutralize=False,
        saveprefix=saveprefix)

    run_tleap('tleap.in', directory=directory)


def countresidues(filename='tleap.in',
                  directory='.',
                  choice='water_residues',
                  volume=False):
    """
    Run and parse `tleap` output and return the number of residues added.
    The first choice gives a list of water residues. The second choice
    gives a dictionary of residue names and their number.
    """

    output = run_tleap(filename, directory)

    if choice == 'water_residues':
        # Return a list of residue numbers for the waters
        water_residues = []
        for line in output[0].splitlines():
            # Is this line a water?
            r = re.search("^R<WAT (.*)>", line)
            if r:
                water_residues.append(r.group(1))
        return water_residues

    elif choice == 'residue_dictionary':
        # Reurn a dictionary of {'RES' : number of RES}
        residues = {}
        for line in output[0].splitlines():
            # Is this line a residue from `desc` command?
            r = re.search("^R<(.*) ", line)
            if r:
                residue_name = r.group(1)
                # If this residue is not in the dictionary, initialize and
                # set the count to 1.
                if residue_name not in residues:
                    residues[residue_name] = 1
                # If this residue is in the dictionary, increment the count
                # each time we find an instance.
                elif residue_name in residues:
                    residues[residue_name] += 1
            if volume:
                r = re.search("Volume(.*)", line)
                if r:
                    volume = float(r.group(1)[1:-4])
                    return volume
        return residues
    else:
        raise Exception('Nothing to count.')


def solvate(tleapfile,
            pdbfile=None,
            pbctype=1,
            bufferwater='12.0A',
            waterbox='TIP3PBOX',
            neutralize=True,
            counter_cation='Na+',
            counter_anion='Cl-',
            addions=None,
            saveprefix='solvated'):
    """
    This routine solvates a solute system with a specified amount of water/ions.

    ARGUMENTS

    tleapfile : a fully functioning tleap file which is capable of preparing
    the system in gas phase. It should load all parameter files that will be
    necessary for solvation, including the water model and any custom
    residues. Assumes the final conformations of the solute are loaded via
    PDB.

    pdbfile : if present, the function will search for any loadpdb commands in
    the tleapfile and replace whatever is there with pdbfile.  This would be
    used for cases where we have modified PDBs. returnlist can be ALL for all
    residuse or WAT for waters.

    pbctype : the type of periodic boundary conditions. 0 = cubic, 1 =
    rectangular, 2 = truncated octahedron, None = no solvation.  If
    rectangular, only the z-axis buffer can be manipulated; the x- and y-axis
    will use a 10 Ang buffer.

    waterbox : the water box name to use with the solvatebox/solvateoct
    command.

    neutralize : False = do not neutralize the system, True = neutralize the
    system. the counterions to be used are specified below with
    'counter_cation' and 'counter_anion'.

    counter_cation : a mask to specify neutralizing cations

    counter_anion : a mask to specify neturalizing anions

    addions : a list of residue masks and values which indicate how much
    additional ions to add. The format for the values is as following: if the
    value is an integer, then add that exact integer amount of ions; if the
    value is followed by an 'M', then add that amount in molarity;  if 'm',
    add by molality.  example: ['Mg+',5, 'Cl-',10, 'K+','0.050M']

    """

    unit = 'model'
    addion_residues = []
    addion_values = []
    bufferval = [0.0]
    buffer_iterexp = 1
    wat_added = [0.0]

    dir = os.path.dirname(tleapfile)
    if dir == '':
        dir = '.'

    # Read tleapfile
    tleaplines = read_tleaplines(tleapfile, pdbfile=pdbfile, skip_solvate=True)

    # If bufferwater ends with 'A', meaning it is a buffer distance...
    if str(bufferwater).endswith('A'):
        # Let's get a rough value of the number of waters if the buffer value
        # is given as a string.
        bufferval.append(float(bufferwater[:-1]))
        write_tleapin(
            filename='tleap_apr_solvate.in',
            directory=dir,
            tleaplines=tleaplines,
            unit=unit,
            pbctype=pbctype,
            bufferval=bufferval[-1],
            waterbox=waterbox,
            neutralize=False,
            counter_cation=None,
            counter_anion=None,
            addion_residues=None,
            addion_values=None,
            removewat=None,
            saveprefix=None)
        # Get the number of water residues added...
        bufferwater = countresidues(
            filename='tleap_apr_solvate.in',
            directory=dir,
            choice='residue_dictionary')['WAT']
    if addions:
        if len(addions) % 2 == 1:
            raise Exception(
                "Error: The 'addions' list requires an even number of elements. "
                "Make sure there is a residue mask followed by a value for "
                "each ion to be added")
        for i, txt in enumerate(addions):
            if i % 2 == 0:
                addion_residues.append(txt)
            else:
                # User specifies molaliy...
                if str(txt).endswith('m'):
                    # number to add = (molality) x (number waters) x (0.018 kg/mol per water)
                    addion_values.append(
                        int(
                            np.ceil(
                                float(txt[:-1]) * float(bufferwater) * 0.018)))
                # User specifies molarity...
                elif str(txt).endswith('M'):
                    volume = countresidues(
                        filename='tleap_apr_solvate.in',
                        directory=dir,
                        choice='residue_dictionary',
                        volume=True)
                    N_A = 6.0221409 * 10**23
                    angstrom_cubed_to_liters = 1 * 10**-27
                    number_of_atoms = float(txt[:-1]) * N_A
                    liters = volume * angstrom_cubed_to_liters
                    atoms_to_add = number_of_atoms * liters
                    addion_values.append(np.ceil(atoms_to_add))
                else:
                    addion_values.append(int(txt))

    # First adjust wat_added by changing the bufferval
    cycle = 0
    buffer_iter = 0
    while cycle < 50:
        write_tleapin(
            filename='tleap_apr_solvate.in',
            directory=dir,
            tleaplines=tleaplines,
            unit=unit,
            pbctype=pbctype,
            bufferval=bufferval[-1],
            waterbox=waterbox,
            neutralize=neutralize,
            counter_cation=counter_cation,
            counter_anion=counter_anion,
            addion_residues=addion_residues,
            addion_values=addion_values,
            removewat=None,
            saveprefix=None)
        # Get the number of water residues added...
        wat_added.append(
            countresidues(
                filename='tleap_apr_solvate.in',
                directory=dir,
                choice='residue_dictionary')['WAT'])
        print(cycle, buffer_iter, ":", bufferwater, ':', bufferval[-1],
              buffer_iterexp, wat_added[-2], wat_added[-1])
        cycle += 1
        buffer_iter += 1
        if 0 <= (wat_added[-1] - bufferwater) < 12 or \
                (buffer_iterexp < -3 and (wat_added[-1] - bufferwater) > 0):
            # Possible failure mode: if the tolerance here is very small (0 < () < 1),
            # the loop can exit with bufferval that adds fewer waters than
            # bufferwater
            log.info('Done!')
            break
        # Possible location of a switch to adjust the bufferval by polynomial
        # fit approach.
        elif wat_added[-2] > bufferwater and wat_added[-1] > bufferwater:
            bufferval.append(bufferval[-1] + -1 * (10**buffer_iterexp))
        elif wat_added[-2] > bufferwater and wat_added[-1] < bufferwater:
            if buffer_iter > 1:
                buffer_iterexp -= 1
                buffer_iter = 0
                bufferval.append(bufferval[-1] + 5 * (10**buffer_iterexp))
            else:
                bufferval.append(bufferval[-1] + 1 * (10**buffer_iterexp))
        elif wat_added[-2] < bufferwater and wat_added[-1] > bufferwater:
            if buffer_iter > 1:
                buffer_iterexp -= 1
                buffer_iter = 0
                bufferval.append(bufferval[-1] + -5 * (10**buffer_iterexp))
            else:
                bufferval.append(bufferval[-1] + -1 * (10**buffer_iterexp))
        elif wat_added[-2] < bufferwater and wat_added[-1] < bufferwater:
            bufferval.append(bufferval[-1] + 1 * (10**buffer_iterexp))
        else:
            raise Exception(
                "The bufferval search died due to an unanticipated set of variable values"
            )

    if cycle >= 50:
        raise Exception(
            "Automatic adjustment of the buffer value was unable to converge on \
            a solution with sufficient tolerance")
    elif wat_added[-1] - bufferwater < 0:
        raise Exception(
            "Automatic adjustment of the buffer value resulted in fewer waters \
            added than targeted by bufferwater. Try increasing the tolerance in the above loop"
        )
    else:
        watover = 0
        cycle = 0
        while wat_added[-1] != bufferwater or cycle == 0:
            # Note I don't think there should be water removal errors, but if
            # so, this loop and '+=' method is an attempt to fix.
            watover += wat_added[-1] - bufferwater
            watlist = countresidues(
                filename='tleap_apr_solvate.in',
                choice='water_residues',
                directory=dir)
            if watover == 0:
                removewat = None
            else:
                removewat = watlist[-1 * watover:]

            write_tleapin(
                filename='tleap_apr_solvate.in',
                directory=dir,
                tleaplines=tleaplines,
                unit=unit,
                pbctype=pbctype,
                bufferval=bufferval[-1],
                waterbox=waterbox,
                neutralize=neutralize,
                counter_cation=counter_cation,
                counter_anion=counter_anion,
                addion_residues=addion_residues,
                addion_values=addion_values,
                removewat=removewat,
                saveprefix=saveprefix)
            # Get the full residue dictionary...
            reslist = countresidues(
                filename='tleap_apr_solvate.in',
                choice='residue_dictionary',
                directory=dir)
            wat_added.append(reslist['WAT'])
            for key, value in sorted(reslist.items()):
                log.info('{}\t{}'.format(key, value))
            cycle += 1
            if cycle >= 10:
                raise Exception(
                    "Solvation failed due to an unanticipated problem with water removal"
                )
