
function save_untouch_nii_gz(nii, filename)

[p,f,e] = fileparts(filename);
if(strcmpi(e,'.gz'))
    tmpDir=tempname;
    disp(['Using tmpDir: ' tmpDir]);
    mkdir(tmpDir);
    tmpFileName = fullfile(tmpDir, f);
    save_untouch_nii(nii, tmpFileName);
    gzip(tmpFileName,p);
    
    delete(tmpFileName);
    rmdir(tmpDir);
else
    save_untouch_nii(nii, filename);
end    