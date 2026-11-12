% Global main(), estimate first and then add noise
clc;
clear;
close all;

%% Parameter Init
NFFT = 409600;
data_len = 1.5e6;       % Read points
ddc_decifactor = 4;     % Downconversion downsampling index
fs = 100e6;
snrRange = [-2,-20];    % Target signal-to-noise ratio range

%% args: Symbol bandwidth, file name, file path
bw = 20e6;      % Symbol bandwidth

file_in = "";
file_out = "";
files_dat = dir(fullfile(file_in, '*.dat'));
files_iq = dir(fullfile(file_in, '*.iq'));
files = [files_dat; files_iq];

for ii = length(files):-1:1
    fileName{ii} = files(ii).name;

    fp = fopen(fullfile(file_in,fileName{ii}), "rb");
    data = fread(fp, data_len*2,"float");
    dataIQ = data(1:2:end) + data(2:2:end) * 1j;
    fclose(fp);

    % add noisy
    [idx1,idx2,idx3,idx4,f1, f2] = positionFind(dataIQ, fs, bw, NFFT);
    snr_esti = snrEsti(dataIQ,fs,NFFT,f1,f2,idx1,idx2,idx3,idx4);
    noise = snr_esti-15;
    rawSnr = snr_esti;
    for SNR = snrRange(1):-2:snrRange(2)
        while(abs(snr_esti - SNR) > 0.1)
            add = abs(snr_esti - SNR) / 2;
            if(snr_esti - SNR>0)
                noise = noise - add;
            else
                noise = noise + add;
            end
            datanoise = awgn1(dataIQ,noise,rawSnr);

            
            snr_esti = snrEsti(datanoise,fs,NFFT,f1,f2,idx1,idx2,idx3,idx4);
            disp("SNR"+snr_esti);
        end
        % save file
        DoAddNoise(file_out,file_in,fileName{ii},rawSnr,noise,SNR);
    end
end