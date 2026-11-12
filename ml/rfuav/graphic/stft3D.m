clc;
clear;
close all;

% args
fs = 100e6;                   % sample rate
fc = 2440e6;                  
fftlength = [2048,1024, 512, 128]; 
time_sec = 0.5;                   
dataform = 'float32';           
byte_per = 4;                   
datalength = time_sec*fs*byte_per*2;
file = ""; % path

ii = 2;
blocksize = 1e6;            
times = datalength / blocksize; 
overlap = 0.25;
outLengthPer = 1+floor((blocksize/2 - fftlength(ii)) / (fftlength(ii)*(1-overlap)));
sTotal = zeros(fftlength(ii),times*outLengthPer);
tTotal = zeros(1,times*outLengthPer);

for i = 1:times
    fp = fopen(file, "rb");
    fseek(fp,blocksize*(i-1),-1);
    data = fread(fp, blocksize, dataform);
    fclose(fp);
    dataIQ = data(1:2:end) + 1j * data(2:2:end);  
    clear data;
    [s, f, t] = spectrogram(dataIQ,fftlength(ii),fftlength(ii)*overlap,fftlength(ii),fs);
    sTotal = [sTotal, s];
    tTotal = [tTotal, t + (i-1)*blocksize/fs];
      
end
clear dataIQ;

figure;
surf(tTotal, f, abs(sTotal), 'EdgeColor', 'none');
axis xy;
colormap jet;
xlabel('Time (s)');
ylabel('Frequency (Hz)');
title('STFT of IQ Signal');
colorbar;

% Setting the Viewing Angle
view(-45, 60);
