function  [Number, Centroid, Volume, Dist, EquivDiameter, Extent, AxisLength, AxisRatio, Solidity, thickness, SurfaceArea] = MultGeo(BW)

if nnz(BW)==0
    Number=NaN; Centroid=NaN;  Volume=NaN;  Dist=NaN;  EquivDiameter=NaN;  Extent=NaN;  AxisLength=NaN;  AxisRatio=NaN;  Solidity=NaN;  thickness=NaN;  SurfaceArea = NaN;
else
    
    stats = regionprops3(BW,'all');
    Volumes= stats.Volume;
    Number=length(stats.Volume);
    Weights=Volumes/sum(Volumes);
    
    Centroids= stats.Centroid;
    Centroid= sum(Centroids.*Weights,1);
    
    [~,idx]=sort(Volumes,'descend');
    
    Dist=0;
    
    for jj=1:Number
        X=[Centroids(idx(1),:);Centroids(jj,:)];
        Dist = Dist + pdist(X,'euclidean')*Weights(jj);
    end
         
    Volume=sum(Volumes);
    
    EquivDiameters= stats.EquivDiameter;
    EquivDiameter= sum(EquivDiameters.*Weights);
    
    Extents= stats.Extent;
    Extent=sum(Extents.*Weights);
    
    PrincipalAxisLengths= stats.PrincipalAxisLength;
    PrincipalAxisLengthw= PrincipalAxisLengths.*repmat(Weights,1,3);
    PrincipalAxisLength= sum(PrincipalAxisLengthw,1);
    AxisRatio=PrincipalAxisLength(1)/PrincipalAxisLength(2)+PrincipalAxisLength(1)/PrincipalAxisLength(3);
    
    AxisLength=sum(PrincipalAxisLength);
    
    Soliditys= stats.Solidity;
    Solidity= sum(Soliditys.*Weights);
    
    SurfaceAreas= stats.SurfaceArea;
    SurfaceArea= sum(SurfaceAreas);
    
    thickness=Volume/SurfaceArea;
    
end
end