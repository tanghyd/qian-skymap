from pathlib import Path

import click
import numpy as np
import spiir

# Here is the detector code for the old version of LAL(6.49.0), see:
# /fred/oz016/opt-pipe/include/lal/LALDetectors.h
# Be careful when chenge to new version - the code is different, see:
# https://lscsoft.docs.ligo.org/lalsuite/lal/_l_a_l_detectors_8h_source.html#l00168
LAL_IFO_MAP = {'L1': 5, 'H1': 4, 'V1':1, 'K1': 16, 'I1': 17}


@click.command
@click.argument("xml", type=str) # default="data/coinc_xml/H1L1V1_1187008882_3_806.xml"
@click.option("--out", type=str, default="data", help="Output data directory")
def main(xml: str, out: str = "data"):
    """Reads in a SPIIR coinc.xml file and writes data (SNR, sigma) to .txt files."""
    print(f'Processing coinc.xml file from {xml}...')
    xmlfile = spiir.io.ligolw.coinc.load_coinc_xml(xml)
    
    # specify folder to save output data
    out_path = Path(out)
    out_path.mkdir(exist_ok=True, parents=True)
    (out_path / "snr_data").mkdir(exist_ok=True)  # make output subfolder for SNR data

    try:
        ifos = list(xmlfile['snrs'].keys())
    except KeyError as err:
        raise KeyError(
            f"snr array data not present {xml} file. Please check your coinc.xml!"
        ) from err
    
    ndet = len(ifos)

    # Calculate sigma = sqrt((h|h)) = deff/SNR
    deff_array = np.array([xmlfile['tables']['postcoh'][f"deff_{ifo}"] for ifo in ifos])
    max_snr_array = np.array([xmlfile['tables']['postcoh'][f"snglsnr_{ifo}"] for ifo in ifos])
    sigma_array = deff_array*max_snr_array

    trigger_time = xmlfile["tables"]["postcoh"]["end_time"].item()
    trigger_time += xmlfile["tables"]["postcoh"]["end_time_ns"].item() * 1e-9

    # Save event info
    # trigger_time, ndet,    detcode1, ..., detcodeN,    max_snr1, ..., max_snrN,    sigma1, ..., sigmaN
    # 1+1+N+N+N = 3N+2 elements
    event_info = [trigger_time, ndet]
    for ifo in ifos:
        event_info.append(LAL_IFO_MAP[ifo])
    event_info.append(max_snr_array)
    event_info.append(sigma_array)
    np.savetxt(out_path / 'event_info', np.array(event_info))

    # Save SNR series for each detector
    for ifo in ifos:
        timestamps = xmlfile["snrs"][ifo].index.values
        real_snr = np.real(xmlfile['snrs'][ifo])
        imag_snr = np.imag(xmlfile['snrs'][ifo])
        snr_to_save = np.array([timestamps[ifo], real_snr, imag_snr]).T 
        np.savetxt(out_path / "snr_data" / f"snr_det{LAL_IFO_MAP[ifo]}", snr_to_save)

    print(f'Trigger time: {trigger_time}')
    print(f'Detectors: {ifos}')
    print(f'SNRs: {max_snr_array}')
    print(f'sigmas: {sigma_array}')
    print('SNR and event info have been saved. \n')

if __name__ == "__main__":
    main()