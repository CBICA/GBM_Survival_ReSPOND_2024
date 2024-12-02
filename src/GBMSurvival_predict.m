function GBMSurvival(Age,fTumorRA,fSeg_SRI,fVent_SRI,fMod,fAtlas,outdir,modelmat)


Age=str2double(Age);
fprintf("Age:%f\n",Age);
fprintf("fTumorRA:%s\n",fTumorRA)
fprintf("fSeg_SRI:%s\n",fSeg_SRI)
fprintf("fVent_SRI:%s\n",fVent_SRI)
fprintf("fMod:%s\n",fMod)
fprintf("fAtlas:%s\n",fAtlas)
fprintf("outdir:%s\n",outdir)
fprintf("model:%s\n",modelmat)



fprintf('Reading input..\n');
fprintf('TC in atlas\n');
TumorRA = load_untouch_nii_gz([fTumorRA]);
TumorRA = logical(TumorRA.img);

fprintf('seg in SRI\n');
Seg_SRI = load_untouch_nii_gz([fSeg_SRI]);
Seg_SRI=single(Seg_SRI.img);

fprintf('VT in SRI\n');
Vent_SRI= load_untouch_nii_gz([fVent_SRI]);
Vent_SRI=logical(Vent_SRI.img);

fprintf('t1ce in SRI\n');
Mod = load_untouch_nii_gz([fMod]);
Mod=single(Mod.img);

fprintf('staging atlas\n');
Atlas = load_untouch_nii_gz([fAtlas]);
Atlas = double(Atlas.img);

fprintf('\n');
fprintf('Extracting features..\n');

[Features_sub, Features_Name] = FeatEx(TumorRA,Seg_SRI,Vent_SRI,Mod,Atlas);
fout=sprintf("%s/features.csv",outdir);
table1=table([Features_Name;num2cell(Features_sub)]);
writetable(table1,fout,'WriteVariableNames',0);

disp('############### Apply model ###########')


fprintf('Loading pre-trained model..\n');
load(modelmat);

fprintf('combine with age..\n');

display(size(Features_sub));
display(Features_sub)

Test_Features=double([Age Features_sub(1,:)]);

display(size(Test_Features));
display(Test_Features);

fprintf('scale..\n')
Input_test=(Test_Features-repmat(mu,size(Test_Features,1),1))./(repmat(sigma_fe,size(Test_Features,1),1));

fprintf('Predict..\n');
[~, ~, prob_estimates] = svmpredict(ones(size(Input_test,1),1), Input_test, model, '-b 1');

SPI=prob_estimates(:,idk);
Stage=2*ones(size(SPI));
Stage(SPI<0.3)=3;
Stage(SPI>0.7)=1;

fprintf('output results..\n')
fout=sprintf("%s/results.csv",outdir);
table2=table([{'stage','SPI','prob_short','prob_long'};[num2cell(Stage) num2cell(SPI) num2cell(prob_estimates)]]);
writetable(table2,fout,'WriteVariableNames',0);


fprintf('Finished.\n');
