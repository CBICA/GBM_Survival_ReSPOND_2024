function [Features, Features_Name] = FeatEx(TumorRA,Seg,Vent_SRI,Mod,Atlas)


Jakob_Vent = Atlas(:,:,:,1);
Jakob_Dist_Vent = Atlas(:,:,:,2);
RLJacob = Atlas(:,:,:,3);
atlas_Norm_Sur_SSD = Atlas(:,:,:,4);

Jacob_Dist_Tumor = bwdist(TumorRA);
Size_Over_Jacob = nnz(TumorRA ==1&Jakob_Vent==1);

Vent_Tumor_Dist_Jacob=(Jakob_Dist_Vent+Jacob_Dist_Tumor);
Vent_Tumor_Dist_Jacob=sort(Vent_Tumor_Dist_Jacob(:));
Vent_Tumor_Dist_Jacob=mean(Vent_Tumor_Dist_Jacob(1:100));

SSD = atlas_Norm_Sur_SSD(TumorRA ==1&atlas_Norm_Sur_SSD>0);
mean_SSD = mean(SSD(:));
max_SSD = max(SSD(:));
min_SSD = min(SSD(:));
median_SSD = median(SSD(:));
mode_SSD = mode(SSD(:));

Volin_Jacob=nnz(TumorRA ==1);
RR=nnz(TumorRA ==1&RLJacob==1);
LL=nnz(TumorRA ==1&RLJacob==2);
OO=nnz(TumorRA ==1&RLJacob==0);

Locations(1,:) = [LL ];
Headings_Locations = {' Left'};


if isempty(SSD)
    Locations_SSD(1,:)=NaN(1,5);
else
    Locations_SSD(1,:)=[mean_SSD min_SSD median_SSD ];
end

Headings_SSD ={'SSD_mean','SSD_min','SSD_median'};


Size_NC= nnz(Seg==1);
Size_ET= nnz(Seg==4);
Size_ED= nnz(Seg==2);

Tumor_Atl=Seg==1|Seg==4;
Over=Vent_SRI==1&Tumor_Atl==1;
Size_Over=size(find(Over==1),1);

Dist_Vent = bwdist(Vent_SRI);
Dist_Tumor = bwdist(Tumor_Atl);

Vent_Tumor_Dist=(Dist_Vent+Dist_Tumor);
Vent_Tumor_Dist=sort(Vent_Tumor_Dist(:));
Vent_Tumor_Dist=mean(Vent_Tumor_Dist(1:100));

TumorAtlClean = bwareaopen(Tumor_Atl, 40);  

[Number, ~, Volume, Dist, EquivDiameter, Extent, AxisLength, AxisRatio, Solidity, thickness, SurfaceArea] = MultGeo(TumorAtlClean);


Geometry(1,:)=[Number Extent AxisLength AxisRatio];
Headings_Geometry={'Number','Extent','AxisLength','AxisRatio'};

brain_size=logical(Mod);
brain_size=size(find(brain_size==1),1);

Volumetrics(1,:)=[Size_NC Size_ET ];
Headings_Volumetrics={'Size_NC','Size_ET'};

BS = brain_size;
Dist = Vent_Tumor_Dist;
NC  = Size_NC;
ET  = Size_ET;
ED  = Size_ED;
Over = Size_Over;

Over(Over>3000)=3000;


Mix_Volumetrics(1,1)=Dist-(Over/300);
Mix_Volumetrics(1,2)=ED*100./(NC+ET);
Mix_Volumetrics(1,3)=ED*100./(NC+ET+ED);
Mix_Volumetrics(1,4)=ET*100./BS;
Mix_Volumetrics(1,5)=NC*100./BS;
Mix_Volumetrics(1,6)=ED*100./BS;
Mix_Volumetrics(1,7)=(NC+ET)*100./BS;
Mix_Volumetrics(1,8)=(NC+ET+ED)*100./BS;
Mix_Volumetrics(1,9)=(NC+ET)./(NC+ET+ED);

Headings_Mix_Volumetrics={'Dist2Vent','ED*100./(NC+ET)','ED*100./(NC+ET+ED)','ET*100./BS','NC*100./BS','ED*100./BS','(NC+ET)*100./BS','(NC+ET+ED)*100./BS','(NC+ET)./(NC+ET+ED)'};


Features_Name=[Headings_Volumetrics Headings_Mix_Volumetrics Headings_Geometry Headings_Locations Headings_SSD];
Features=[Volumetrics Mix_Volumetrics Geometry Locations Locations_SSD];
 
disp ('##Features extraction completed##')

end

