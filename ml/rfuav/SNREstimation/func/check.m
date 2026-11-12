function [] = check(filein,nfft,fs,time,datatype)
    arguments
        filein = ''
        nfft double = 512
        fs double = 100e6
        time double = 0.01
        datatype = 'float32'
    end
    datalength = time*fs*2;
    fp = fopen(filein,'rb');
    data = fread(fp,datalength,datatype);
    fclose(fp);
    dataIQ = data(1:2:end) +  1j*data(2:2:end);
    stft(dataIQ,fs,"FFTLength",nfft);
end

