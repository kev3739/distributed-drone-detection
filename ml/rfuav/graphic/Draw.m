% Draw one color resolution
%% Single frequency resolution and color-mapped plotting
clc;clear;close all;

% args
fs = 100e6;                    
fftpoint = [1024];
time_sec = 0.1;                   
dataform = 'float32';           
byte_per = 4;                   
datalength = time_sec*fs*byte_per*2;       
file_in ={"",
          "",
          "",
          ""};% {path1,path2,...,pathn}
filepathOut = ""; % output path

files = [];
for i = 1:length(file_in)

    files_dat = dir(fullfile(file_in{i}, '*.dat'));
    files_iq = dir(fullfile(file_in{i}, '*.iq'));
    files_bin = dir(fullfile(file_in{i}, '*.bin'));

    files = [files,files_dat; files_iq,files_bin];
    file_num(i) = length(files);
end
fileFlag = 1;

for ii = 1:length(files)
    fileName{ii} = files(ii).name;
    while(ii > file_num(fileFlag))
        fileFlag = fileFlag + 1;
    end
    file_input = fullvfile(file_in{fileFlag},fileName{ii})

    myname = char(fileName{ii});
    for i = 1:length(myname)
        if (strcmp(myname(i), '-') || strcmp(myname(i), '_'))
            flytype = string(myname(1:i-1));
            break; 
        end
    end
    filepathOut = filepathOut + '\' + flytype + '\' + fileName{ii}(1:end-3);
    color = ["parula"];

    if ~exist(filepathOut,"dir")
        mkdir(filepathOut);
    else
        disp("File exist!");
    end

    fp = fopen(file_input, 'rb');
    fseek(fp, 0, 1);
    fileSize = ftell(fp);
    fclose(fp);
    readtime = ceil(fileSize/datalength);


    %% Read and save files in batches
    time = 0;
    for i =1:readtime
        tic
        fp = fopen(file_input, 'rb'); 
        fseek(fp,(i-1)*datalength,-1);
        data = fread(fp,datalength/4,dataform);
        fclose(fp);
        dataIQ = data(1:2:end-1) + 1i * data(2:2:end);
        clear data;
        for j = 1:length(fftpoint)
            for k = 1:length(color)
                stft(dataIQ,fs,FFTLength=fftpoint(j));
                colormap(color(k));
                yticks([-50 :10:50]);
                yticklabels([5710:10:5810]);
                xticks([0:10:100]);
                xticklabels([0:0.1/10:0.1]);
                xlabel("Time(s)");
                title(fileName{ii}(1:end-4));
                title(flytype);

                newFile = fullfile(filepathOut,num2str(i*0.1-0.1+time) + "-" + num2str(i*0.1+time) + "s-" +...
                    color(k) + "-" + num2str(fftpoint(j)) + ".jpg"); 
                set(gcf, 'Units', 'inches', 'Position', [0, 0, 8, 6]);
                print(gcf, newFile, '-dpng', '-r300');
                clf;
            end
        end
        toc
    end
end