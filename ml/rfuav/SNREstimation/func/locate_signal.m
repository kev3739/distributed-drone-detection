% Finding signal and noise locations
function [idx1,idx2,idx3,idx4,f1, f2] = positionFind(dataIQ, fs, bw, NFFT)
    %% Signal location detection
    [f1, f2] = dronesOFDMFreqShiftEsti(dataIQ, fs, bw, NFFT);
    f = (f1 + f2) / 2;
    sig = dronesOFDMFreqCompensation(dataIQ, fs, f);
    f11 = f1 - f;   f22 = f2 - f;
    
    
    
    %% Downsampling
    refs = fs/2;
    reNfft = NFFT / 2;
    sigResample = resample(sig, refs, fs);
    
    [pxx3, fvec3] = pwelch(sigResample, ...
        hamming(round(length(sigResample)/ 10)), [], reNfft, refs, "centered");
    
    
    %% SNR Esti
    temp11 = abs(fvec3 - f11);
    temp22 = abs(fvec3 - f22);
    [~, idx1] = min(temp11);
    [~, idx2] = min(temp22);
    
    
    bwNoise = 1e6;       % Noise bandwidth
    f3  = 0.75e6;       
    
    bwNoiseNfft = round(reNfft * (bwNoise / refs));
    idx4 = idx1 - round(reNfft * (f3 / refs));
    idx3 = idx4 - bwNoiseNfft;
end

