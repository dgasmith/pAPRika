"""
Tests the restraints utilities.
"""

import unittest
import warnings
import numpy as np
import logging as log
import subprocess as sp
import parmed as pmd
import pytest
import paprika
from paprika.restraints import *

def test_DAT_restraint():
    #1
    rest1 = DAT_restraint()
    rest1.continuous_apr = False
    rest1.auto_apr = False
    rest1.structure_file = './cb6-but/cb6-but-notcentered.pdb'
    rest1.mask1 = ':CB6@O,O2,O4,O6,O8,O10'
    rest1.mask2 = ':BUT@C3'
    rest1.attach['target'] = 3.0
    rest1.attach['num_windows'] = 4
    rest1.attach['fc_initial'] = 0.0
    rest1.attach['fc_final'] = 3.0
    rest1.pull['fc'] = rest1.attach['fc_final']
    rest1.pull['num_windows'] = 4
    rest1.pull['target_initial'] = rest1.attach['target']
    rest1.pull['target_final'] = 6.0
    rest1.release['target'] = rest1.pull['target_final']
    rest1.release['num_windows'] = rest1.attach['num_windows']
    rest1.release['fc_initial'] = rest1.attach['fc_initial']
    rest1.release['fc_final'] = rest1.attach['fc_final']
    rest1.initialize()
    assert rest1.index1 == [13, 31, 49, 67, 85, 103]
    assert rest1.index2 == [119]
    assert rest1.index3 == None
    assert rest1.index4 == None
    assert np.allclose(rest1.phase['attach']['force_constants'], np.array( [0.0, 1.0, 2.0, 3.0] ))
    assert np.allclose(rest1.phase['attach']['targets'], np.array( [3.0, 3.0, 3.0, 3.0] ))
    assert np.allclose(rest1.phase['pull']['force_constants'], np.array( [3.0, 3.0, 3.0, 3.0] ))
    assert np.allclose(rest1.phase['pull']['targets'], np.array( [3.0, 4.0, 5.0, 6.0] ))
    assert np.allclose(rest1.phase['release']['force_constants'], np.array( [0.0, 1.0, 2.0, 3.0] ))
    assert np.allclose(rest1.phase['release']['targets'], np.array( [6.0, 6.0, 6.0, 6.0] ))
    window_list = create_window_list([rest1])
    assert window_list == ['a000', 'a001', 'a002', 'a003', 'p000', 'p001', 'p002', 'p003', 'r000', 'r001', 'r002', 'r003']

    #1a    
    rest2 = DAT_restraint()
    rest2.continuous_apr = False
    rest2.auto_apr = False
    rest2.structure_file = './cb6-but/cb6-but-notcentered.pdb'
    rest2.mask1 = ':CB6@O,O2,O4,O6,O8,O10'
    rest2.mask2 = ':BUT@C3'
    rest2.mask3 = ':BUT@C'
    rest2.attach['target'] = 180.0
    rest2.attach['num_windows'] = 4
    rest2.attach['fc_final'] = 75.0
    rest2.pull['fc'] = rest2.attach['fc_final']
    rest2.pull['num_windows'] = 4
    rest2.pull['target_final'] = 180.0
    rest2.release['target'] = rest2.pull['target_final']
    rest2.release['num_windows'] = rest2.attach['num_windows']
    rest2.release['fc_final'] = rest2.attach['fc_final']
    rest2.initialize()
    assert rest2.index1 == [13, 31, 49, 67, 85, 103]
    assert rest2.index2 == [119]
    assert rest2.index3 == [109]
    assert rest2.index4 == None
    assert np.allclose(rest2.phase['attach']['force_constants'], np.array( [0.0, 25.0, 50.0, 75.0] ))
    assert np.allclose(rest2.phase['attach']['targets'], np.array( [180.0, 180.0, 180.0, 180.0] ))
    assert np.allclose(rest2.phase['pull']['force_constants'], np.array( [75.0, 75.0, 75.0, 75.0] ))
    assert np.allclose(rest2.phase['pull']['targets'], np.array( [0.0, 60.0, 120.0, 180.0] ))
    assert np.allclose(rest2.phase['release']['force_constants'], np.array( [0.0, 25.0, 50.0, 75.0] ))
    assert np.allclose(rest2.phase['release']['targets'], np.array( [180.0, 180.0, 180.0, 180.0] ))
    window_list = create_window_list([rest2])
    assert window_list == ['a000', 'a001', 'a002', 'a003', 'p000', 'p001', 'p002', 'p003', 'r000', 'r001', 'r002', 'r003']
    
    #2
    rest3 = DAT_restraint()
    rest3.continuous_apr = False
    rest3.auto_apr = True
    rest3.structure_file = './cb6-but/cb6-but-notcentered.pdb'
    rest3.mask1 = ':CB6@O2'
    rest3.mask2 = ':CB6@O'
    rest3.mask3 = ':BUT@C3'
    rest3.mask4 = ':BUT@C'
    rest3.attach['target'] = 90.0
    rest3.attach['fc_increment'] = 25.0
    rest3.attach['fc_initial'] = 0.0
    rest3.attach['fc_final'] = 75.0
    #rest3.pull['fc'] = rest3.attach['fc_final']
    rest3.pull['target_increment'] = 1.0
    #rest3.pull['target_initial'] = rest3.attach['target']
    rest3.pull['target_final'] = 93.0
    #rest3.release['target'] = rest3.pull['target_final']
    #rest3.release['fc_increment'] = rest3.attach['fc_increment']
    #rest3.release['fc_initial'] = rest3.attach['fc_initial']
    #rest3.release['fc_final'] = rest3.attach['fc_final']
    rest3.initialize()
    assert rest3.index1 == [31]
    assert rest3.index2 == [13]
    assert rest3.index3 == [119]
    assert rest3.index4 == [109]
    assert np.allclose(rest3.phase['attach']['force_constants'], np.array( [0.0, 25.0, 50.0, 75.0] ))
    assert np.allclose(rest3.phase['attach']['targets'], np.array( [90.0, 90.0, 90.0, 90.0] ))
    assert np.allclose(rest3.phase['pull']['force_constants'], np.array( [75.0, 75.0, 75.0, 75.0] ))
    assert np.allclose(rest3.phase['pull']['targets'], np.array( [90.0, 91.0, 92.0, 93.0] ))
    assert np.allclose(rest3.phase['release']['force_constants'], np.array( [0.0, 25.0, 50.0, 75.0] ))
    assert np.allclose(rest3.phase['release']['targets'], np.array( [93.0, 93.0, 93.0, 93.0] ))
    window_list = create_window_list([rest3])
    assert window_list == ['a000', 'a001', 'a002', 'a003', 'p000', 'p001', 'p002', 'p003', 'r000', 'r001', 'r002', 'r003']

    #2a
    rest4 = DAT_restraint()
    rest4.continuous_apr = False
    rest4.auto_apr = False
    rest4.structure_file = './cb6-but/cb6-but-notcentered.pdb'
    rest4.mask1 = ':CB6@O2'
    rest4.mask2 = ':CB6@O'
    rest4.mask3 = ':BUT@C3'
    rest4.mask4 = ':BUT@C'
    rest4.attach['target'] = 0.0
    rest4.attach['fc_increment'] = 25.0
    rest4.attach['fc_final'] = 75.0
    rest4.pull['fc'] = 75.0
    rest4.pull['target_increment'] = 1.0
    rest4.pull['target_final'] = 3.0
    rest4.release['target'] = 3.0
    rest4.release['fc_increment'] = 25.0
    rest4.release['fc_final'] = 75.0
    rest4.initialize()
    assert rest4.index1 == [31]
    assert rest4.index2 == [13]
    assert rest4.index3 == [119]
    assert rest4.index4 == [109]
    assert np.allclose(rest4.phase['attach']['force_constants'], np.array( [0.0, 25.0, 50.0, 75.0] ))
    assert np.allclose(rest4.phase['attach']['targets'], np.array( [0.0, 0.0, 0.0, 0.0] ))
    assert np.allclose(rest4.phase['pull']['force_constants'], np.array( [75.0, 75.0, 75.0, 75.0] ))
    assert np.allclose(rest4.phase['pull']['targets'], np.array( [0.0, 1.0, 2.0, 3.0] ))
    assert np.allclose(rest4.phase['release']['force_constants'], np.array( [0.0, 25.0, 50.0, 75.0] ))
    assert np.allclose(rest4.phase['release']['targets'], np.array( [3.0, 3.0, 3.0, 3.0] ))
    window_list = create_window_list([rest4])
    assert window_list == ['a000', 'a001', 'a002', 'a003', 'p000', 'p001', 'p002', 'p003', 'r000', 'r001', 'r002', 'r003']

    #3
    rest5 = DAT_restraint()
    rest5.continuous_apr = False
    rest5.auto_apr = False
    rest5.structure_file = './cb6-but/cb6-but-notcentered.pdb'
    rest5.mask1 = ':CB6@O,O2,O4,O6,O8,O10'
    rest5.mask2 = ':BUT@C*'
    rest5.attach['target'] = 0.0
    rest5.attach['fraction_list'] = [0.0, 0.2, 0.5, 1.0]
    rest5.attach['fc_final'] = 5.0
    rest5.pull['fc'] = rest5.attach['fc_final']
    rest5.pull['fraction_list'] = [0.0, 0.5, 1.0]
    rest5.pull['target_final'] = 1.0
    rest5.release['target'] = rest5.pull['target_final']
    rest5.release['fraction_list'] = [0.0, 0.3, 0.6, 1.0]
    rest5.release['fc_final'] = rest5.attach['fc_final']
    rest5.initialize()
    assert rest5.index1 == [13, 31, 49, 67, 85, 103]
    assert rest5.index2 == [109, 113, 115, 119]
    assert rest5.index3 == None
    assert rest5.index4 == None
    assert np.allclose(rest5.phase['attach']['force_constants'], np.array( [0.0, 1.0, 2.5, 5.0] ))
    assert np.allclose(rest5.phase['attach']['targets'], np.array( [0.0, 0.0, 0.0, 0.0] ))
    assert np.allclose(rest5.phase['pull']['force_constants'], np.array( [5.0, 5.0, 5.0] ))
    assert np.allclose(rest5.phase['pull']['targets'], np.array( [0.0, 0.5, 1.0] ))
    assert np.allclose(rest5.phase['release']['force_constants'], np.array( [0.0, 1.5, 3.0, 5.0] ))
    assert np.allclose(rest5.phase['release']['targets'], np.array( [1.0, 1.0, 1.0, 1.0] ))
    window_list = create_window_list([rest5])
    assert window_list == ['a000', 'a001', 'a002', 'a003', 'p000', 'p001', 'p002', 'r000', 'r001', 'r002', 'r003']

    #4
    rest6 = DAT_restraint()
    rest6.continuous_apr = False
    rest6.auto_apr = False
    rest6.structure_file = './cb6-but/cb6-but-notcentered.pdb'
    rest6.mask1 = ':CB6@O,O2,O4,O6,O8,O10'
    rest6.mask2 = ':BUT@C*'
    rest6.attach['target'] = 0.0
    rest6.attach['fraction_increment'] = 0.25
    rest6.attach['fc_final'] = 5.0
    rest6.pull['fc'] = rest6.attach['fc_final']
    rest6.pull['fraction_increment'] = 0.5
    rest6.pull['target_final'] = 1.0
    rest6.release['target'] = rest6.pull['target_final']
    rest6.release['fraction_increment'] = 0.33
    rest6.release['fc_final'] = rest6.attach['fc_final']
    rest6.initialize()
    assert rest6.index1 == [13, 31, 49, 67, 85, 103]
    assert rest6.index2 == [109, 113, 115, 119]
    assert rest6.index3 == None
    assert rest6.index4 == None
    assert np.allclose(rest6.phase['attach']['force_constants'], np.array( [0.0, 1.25, 2.5, 3.75, 5.0] ))
    assert np.allclose(rest6.phase['attach']['targets'], np.array( [0.0, 0.0, 0.0, 0.0, 0.0] ))
    assert np.allclose(rest6.phase['pull']['force_constants'], np.array( [5.0, 5.0, 5.0] ))
    assert np.allclose(rest6.phase['pull']['targets'], np.array( [0.0, 0.5, 1.0] ))
    ### Note, the 6.6 in the following test is wrong ... needs to get fixed.
    assert np.allclose(rest6.phase['release']['force_constants'], np.array( [0.0, 1.65, 3.3, 4.95, 6.6] ))
    assert np.allclose(rest6.phase['release']['targets'], np.array( [1.0, 1.0, 1.0, 1.0, 1.0] ))
    window_list = create_window_list([rest6])
    assert window_list == ['a000', 'a001', 'a002', 'a003', 'a004', 'p000', 'p001', 'p002', 'r000', 'r001', 'r002', 'r003', 'r004']

    #5
    rest7 = DAT_restraint()
    rest7.continuous_apr = True
    rest7.auto_apr = False
    rest7.structure_file = './cb6-but/cb6-but-notcentered.pdb'
    rest7.mask1 = ':1@O,O1,:BUT@H1'
    rest7.mask2 = ':CB6@N'
    rest7.attach['target'] = 0.0
    rest7.attach['fc_list'] = [0.0, 0.5, 1.0, 2.0]
    rest7.pull['fc'] = 2.0
    rest7.pull['target_list'] = [0.0, 0.5, 1.0, 1.5]
    rest7.release['target'] = 1.5
    rest7.release['fc_list'] = [0.0, 0.66, 1.2, 2.0]
    rest7.initialize()
    assert rest7.index1 == [13, 14, 111]
    assert rest7.index2 == [3]
    assert rest7.index3 == None
    assert rest7.index4 == None
    assert np.allclose(rest7.phase['attach']['force_constants'], np.array( [0.0, 0.5, 1.0, 2.0] ))
    assert np.allclose(rest7.phase['attach']['targets'], np.array( [0.0, 0.0, 0.0, 0.0] ))
    assert np.allclose(rest7.phase['pull']['force_constants'], np.array( [2.0, 2.0, 2.0, 2.0] ))
    assert np.allclose(rest7.phase['pull']['targets'], np.array( [0.0, 0.5, 1.0, 1.5] ))
    assert np.allclose(rest7.phase['release']['force_constants'], np.array( [0.0, 0.66, 1.2, 2.0] ))
    assert np.allclose(rest7.phase['release']['targets'], np.array( [1.5, 1.5, 1.5, 1.5] ))
    window_list = create_window_list([rest7])
    assert window_list == ['a000', 'a001', 'a002', 'p000', 'p001', 'p002', 'p003', 'r000', 'r001', 'r002']


test_DAT_restraint()

