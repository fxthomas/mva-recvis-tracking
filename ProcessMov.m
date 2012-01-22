load ('VOC2009/person_final.mat', 'model');
fs = dir ('MOV/*.jpg');
RES = cell (size(fs,1),1);
for i=1:size(fs,1)
    ic = regexp (fs(i).name, 'image_(\d+)_0\.jpg', 'tokens');
    idx = idx{1};
    disp idx
    
    RES{idx} = process (imread (strcat('MOV/',fs(i).name)), model);
end