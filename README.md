# pyedfreader

main-load-edf.py is used to read all EDF+ files in a folder and then save all of them into .mat files. You should modify the PSG folder path and ANN folder path in the script.

    psg_dir = '/Users/XXX/PSG-Folder/'
    ann_dir = '/Users/XXX/Annotations-Folder/'

In the PSG and ANN folders, the corresponding PSG file and ANN file must be in order. For example:
    
    in the PSG-Folder:
    	01-03-0001 PSG.edf
    	01-03-0002 PSG.edf
    	01-03-0003 PSG.edf
    	01-03-0004 PSG.edf
    	01-03-0005 PSG.edf
    	
    in the Annotations-Folder:
    	01-03-0001 Annotations.edf
    	01-03-0002 Annotations.edf
    	01-03-0003 Annotations.edf
    	01-03-0004 Annotations.edf
    	01-03-0005 Annotations.edf