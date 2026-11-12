% Verify noise addition effect
clc;clear;
filein = ""; % path
files = dir(fullfile(filein,'*.dat'));

[~, idx] = sort([files.datenum]); 
sortedFiles = files(idx); 
figure
nfft = 4096;
for ii = 1:length(files)
    fileName{ii} = sortedFiles(ii).name;
    file_input = fullfile(filein,fileName{ii});
    subplot(3,4,ii)
    fp = fopen(file_input,'rb');
    data = fread(fp,10e6,"float");
    fclose(fp);
    dataIQ = data(1:2:end) +  1j*data(2:2:end);
    stft(dataIQ,100e6);
    title(fileName{ii});
end