function y = dronesOFDMFreqCompensation(x, fs, f)
    t = (1 : length(x))' / fs;
    y = x .* exp(-f*2*pi*1j*t);
end

