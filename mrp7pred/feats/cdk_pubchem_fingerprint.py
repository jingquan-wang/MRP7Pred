"""
Generate 881-bit pubchem molecular fingerprint via cdk
"""

from numpy import ndarray
import numpy as np

# from PyFingerprint.All_Fingerprint import get_fingerprint

import warnings

warnings.filterwarnings("ignore")


def _pubchem_fingerprint(smi: str) -> ndarray:
    """
    Get the 881-bit PubChem molecular finger print from smiles
    """
    # pubchem_fp = np.zeros(881)
    # idx_ones = get_fingerprint(smi, fp_type="pubchem")
    # pubchem_fp[idx_ones] = 1
    # return pubchem_fp
    pass
