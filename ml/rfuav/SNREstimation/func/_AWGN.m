%  Load data
function [noisy_data] = awgn1(dataIQ,targetSNR_dB);
    targetSNR = 10^(targetSNR_dB / 10); 
    signalPower = 27;
    % Calculate the required noise power
    noisePower = signalPower / targetSNR; 
    
    % generate noise
    noise = sqrt(noisePower/2) .* (randn(size(dataIQ)) + 1j * randn(size(dataIQ))); 
    noisy_data = dataIQ + noise;

