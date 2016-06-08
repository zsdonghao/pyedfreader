# pyedfreader

main-load-edf.py is used to read all EDF+ files in a folder and then save all of them into .mat files. You should modify the PSG folder path and ANN folder path in the script.

```python
psg_dir = '/Users/XXX/PSG-Folder/'
ann_dir = '/Users/XXX/Annotations-Folder/'
```


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
    	
In the .mat file:
	
	All variables name are following EDF+ standard.
	
	time: the start time (s) of an annotation
	epoch_duration: normally 30 or 20 seconds according to AASM standard
	annotations: 
			0~ Stage Wake 
		 	1~ Stage N1
		 	2~ Stage N2	
		 	3~ Stage N3 
		 	4~ Stage REM	 
		 	5~ Unknown
	
	signals:
			a cell to store all channels, their corresponding channel name are listed in "label"
	fs: sampling frequency of different channels
 
To use this script, please cite:

	XXX	