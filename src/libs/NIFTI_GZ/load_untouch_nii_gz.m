function nifti_struct = load_untouch_nii_gz(filename)

[p,f,e] = fileparts(filename);
if(strcmpi(e,'.gz'))
    tmpDir=tempname;
    disp(['Using tmpDir: ' tmpDir]);
    mkdir(tmpDir);
    gunzip(filename, tmpDir);
    tmpFileName = fullfile(tmpDir, f);
    nifti_struct=load_untouch_nii(tmpFileName);
    
    delete(tmpFileName);
    rmdir(tmpDir);
else
    nifti_struct=load_untouch_nii(filename);
end