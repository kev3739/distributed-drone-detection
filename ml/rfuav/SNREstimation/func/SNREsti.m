% Signal-to-noise ratio estimation function
function snrEsti = snrEsti(dataIQ, fs, nfft,f1, f2,idx1,idx2,idx3,idx4)

f = (f1 + f2) / 2;
sig = dronesOFDMFreqCompensation(dataIQ, fs, f);


%% Downsampling
refs = fs/2;
reNfft = nfft / 2;
sigResample = resample(sig, refs, fs);

fftTemp = abs(fftshift(fft(sigResample, reNfft) / reNfft));
sigPower = mean(fftTemp(idx1:idx2) .^ 2);
nosPower = mean(fftTemp(idx3:idx4) .^ 2);

snrEsti = 10 * log10((sigPower-nosPower)/nosPower);
snrEsti = real(snrEsti);
%% Figure
[pxx3, fvec3] = pwelch(sigResample, ...
    hamming(round(length(sigResample)/ 10)), [], reNfft, refs, "centered");
f11 = f1 - f;   f22 = f2 - f;
[pxx, fvec] = pwelch(dataIQ, hamming(round(length(dataIQ)/ 10)), [], nfft, fs, "centered");
pxx = db(pxx);
subplot(311)
plot(fvec, pxx);    xline(f1, 'r');  xline(f2, 'r');
title("Raw Signal Data")

subplot(312)
[pxx2, fvec2] = pwelch(sig, hamming(round(length(sig)/ 10)), [], nfft, fs, "centered");
pxx2 = db(pxx2);
plot(fvec2, pxx2);    xline(f11, 'r');  xline(f22, 'r');
title("Signal: Carrier correction")

subplot(313)
pxx3 = db(pxx3);
plot(fvec3, pxx3);    
xline(fvec3(idx1), 'r');  xline(fvec3(idx2), 'r');
xline(fvec3(idx3), 'k');  xline(fvec3(idx4), 'k');
title("Signal: Downsampling")
end

